"""
API Key authentication module.
"""
import os
from typing import Optional


def get_api_key() -> str:
    """Get the valid API key from environment."""
    return os.environ.get("API_KEY", "sk_test_123456789")


def validate_api_key(api_key: Optional[str]) -> bool:
    """
    Validate the provided API key against stored key.
    
    Args:
        api_key: The API key from request header
        
    Returns:
        True if valid, False otherwise
    """
    if not api_key:
        return False
    
    valid_key = get_api_key()
    return api_key == valid_key
