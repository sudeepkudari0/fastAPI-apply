"""
Groq AI service for CV and cover letter generation
"""
import httpx
from typing import Tuple
from fastapi import HTTPException
from app.core.config import settings
from app.core.logging import get_logger


logger = get_logger(__name__)


# Default CV template
DEFAULT_CV_TEMPLATE = """John Doe
Full Stack Developer
Email: john@example.com | Phone: +1234567890

SUMMARY
Experienced developer with 2 years in React, Node.js, Python...

SKILLS
- Languages: JavaScript, Python, TypeScript
- Frontend: React, Next.js, Tailwind
- Backend: Node.js, Express, FastAPI
- Database: PostgreSQL, MongoDB

EXPERIENCE
Software Engineer - ABC Corp (2022-2024)
- Built full-stack applications using React and Node.js
- Improved application performance by 40%
- Led team of 3 developers

EDUCATION
B.Tech Computer Science - XYZ University (2020-2022)"""


async def call_groq_api(prompt: str, system_prompt: str, api_key: str) -> httpx.Response:
    """
    Helper function to call Groq API
    
    Args:
        prompt: User prompt
        system_prompt: System prompt
        api_key: Groq API key
        
    Returns:
        HTTP response from Groq API
    """
    async with httpx.AsyncClient(timeout=settings.groq_timeout) as client:
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
                    {"role": "user", "content": prompt}
                ],
                "temperature": settings.groq_temperature,
                "max_tokens": settings.groq_max_tokens
            }
        )
        return response


def create_cv_prompt(cv_template: str, job_title: str, company: str, description: str) -> Tuple[str, str]:
    """
    Create system and user prompts for CV tailoring
    
    Returns:
        Tuple of (system_prompt, user_prompt)
    """
    system_prompt = "You are a professional CV writer who tailors resumes to job descriptions while maintaining formatting."
    
    user_prompt = f"""You are a professional CV writer. Tailor this CV to match the job description below.

IMPORTANT RULES:
1. Keep the EXACT same formatting and structure
2. Keep the same section headers (SUMMARY, SKILLS, EXPERIENCE, EDUCATION)
3. Only modify the content to highlight relevant skills for this specific job
4. Keep it concise - same length as original
5. Make it ATS-friendly
6. Return ONLY the tailored CV, no explanations

Original CV:
{cv_template}

Job Title: {job_title}
Company: {company}

Job Description:
{description or 'No description provided'}

Tailored CV:"""
    
    return system_prompt, user_prompt


def create_cover_letter_prompt(cv_template: str, job_title: str, company: str, description: str) -> Tuple[str, str]:
    """
    Create system and user prompts for cover letter generation
    
    Returns:
        Tuple of (system_prompt, user_prompt)
    """
    system_prompt = "You are a professional cover letter writer who creates compelling, personalized cover letters."
    
    user_prompt = f"""Write a professional cover letter for this job application.

IMPORTANT RULES:
1. Professional and compelling tone
2. Highlight relevant skills from the CV template
3. Show enthusiasm for the role and company
4. Keep it concise (250-300 words)
5. Include proper greeting and closing
6. Return ONLY the cover letter, no explanations

CV Information:
{cv_template}

Job Title: {job_title}
Company: {company}

Job Description:
{description or 'No description provided'}

Cover Letter:"""
    
    return system_prompt, user_prompt


async def generate_tailored_content(
    job_title: str,
    company: str,
    description: str,
    cv_template: str,
    api_key: str
) -> Tuple[str, str]:
    """
    Generate tailored CV and cover letter using Groq AI
    
    Args:
        job_title: Job title
        company: Company name
        description: Job description
        cv_template: CV template to tailor
        api_key: Groq API key
        
    Returns:
        Tuple of (tailored_cv, cover_letter)
        
    Raises:
        HTTPException: If API call fails
    """
    logger.info(f"Generating tailored content for {job_title} at {company}")
    
    # Generate tailored CV
    cv_system_prompt, cv_user_prompt = create_cv_prompt(cv_template, job_title, company, description)
    
    logger.info("Generating tailored CV...")
    cv_response = await call_groq_api(cv_user_prompt, cv_system_prompt, api_key)
    
    if cv_response.status_code != 200:
        error_detail = cv_response.text
        logger.error(f"CV API error (status {cv_response.status_code}): {error_detail}")
        raise HTTPException(status_code=cv_response.status_code, detail=error_detail)
    
    cv_result = cv_response.json()
    tailored_cv = cv_result.get("choices", [{}])[0].get("message", {}).get("content", "")
    
    if not tailored_cv:
        raise HTTPException(status_code=500, detail="Empty CV response from AI")
    
    logger.info("Successfully generated tailored CV")
    
    # Generate cover letter
    cl_system_prompt, cl_user_prompt = create_cover_letter_prompt(cv_template, job_title, company, description)
    
    logger.info("Generating cover letter...")
    cl_response = await call_groq_api(cl_user_prompt, cl_system_prompt, api_key)
    
    if cl_response.status_code != 200:
        error_detail = cl_response.text
        logger.error(f"Cover letter API error (status {cl_response.status_code}): {error_detail}")
        raise HTTPException(status_code=cl_response.status_code, detail=error_detail)
    
    cl_result = cl_response.json()
    cover_letter = cl_result.get("choices", [{}])[0].get("message", {}).get("content", "")
    
    if not cover_letter:
        raise HTTPException(status_code=500, detail="Empty cover letter response from AI")
    
    logger.info("Successfully generated cover letter")
    
    return tailored_cv, cover_letter

