"""
Health check and status endpoints
"""
from fastapi import APIRouter, Depends
from app.models.schemas import HealthResponse, APIKeysStatusResponse
from app.api.deps import get_groq_key_manager
from app.core.api_key_manager import GroqAPIKeyManager


router = APIRouter()


@router.get("/", response_model=dict)
def read_root():
    """Root endpoint"""
    return {"status": "JobSpy API is running"}


@router.get("/health", response_model=HealthResponse)
def health_check():
    """Health check endpoint"""
    return {"status": "healthy"}


@router.get("/api-keys/status", response_model=APIKeysStatusResponse)
def get_api_keys_status(
    key_manager: GroqAPIKeyManager = Depends(get_groq_key_manager)
):
    """Get the status of all API keys"""
    return key_manager.get_status()

