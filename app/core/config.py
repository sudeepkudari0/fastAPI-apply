"""
Application configuration settings
"""
from pydantic_settings import BaseSettings
from typing import List
import os


class Settings(BaseSettings):
    """Application settings"""
    
    # API Settings
    app_name: str = "JobSpy API"
    app_version: str = "1.0.0"
    
    # Groq API Settings
    groq_api_keys: str = ""
    groq_model: str = "llama-3.3-70b-versatile"
    groq_timeout: float = 60.0
    groq_max_tokens: int = 2000
    groq_temperature: float = 0.7
    
    # API Key Manager Settings
    api_key_cooldown_minutes: int = 5
    
    # Server Settings
    host: str = "0.0.0.0"
    port: int = 8000
    
    class Config:
        env_file = ".env"
        case_sensitive = False
    
    @property
    def groq_api_keys_list(self) -> List[str]:
        """Parse comma-separated API keys"""
        return [key.strip() for key in self.groq_api_keys.split(",") if key.strip()]


# Create global settings instance
settings = Settings()

