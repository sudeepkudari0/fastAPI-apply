"""
CV and cover letter tailoring endpoints
"""
from fastapi import APIRouter, HTTPException, Depends
import base64
import httpx
from app.models.schemas import TailorCVRequest, TailorCVResponse
from app.services.groq_service import generate_tailored_content, DEFAULT_CV_TEMPLATE
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
    Returns both as PDF files (base64 encoded) with automatic API key failover.
    
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
    
    cv_template = request.cv_template or DEFAULT_CV_TEMPLATE
    
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
            
            # Generate tailored CV and cover letter
            tailored_cv, cover_letter = await generate_tailored_content(
                job_title=request.title,
                company=request.company,
                description=request.description,
                cv_template=cv_template,
                api_key=api_key
            )
            
            # Generate PDFs
            logger.info("Generating PDF files...")
            cv_pdf_buffer = generate_pdf_from_text(tailored_cv, f"CV_{request.title}")
            cl_pdf_buffer = generate_pdf_from_text(cover_letter, f"CoverLetter_{request.title}")
            
            # Convert to base64
            cv_pdf_base64 = base64.b64encode(cv_pdf_buffer.read()).decode('utf-8')
            cl_pdf_base64 = base64.b64encode(cl_pdf_buffer.read()).decode('utf-8')
            
            logger.info(f"Successfully completed all tasks using API key: {api_key[:10]}...")
            
            return TailorCVResponse(
                success=True,
                cv_pdf=cv_pdf_base64,
                cover_letter_pdf=cl_pdf_base64,
                cv_text=tailored_cv,
                cover_letter_text=cover_letter,
                job_title=request.title,
                company=request.company,
                url=request.url,
                api_key_used=api_key[:10] + "...",
                attempt=attempt + 1,
                message="CV and Cover Letter PDFs generated successfully"
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

