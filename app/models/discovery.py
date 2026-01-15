"""
Discovery models for internet-wide job search
"""
from pydantic import BaseModel, Field
from typing import Optional


class DiscoverJobsRequest(BaseModel):
    """Request to discover jobs from internet"""
    role: str = Field(..., description="Target role, e.g. 'Full Stack Developer'")
    experience_years: int = Field(default=2, description="Years of experience")
    skills: list[str] = Field(default_factory=list, description="Key skills to match")
    location: str = Field(default="Remote", description="Preferred location")
    max_results: int = Field(default=20, le=20, description="Max results (capped at 20)")
    include_startups: bool = Field(default=True, description="Include startup companies")
    include_enterprise: bool = Field(default=True, description="Include enterprise companies")
    custom_search_terms: list[str] = Field(default_factory=list, description="Additional search terms")


class DiscoveredJob(BaseModel):
    """Structured job extracted from any website"""
    title: str
    company: str
    location: Optional[str] = None
    description: str
    apply_url: str
    source_url: str
    salary_range: Optional[str] = None
    job_type: Optional[str] = None
    posted_date: Optional[str] = None
    requirements: list[str] = Field(default_factory=list)
    confidence_score: float = Field(default=0.0, ge=0.0, le=1.0)


class DiscoverJobsResponse(BaseModel):
    """Response with discovered jobs"""
    jobs: list[DiscoveredJob]
    count: int
    search_queries_used: list[str]
    sources_crawled: int
    errors: list[str] = Field(default_factory=list)
