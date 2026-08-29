"""
Configuration management for the LLM Refactoring Research project.
"""
import os
import secrets
from typing import Optional
from pydantic import BaseSettings, Field, validator

class Config(BaseSettings):
    """Application configuration loaded from environment variables."""
    
    HF_API_KEY: str = Field(
        default="",
        description="HuggingFace API key for model inference and dataset access."
    )
    RANDOM_SEED: int = Field(
        default=42,
        description="Random seed for reproducibility."
    )
    MAX_ATTEMPTS: int = Field(
        default=400,
        description="Maximum number of attempts to fetch valid data samples."
    )
    MIN_VALID_FUNCTIONS: int = Field(
        default=100,
        description="Minimum number of valid function samples required."
    )
    BATCH_SIZE: int = Field(
        default=10,
        description="Batch size for LLM inference requests."
    )
    
    class Config:
        env_file = ".env"
        case_sensitive = True

    @validator('HF_API_KEY')
    def validate_api_key(cls, v):
        if not v:
            raise ValueError("HF_API_KEY must be set in environment variables.")
        return v

def get_secret(key: str, default: Optional[str] = None) -> str:
    """
    Retrieve a secret value from environment variables.
    
    Args:
        key: The environment variable name.
        default: Default value if key is not found.
        
    Returns:
        The value of the environment variable.
        
    Raises:
        ValueError: If the key is required but not set.
    """
    value = os.getenv(key, default)
    if value is None:
        # Check if this is a critical secret (simple heuristic)
        if key.endswith("_KEY") or key.endswith("_SECRET"):
            raise ValueError(f"Required secret {key} is not set.")
    return value
