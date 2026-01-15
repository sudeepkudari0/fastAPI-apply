"""
Job discovery endpoints for internet-wide job search
"""
from fastapi import APIRouter, HTTPException, Depends

from app.models.discovery import (
    DiscoverJobsRequest,
    DiscoverJobsResponse,
)
from app.services.discovery_service import discover_jobs
from app.api.deps import get_groq_key_manager
from app.core.api_key_manager import GroqAPIKeyManager
from app.core.logging import get_logger

router = APIRouter()
logger = get_logger(__name__)


@router.post("/discover", response_model=DiscoverJobsResponse)
async def discover_jobs_endpoint(
    request: DiscoverJobsRequest,
    key_manager: GroqAPIKeyManager = Depends(get_groq_key_manager)
):
    """
    Discover jobs from across the internet based on your profile.
    
    This endpoint:
    1. Generates smart search queries using AI based on your role/skills
    2. Searches the web for company career pages 
    3. Crawls and extracts job listings using AI
    4. Returns structured job data
    
    **Limits:**
    - Max 20 results for real-time performance
    - Excludes job aggregators (Indeed, LinkedIn, etc.) - focuses on direct company pages
    
    **Best for:**
    - Finding jobs at startups and companies not on major job boards
    - Discovering opportunities on Greenhouse, Lever, and direct career pages
    """
    logger.info(f"Discovery request: {request.role} in {request.location}")
    
    # Get available API key
    api_key = key_manager.get_available_key()
    if not api_key:
        raise HTTPException(
            status_code=503,
            detail="No API keys available. Please try again later."
        )
    
    try:
        jobs, queries_used, sources_crawled, errors = await discover_jobs(
            request=request,
            api_key=api_key
        )
        
        return DiscoverJobsResponse(
            jobs=jobs,
            count=len(jobs),
            search_queries_used=queries_used,
            sources_crawled=sources_crawled,
            errors=errors
        )
        
    except Exception as e:
        logger.error(f"Discovery error: {e}")
        key_manager.mark_key_failed(api_key)
        raise HTTPException(status_code=500, detail=str(e))
