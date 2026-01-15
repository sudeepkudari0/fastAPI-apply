"""
Resume tailoring endpoints - generates styled PDFs matching original resume format
"""
from fastapi import APIRouter, HTTPException, Depends
import base64
import httpx
from app.models.schemas import TailorCVRequest, TailorCVResponse
from app.models.resume import ResumeData
from app.services.resume_loader import load_resume_from_yaml
from app.services.resume_tailor_service import tailor_resume_content, generate_cover_letter
from app.services.resume_pdf_service import generate_styled_resume_pdf
from app.services.pdf_service import generate_pdf_from_text
from app.api.deps import get_groq_key_manager
from app.core.api_key_manager import GroqAPIKeyManager
from app.core.logging import get_logger


router = APIRouter()
logger = get_logger(__name__)


@router.post("/tailor-cv", response_model=TailorCVResponse)
async def tailor_cv(
    request: TailorCVRequest,
    key_manager: GroqAPIKeyManager = Depends(get_groq_key_manager)
):
    """
    Tailor a CV and generate a cover letter for a job using Groq AI.
    Returns styled PDF matching user's original resume format.
    
    Args:
        request: CV tailoring request with job details
        key_manager: API key manager dependency
        
    Returns:
        Tailored CV and cover letter as PDFs and text
    """
    
    if not key_manager.api_keys:
        raise HTTPException(
            status_code=500, 
            detail="No Groq API keys configured. Set GROQ_API_KEYS environment variable."
        )
    
    # Load base resume from YAML
    try:
        base_resume = load_resume_from_yaml()
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=500,
            detail="Resume template not found. Please add your resume to public/resume_template.yaml"
        )
    except ValueError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Invalid resume template: {str(e)}"
        )
    
    # Try each available API key
    max_retries = len(key_manager.api_keys)
    last_error = None
    
    for attempt in range(max_retries):
        api_key = key_manager.get_available_key()
        
        if not api_key:
            raise HTTPException(
                status_code=503,
                detail="All API keys are currently unavailable. Please try again later."
            )
        
        try:
            logger.info(f"Attempt {attempt + 1}/{max_retries} - Using API key: {api_key[:10]}...")
            
            # Tailor resume content using AI
            tailored_resume = await tailor_resume_content(
                resume_data=base_resume,
                job_title=request.title,
                company=request.company,
                description=request.description,
                api_key=api_key
            )
            
            # Generate cover letter
            cover_letter = await generate_cover_letter(
                resume_data=tailored_resume,
                job_title=request.title,
                company=request.company,
                description=request.description,
                api_key=api_key
            )
            
            # Generate styled resume PDF
            logger.info("Generating styled resume PDF...")
            cv_pdf_buffer = generate_styled_resume_pdf(tailored_resume)
            
            # Generate cover letter PDF (using existing simple PDF service)
            logger.info("Generating cover letter PDF...")
            cl_pdf_buffer = generate_pdf_from_text(cover_letter, f"CoverLetter_{request.title}")
            
            # Convert to base64
            cv_pdf_base64 = base64.b64encode(cv_pdf_buffer.read()).decode('utf-8')
            cl_pdf_base64 = base64.b64encode(cl_pdf_buffer.read()).decode('utf-8')
            
            # Generate text version of CV for response
            cv_text = _resume_to_text(tailored_resume)
            
            logger.info(f"Successfully completed all tasks using API key: {api_key[:10]}...")
            
            return TailorCVResponse(
                success=True,
                cv_pdf=cv_pdf_base64,
                cover_letter_pdf=cl_pdf_base64,
                cv_text=cv_text,
                cover_letter_text=cover_letter,
                job_title=request.title,
                company=request.company,
                url=request.url,
                api_key_used=api_key[:10] + "...",
                attempt=attempt + 1,
                message="Styled CV and Cover Letter PDFs generated successfully"
            )
        
        except HTTPException as e:
            # Check if it's a rate limit or quota error
            if e.status_code in [429, 403]:
                logger.warning(f"Rate limit/quota error for API key: {api_key[:10]}...")
                key_manager.mark_key_failed(api_key)
                last_error = e.detail
                continue
            
            # Check error message for rate limit indicators
            error_detail = str(e.detail).lower()
            if any(keyword in error_detail for keyword in ["rate", "quota", "limit"]):
                key_manager.mark_key_failed(api_key)
                last_error = e.detail
                continue
            
            # Other HTTP exceptions should be re-raised
            raise
        
        except httpx.TimeoutException:
            logger.error(f"Timeout with API key: {api_key[:10]}...")
            last_error = "Request timeout"
            continue
        
        except Exception as e:
            logger.error(f"Error with API key {api_key[:10]}...: {str(e)}")
            last_error = str(e)
            continue
    
    # All retries failed
    raise HTTPException(
        status_code=503,
        detail=f"Failed to generate CV and cover letter after {max_retries} attempts. Last error: {last_error}"
    )


def _resume_to_text(resume: ResumeData) -> str:
    """Convert ResumeData to plain text format for API response"""
    lines = []
    
    # Personal info
    lines.append(resume.personal.name)
    if resume.personal.portfolio:
        lines.append(f"Portfolio: {resume.personal.portfolio}")
    lines.append(f"Email: {resume.personal.email}")
    lines.append(f"Phone: {resume.personal.phone}")
    if resume.personal.linkedin:
        lines.append(f"LinkedIn: {resume.personal.linkedin}")
    lines.append("")
    
    # Summary
    lines.append(resume.summary)
    lines.append("")
    
    # Employment
    lines.append("EMPLOYMENT HISTORY")
    lines.append("-" * 40)
    for emp in resume.employment:
        lines.append(f"{emp.position}, {emp.company}")
        lines.append(f"Duration: {emp.duration}")
        if emp.technologies:
            lines.append(f"Technologies: {emp.technologies}")
        for role in emp.roles:
            lines.append(f"  {role.title}:")
            for bullet in role.bullets:
                lines.append(f"    - {bullet}")
        lines.append("")
    
    # Projects
    lines.append("PROJECTS")
    lines.append("-" * 40)
    for project in resume.projects:
        title = project.name
        if project.url:
            title += f" | {project.url}"
        lines.append(title)
        for bullet in project.bullets:
            lines.append(f"  - {bullet}")
        lines.append("")
    
    # Skills
    lines.append("SKILLS")
    lines.append("-" * 40)
    lines.append(resume.skills)
    lines.append("")
    
    # Education
    lines.append("EDUCATION")
    lines.append("-" * 40)
    lines.append(f"{resume.education.degree}, {resume.education.institution}")
    edu_text = resume.education.duration
    if resume.education.cgpa:
        edu_text += f" | CGPA - {resume.education.cgpa}"
    lines.append(edu_text)
    
    return "\n".join(lines)
