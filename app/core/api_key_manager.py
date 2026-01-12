"""
Groq API Key Manager with automatic failover on rate limits
"""
from datetime import datetime, timedelta
from typing import Optional, List
from app.core.logging import get_logger


logger = get_logger(__name__)


class GroqAPIKeyManager:
    """Manages multiple Groq API keys with automatic failover on rate limits"""
    
    def __init__(self, api_keys: List[str], cooldown_minutes: int = 5):
        """
        Initialize the API key manager
        
        Args:
            api_keys: List of Groq API keys
            cooldown_minutes: Cooldown period for failed keys
        """
        self.api_keys = api_keys
        self.current_key_index = 0
        self.failed_keys = {}  # Track failed keys with timestamp
        self.cooldown_minutes = cooldown_minutes
        
        if not self.api_keys:
            logger.warning("No GROQ_API_KEYS found in environment variables")
        else:
            logger.info(f"Initialized GroqAPIKeyManager with {len(self.api_keys)} API keys")
    
    def get_available_key(self) -> Optional[str]:
        """Get an available API key, skipping those in cooldown"""
        now = datetime.now()
        
        # Clean up expired cooldowns
        self.failed_keys = {
            key: timestamp 
            for key, timestamp in self.failed_keys.items()
            if now - timestamp < timedelta(minutes=self.cooldown_minutes)
        }
        
        # Find an available key
        for _ in range(len(self.api_keys)):
            key = self.api_keys[self.current_key_index]
            
            if key not in self.failed_keys:
                return key
            
            # Move to next key
            self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
        
        # If all keys are in cooldown, return the least recently failed
        if self.api_keys:
            logger.warning("All API keys are in cooldown, using least recently failed")
            return self.api_keys[self.current_key_index]
        
        return None
    
    def mark_key_failed(self, api_key: str):
        """Mark a key as failed (rate limited or quota exceeded)"""
        self.failed_keys[api_key] = datetime.now()
        logger.warning(f"Marked API key as failed: {api_key[:10]}... (cooldown: {self.cooldown_minutes}m)")
        
        # Move to next key
        self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
    
    def rotate_to_next_key(self):
        """Manually rotate to the next key"""
        if len(self.api_keys) > 1:
            self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
            logger.info(f"Rotated to next API key (index: {self.current_key_index})")
    
    def get_status(self) -> dict:
        """Get the status of all API keys"""
        return {
            "total_keys": len(self.api_keys),
            "current_key_index": self.current_key_index,
            "failed_keys_count": len(self.failed_keys),
            "cooldown_minutes": self.cooldown_minutes,
            "has_available_keys": self.get_available_key() is not None
        }

