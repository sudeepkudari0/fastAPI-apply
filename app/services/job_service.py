"""
Job scraping service
"""
from jobspy import scrape_jobs
from typing import List, Optional
import pandas as pd
import numpy as np
from app.core.logging import get_logger


logger = get_logger(__name__)


def scrape_job_listings(
    sites: List[str],
    search_term: str,
    location: str,
    results_wanted: int,
    hours_old: int,
    is_remote: bool,
    country_indeed: str,
    experience_level: Optional[str] = None
) -> List[dict]:
    """
    Scrape job listings from various job boards
    
    Args:
        sites: List of job sites to scrape
        search_term: Search term for jobs
        location: Job location
        results_wanted: Number of results to return
        hours_old: Filter jobs posted within this many hours
        is_remote: Filter for remote jobs
        country_indeed: Country for Indeed searches
        experience_level: Filter by experience level
        
    Returns:
        List of job dictionaries
    """
    logger.info(f"Scraping jobs: {search_term} in {location} from {sites}")
    
    jobs_df = scrape_jobs(
        site_name=sites,
        search_term=search_term,
        location=location,
        results_wanted=results_wanted,
        hours_old=hours_old,
        is_remote=is_remote,
        country_indeed=country_indeed
    )

    if jobs_df is None or jobs_df.empty:
        logger.warning("No jobs found")
        return []

    # Filter by experience if needed
    if experience_level:
        logger.info(f"Filtering by experience level: {experience_level}")
        jobs_df = jobs_df[
            jobs_df["description"].str.contains(
                f"{experience_level}|0-3 years|entry level",
                case=False,
                na=False
            )
        ]

    # Replace NaN/infinity with None for JSON compatibility
    jobs_df = jobs_df.replace([np.nan, np.inf, -np.inf], None)

    jobs_list = jobs_df.to_dict(orient="records")
    
    logger.info(f"Found {len(jobs_list)} jobs")
    return jobs_list

