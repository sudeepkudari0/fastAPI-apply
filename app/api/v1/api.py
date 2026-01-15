"""
API v1 router aggregator
"""
from fastapi import APIRouter
from app.api.v1.endpoints import health, jobs, cv, discovery


api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(health.router, tags=["health"])
api_router.include_router(jobs.router, tags=["jobs"])
api_router.include_router(cv.router, tags=["cv"])
api_router.include_router(discovery.router, prefix="/discovery", tags=["discovery"])


