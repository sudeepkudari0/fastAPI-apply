from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from jobspy import scrape_jobs
from typing import List, Optional
import pandas as pd

app = FastAPI(title="JobSpy API")

class JobSearchRequest(BaseModel):
    sites: List[str] = ["indeed", "linkedin", "zip_recruiter"]
    search_term: str = "developer"
    location: str = "Remote"
    results_wanted: int = 20
    hours_old: int = 72
    is_remote: bool = True
    country_indeed: str = "USA"
    experience_level: Optional[str] = None  # entry, mid, senior

@app.get("/")
def read_root():
    return {"status": "JobSpy API is running"}

@app.post("/scrape")
def scrape_jobs_endpoint(request: JobSearchRequest):
    try:
        jobs_df = scrape_jobs(
            site_name=request.sites,
            search_term=request.search_term,
            location=request.location,
            results_wanted=request.results_wanted,
            hours_old=request.hours_old,
            is_remote=request.is_remote,
            country_indeed=request.country_indeed
        )
        
        if jobs_df is None or jobs_df.empty:
            return {"jobs": [], "count": 0}
        
        # Filter by experience if needed
        if request.experience_level:
            # Basic filtering - you can enhance this
            jobs_df = jobs_df[
                jobs_df['description'].str.contains(
                    f"{request.experience_level}|0-3 years|entry level",
                    case=False, na=False
                )
            ]
        
        jobs_list = jobs_df.to_dict(orient='records')
        
        return {
            "jobs": jobs_list,
            "count": len(jobs_list)
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
def health_check():
    return {"status": "healthy"}
```

**`requirements.txt`:**
```
fastapi
uvicorn[standard]
python-jobspy
pandas