"""
Discovery service for internet-wide job search.

This service:
1. Generates smart search queries based on user profile
2. Discovers career pages using DuckDuckGo
3. Crawls pages and extracts structured job data using AI
"""
import asyncio
import json
import re
from typing import Optional
from urllib.parse import urlparse, urljoin

import httpx
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS

from app.core.config import settings
from app.core.logging import get_logger
from app.models.discovery import DiscoveredJob, DiscoverJobsRequest

logger = get_logger(__name__)

# Known career page patterns to prioritize
CAREER_PAGE_PATTERNS = [
    r'/careers',
    r'/jobs',
    r'/join',
    r'/work-with-us',
    r'/opportunities',
    r'boards\.greenhouse\.io',
    r'jobs\.lever\.co',
    r'careers\.smartrecruiters\.com',
    r'workday\.com.*careers',
]

# Domains to exclude (job aggregators - we want direct company pages)
EXCLUDED_DOMAINS = [
    'indeed.com',
    'linkedin.com',
    'glassdoor.com',
    'ziprecruiter.com',
    'monster.com',
    'naukri.com',
    'dice.com',
]


async def generate_search_queries(
    role: str,
    skills: list[str],
    location: str,
    experience_years: int,
    include_startups: bool,
    include_enterprise: bool,
    custom_terms: list[str],
    api_key: str
) -> list[str]:
    """
    Use LLM to generate effective search queries for finding career pages.
    
    Args:
        role: Target job role
        skills: Key skills
        location: Preferred location
        experience_years: Years of experience
        include_startups: Include startup companies
        include_enterprise: Include enterprise companies
        custom_terms: Additional search terms from user
        api_key: Groq API key
        
    Returns:
        List of search queries to use
    """
    skill_str = ", ".join(skills[:5]) if skills else ""
    
    system_prompt = """You are a search query optimizer. Generate effective search queries to find company career pages for job seekers.
Return ONLY a JSON array of 5-8 search query strings. No explanation."""
    
    user_prompt = f"""Generate search queries to find career pages for:
- Role: {role}
- Skills: {skill_str}
- Location: {location}
- Experience: {experience_years} years
- Include startups: {include_startups}
- Include enterprise: {include_enterprise}

Focus on finding direct company career pages, not job aggregators.
Include queries like:
- "[role] careers [location]"
- "[skill] company hiring"
- "startup hiring [role]"
- Site-specific: "site:greenhouse.io [role]"

Return JSON array of strings only."""

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": settings.groq_model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    "temperature": 0.7,
                    "max_tokens": 500
                }
            )
            
            if response.status_code == 200:
                content = response.json()["choices"][0]["message"]["content"]
                # Parse JSON from response
                queries = json.loads(content)
                if isinstance(queries, list):
                    # Add custom terms
                    queries.extend(custom_terms)
                    return queries[:10]  # Cap at 10 queries
            
            logger.warning(f"LLM query generation failed: {response.status_code}")
    except Exception as e:
        logger.error(f"Error generating queries: {e}")
    
    # Fallback to basic queries
    basic_queries = [
        f"{role} careers {location}",
        f"{role} jobs company hiring",
        f"site:greenhouse.io {role}",
        f"site:lever.co {role}",
    ]
    if skills:
        basic_queries.append(f"{skills[0]} developer jobs {location}")
    basic_queries.extend(custom_terms)
    return basic_queries


def is_valid_career_url(url: str) -> bool:
    """Check if URL is likely a career page and not an excluded domain."""
    try:
        parsed = urlparse(url)
        domain = parsed.netloc.lower()
        
        # Exclude job aggregators
        for excluded in EXCLUDED_DOMAINS:
            if excluded in domain:
                return False
        
        # Check for career page patterns
        full_url = url.lower()
        for pattern in CAREER_PAGE_PATTERNS:
            if re.search(pattern, full_url):
                return True
        
        # Also accept if it has job-related keywords
        if any(kw in full_url for kw in ['career', 'job', 'hiring', 'join', 'work']):
            return True
            
        return False
    except:
        return False


async def discover_career_pages(queries: list[str], max_results: int) -> list[str]:
    """
    Search the web for career pages using DuckDuckGo.
    
    Args:
        queries: Search queries to use
        max_results: Maximum number of URLs to return
        
    Returns:
        List of career page URLs
    """
    discovered_urls = set()
    
    try:
        ddgs = DDGS()
        
        for query in queries:
            if len(discovered_urls) >= max_results:
                break
                
            logger.info(f"Searching: {query}")
            
            try:
                # Search with DuckDuckGo
                results = ddgs.text(query, max_results=10)
                
                for result in results:
                    url = result.get('href', '')
                    if url and is_valid_career_url(url):
                        discovered_urls.add(url)
                        
                        if len(discovered_urls) >= max_results:
                            break
                            
            except Exception as e:
                logger.warning(f"Search error for '{query}': {e}")
                continue
                
            # Small delay between queries to be respectful
            await asyncio.sleep(0.5)
            
    except Exception as e:
        logger.error(f"Discovery error: {e}")
    
    return list(discovered_urls)[:max_results]


