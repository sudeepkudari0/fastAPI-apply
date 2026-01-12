"""
Dependency injection for API endpoints
"""
from app.core.api_key_manager import GroqAPIKeyManager
from app.core.config import settings


# Initialize the API key manager as a singleton
_groq_key_manager = None


def get_groq_key_manager() -> GroqAPIKeyManager:
    """Get the Groq API key manager instance"""
    global _groq_key_manager
    if _groq_key_manager is None:
        _groq_key_manager = GroqAPIKeyManager(
            api_keys=settings.groq_api_keys_list,
            cooldown_minutes=settings.api_key_cooldown_minutes
        )
    return _groq_key_manager

