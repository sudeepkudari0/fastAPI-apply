"""
Job scraping endpoints
"""
from fastapi import APIRouter, HTTPException
from app.models.schemas import JobSearchRequest, JobSearchResponse
from app.services.job_service import scrape_job_listings


router = APIRouter()


@router.post("/scrape", response_model=JobSearchResponse)
def scrape_jobs_endpoint(request: JobSearchRequest):
    """
    Scrape job listings from various job boards
    
    Args:
        request: Job search parameters
        
    Returns:
        List of scraped jobs with count
    """
    try:
        jobs_list = scrape_job_listings(
            sites=request.sites,
            search_term=request.search_term,
            location=request.location,
            results_wanted=request.results_wanted,
            hours_old=request.hours_old,
            is_remote=request.is_remote,
            country_indeed=request.country_indeed,
            experience_level=request.experience_level
        )

        return {
            "jobs": jobs_list,
            "count": len(jobs_list)
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

