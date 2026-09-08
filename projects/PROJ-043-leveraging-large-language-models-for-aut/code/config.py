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
    TARGET_VALID_FUNCTIONS: int = Field(
        default=200,
        description="Target number of valid function samples to fetch."
    )
    BATCH_SIZE: int = Field(
        default=10,
        description="Batch size for LLM inference requests."
    )
    BASELINE_TOLERANCE: float = Field(
        default=0.01,
        description="Tolerance threshold for checking identity baseline deltas."
    )
    
    class Config:
        env_file = ".env"
        case_sensitive = True

    @validator('HF_API_KEY')
    def validate_api_key(cls, v):
        # Allow empty string during development/testing if explicitly set to empty
        # but in production, it should be provided. We raise only if it's None or missing.
        # However, for strict enforcement as per task requirements, we ensure it's a string.
        if not v:
            # If the key is explicitly set to an empty string in .env, we might want to warn
            # but the task requires validation. We'll allow it to pass if it's just empty string
            # but typically a validator raises if it's invalid.
            # To be safe and consistent with "fail loudly", we raise if it's effectively missing.
            # But the task says "Define variables... with default values and type validation".
            # We'll keep the logic: if it's empty, we might raise or warn. 
            # Given the existing code raised ValueError, we keep it but note that empty string is a valid str.
            # Let's refine: if it's an empty string, we raise because it's not a usable key.
            raise ValueError("HF_API_KEY must be set in environment variables and cannot be empty.")
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