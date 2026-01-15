"""
Resume tailoring service using Groq AI
Tailors structured resume data based on job descriptions
"""
import json
import httpx
from typing import Optional
from fastapi import HTTPException
from app.core.config import settings
from app.core.logging import get_logger
from app.models.resume import ResumeData


logger = get_logger(__name__)


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


def create_resume_tailoring_prompts(resume_data: ResumeData, job_title: str, company: str, description: str) -> tuple[str, str]:
    """
    Create prompts for tailoring resume content to a job description
    
    Returns:
        Tuple of (system_prompt, user_prompt)
    """
    resume_json = resume_data.model_dump_json(indent=2)
    
    system_prompt = """You are an expert resume writer and career coach. Your task is to tailor resume content to match specific job descriptions while maintaining the candidate's authentic experience.

CRITICAL RULES:
1. Return ONLY valid JSON matching the exact same structure as the input
2. Keep ALL personal information unchanged (name, email, phone, portfolio, linkedin)
3. Modify the summary to highlight relevant skills for this role
4. Reword employment bullets to emphasize relevant experience
5. Reorder or emphasize skills based on job requirements
6. Keep the same structure - do not add or remove sections
7. Maintain professional tone and ATS-friendly language
8. Do NOT invent new experiences - only rephrase existing ones
9. Keep bullet points concise and impactful"""

    user_prompt = f"""Tailor this resume for the following job:

**Job Title:** {job_title}
**Company:** {company}

**Job Description:**
{description or 'No description provided - optimize for the job title'}

**Current Resume (JSON):**
```json
{resume_json}
```

Return the tailored resume as valid JSON with the exact same structure. Only modify content to better match this specific role."""

    return system_prompt, user_prompt


def create_cover_letter_prompts(resume_data: ResumeData, job_title: str, company: str, description: str) -> tuple[str, str]:
    """
    Create prompts for generating a cover letter
    
    Returns:
        Tuple of (system_prompt, user_prompt)
    """
    resume_json = resume_data.model_dump_json(indent=2)
    
    system_prompt = """You are a professional cover letter writer who creates compelling, personalized cover letters that get interviews."""

    user_prompt = f"""Write a professional cover letter for this job application.

**Job Title:** {job_title}
**Company:** {company}

**Job Description:**
{description or 'No description provided'}

**Candidate's Resume:**
```json
{resume_json}
```

IMPORTANT RULES:
1. Professional and compelling tone
2. Highlight relevant skills from the resume
3. Show enthusiasm for the role and company
4. Keep it concise (250-300 words)
5. Include proper greeting and closing
6. Return ONLY the cover letter text, no explanations or JSON"""

    return system_prompt, user_prompt


async def tailor_resume_content(
    resume_data: ResumeData,
    job_title: str,
    company: str,
    description: str,
    api_key: str
) -> ResumeData:
    """
    Tailor resume content using Groq AI
    
    Args:
        resume_data: Original structured resume data
        job_title: Target job title
        company: Target company name
        description: Job description
        api_key: Groq API key
        
    Returns:
        Tailored ResumeData
        
    Raises:
        HTTPException: If API call fails
    """
    logger.info(f"Tailoring resume for {job_title} at {company}")
    
    system_prompt, user_prompt = create_resume_tailoring_prompts(
        resume_data, job_title, company, description
    )
    
    response = await call_groq_api(user_prompt, system_prompt, api_key)
    
    if response.status_code != 200:
        error_detail = response.text
        logger.error(f"Resume tailoring API error (status {response.status_code}): {error_detail}")
        raise HTTPException(status_code=response.status_code, detail=error_detail)
    
    result = response.json()
    content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
    
    if not content:
        raise HTTPException(status_code=500, detail="Empty response from AI")
    
    # Parse the JSON response
    try:
        # Clean up the response - remove markdown code blocks if present
        content = content.strip()
        if content.startswith("```json"):
            content = content[7:]
        if content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()
        
        tailored_data = json.loads(content)
        tailored_resume = ResumeData(**tailored_data)
        logger.info("Successfully tailored resume content")
        return tailored_resume
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse AI response as JSON: {e}")
        logger.error(f"Response content: {content[:500]}...")
        raise HTTPException(
            status_code=500, 
            detail=f"AI returned invalid JSON format: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Failed to validate tailored resume: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to validate tailored resume structure: {str(e)}"
        )


async def generate_cover_letter(
    resume_data: ResumeData,
    job_title: str,
    company: str,
    description: str,
    api_key: str
) -> str:
    """
    Generate a cover letter using Groq AI
    
    Args:
        resume_data: Structured resume data
        job_title: Target job title
        company: Target company name
        description: Job description
        api_key: Groq API key
        
    Returns:
        Cover letter text
        
    Raises:
        HTTPException: If API call fails
    """
    logger.info(f"Generating cover letter for {job_title} at {company}")
    
    system_prompt, user_prompt = create_cover_letter_prompts(
        resume_data, job_title, company, description
    )
    
    response = await call_groq_api(user_prompt, system_prompt, api_key)
    
    if response.status_code != 200:
        error_detail = response.text
        logger.error(f"Cover letter API error (status {response.status_code}): {error_detail}")
        raise HTTPException(status_code=response.status_code, detail=error_detail)
    
    result = response.json()
    cover_letter = result.get("choices", [{}])[0].get("message", {}).get("content", "")
    
    if not cover_letter:
        raise HTTPException(status_code=500, detail="Empty cover letter response from AI")
    
    logger.info("Successfully generated cover letter")
    return cover_letter
