"""
Pydantic models for request/response validation
"""
from pydantic import BaseModel
from typing import List, Optional


class JobSearchRequest(BaseModel):
    """Job search request schema"""
    sites: List[str] = ["indeed", "linkedin", "zip_recruiter"]
    search_term: str = "developer"
    location: str = "Remote"
    results_wanted: int = 20
    hours_old: int = 72
    is_remote: bool = True
    country_indeed: str = "USA"
    experience_level: Optional[str] = None


class TailorCVRequest(BaseModel):
    """CV tailoring request schema"""
    title: str
    company: Optional[str] = "N/A"
    description: str
    url: Optional[str] = None  # Job URL
    cv_template: Optional[str] = None  # Optional custom CV template


class JobSearchResponse(BaseModel):
    """Job search response schema"""
    jobs: List[dict]
    count: int


class TailorCVResponse(BaseModel):
    """CV tailoring response schema"""
    success: bool
    cv_pdf: str
    cover_letter_pdf: str
    cv_text: str
    cover_letter_text: str
    job_title: str
    company: str
    url: Optional[str] = None
    api_key_used: str
    attempt: int
    message: str


class HealthResponse(BaseModel):
    """Health check response schema"""
    status: str


class APIKeysStatusResponse(BaseModel):
    """API keys status response schema"""
    total_keys: int
    current_key_index: int
    failed_keys_count: int
    cooldown_minutes: int
    has_available_keys: bool