async def crawl_page(url: str, timeout: int = 30) -> Optional[str]:
    """
    Crawl a webpage and extract text content.
    
    Args:
        url: URL to crawl
        timeout: Request timeout in seconds
        
    Returns:
        Cleaned text content or None if failed
    """
    try:
        async with httpx.AsyncClient(
            timeout=timeout,
            follow_redirects=True,
            headers={
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
            }
        ) as client:
            response = await client.get(url)
            
            if response.status_code != 200:
                logger.warning(f"Failed to crawl {url}: {response.status_code}")
                return None
            
            # Parse HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Remove script and style elements
            for element in soup(['script', 'style', 'nav', 'footer', 'header']):
                element.decompose()
            
            # Get text content
            text = soup.get_text(separator='\n', strip=True)
            
            # Limit text length for LLM
            if len(text) > 15000:
                text = text[:15000]
            
            return text
            
    except Exception as e:
        logger.error(f"Crawl error for {url}: {e}")
        return None


async def extract_jobs_from_content(
    content: str,
    source_url: str,
    role: str,
    api_key: str
) -> list[DiscoveredJob]:
    """
    Use LLM to extract structured job data from page content.
    
    Args:
        content: Page text content
        source_url: Original URL of the page
        role: Target role to filter for
        api_key: Groq API key
        
    Returns:
        List of discovered jobs
    """
    if not content or len(content) < 100:
        return []
    
    system_prompt = """You are a job data extractor. Extract job listings from webpage content.
Return ONLY valid JSON array. Each job object must have these fields:
- title: job title (string)
- company: company name (string)
- location: job location or "Remote" (string or null)
- description: brief job description (string, max 500 chars)
- apply_url: application URL if found, otherwise use source_url (string)
- salary_range: salary if mentioned (string or null)
- job_type: full-time/part-time/contract (string or null)
- requirements: list of key requirements (array of strings, max 5)
- confidence_score: how confident you are this is a real job 0.0-1.0 (number)

Return empty array [] if no relevant jobs found. No explanations."""

    user_prompt = f"""Extract job listings relevant to "{role}" from this career page content.
Source URL: {source_url}

Page Content:
{content[:12000]}

Return JSON array of jobs:"""

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": settings.groq_model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    "temperature": 0.3,
                    "max_tokens": 2000
                }
            )
            
            if response.status_code != 200:
                logger.warning(f"LLM extraction failed: {response.status_code}")
                return []
            
            content = response.json()["choices"][0]["message"]["content"]
            
            # Try to parse JSON from response
            # Handle potential markdown code blocks
            content = content.strip()
            if content.startswith("```"):
                content = re.sub(r'^```\w*\n?', '', content)
                content = re.sub(r'\n?```$', '', content)
            
            jobs_data = json.loads(content)
            
            if not isinstance(jobs_data, list):
                return []
            
            jobs = []
            for job_dict in jobs_data:
                try:
                    # Ensure apply_url is set
                    if not job_dict.get('apply_url'):
                        job_dict['apply_url'] = source_url
                    job_dict['source_url'] = source_url
                    
                    # Create DiscoveredJob instance
                    job = DiscoveredJob(**job_dict)
                    jobs.append(job)
                except Exception as e:
                    logger.warning(f"Failed to parse job: {e}")
                    continue
            
            return jobs
            
    except json.JSONDecodeError as e:
        logger.warning(f"JSON parse error: {e}")
        return []
    except Exception as e:
        logger.error(f"Extraction error: {e}")
        return []


async def discover_jobs(
    request: DiscoverJobsRequest,
    api_key: str
) -> tuple[list[DiscoveredJob], list[str], int, list[str]]:
    """
    Main discovery function that orchestrates the entire flow.
    
    Args:
        request: Discovery request parameters
        api_key: Groq API key
        
    Returns:
        Tuple of (jobs, search_queries_used, sources_crawled, errors)
    """
    errors = []
    
    # Step 1: Generate search queries
    logger.info("Generating search queries...")
    queries = await generate_search_queries(
        role=request.role,
        skills=request.skills,
        location=request.location,
        experience_years=request.experience_years,
        include_startups=request.include_startups,
        include_enterprise=request.include_enterprise,
        custom_terms=request.custom_search_terms,
        api_key=api_key
    )
    logger.info(f"Generated {len(queries)} search queries")
    
    # Step 2: Discover career pages
    logger.info("Discovering career pages...")
    urls = await discover_career_pages(queries, max_results=request.max_results)
    logger.info(f"Found {len(urls)} career page URLs")
    
    if not urls:
        errors.append("No career pages found for given criteria")
        return [], queries, 0, errors
    
    # Step 3: Crawl pages and extract jobs (with concurrency limit)
    all_jobs = []
    sources_crawled = 0
    
    # Process URLs with limited concurrency
    semaphore = asyncio.Semaphore(5)  # Max 5 concurrent crawls
    
    async def process_url(url: str) -> list[DiscoveredJob]:
        nonlocal sources_crawled
        async with semaphore:
            logger.info(f"Crawling: {url}")
            content = await crawl_page(url)
            
            if content:
                sources_crawled += 1
                jobs = await extract_jobs_from_content(
                    content=content,
                    source_url=url,
                    role=request.role,
                    api_key=api_key
                )
                logger.info(f"Extracted {len(jobs)} jobs from {url}")
                return jobs
            else:
                errors.append(f"Failed to crawl: {url}")
                return []
    
    # Run all crawl tasks
    tasks = [process_url(url) for url in urls]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    for result in results:
        if isinstance(result, Exception):
            errors.append(str(result))
        elif isinstance(result, list):
            all_jobs.extend(result)
    
    # Sort by confidence score and limit results
    all_jobs.sort(key=lambda j: j.confidence_score, reverse=True)
    all_jobs = all_jobs[:request.max_results]
    
    logger.info(f"Discovery complete: {len(all_jobs)} jobs from {sources_crawled} sources")
    
    return all_jobs, queries, sources_crawled, errors
