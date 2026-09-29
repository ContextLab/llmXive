import os
import secrets
from typing import Optional
from pydantic import BaseSettings, Field, validator

class Config(BaseSettings):
    """Configuration settings for the project."""
    
    HF_API_KEY: Optional[str] = Field(
        default=None,
        description="Hugging Face API key for model inference"
    )
    RANDOM_SEED: int = Field(
        default=42,
        description="Random seed for reproducibility"
    )
    MAX_ATTEMPTS: int = Field(
        default=400,
        description="Maximum number of attempts to fetch valid functions"
    )
    MIN_VALID_FUNCTIONS: int = Field(
        default=100,
        description="Minimum number of valid functions required"
    )
    TARGET_VALID_FUNCTIONS: int = Field(
        default=200,
        description="Target number of valid functions to fetch"
    )
    BATCH_SIZE: int = Field(
        default=10,
        description="Batch size for API requests"
    )
    BASELINE_TOLERANCE: float = Field(
        default=0.01,
        description="Tolerance for baseline delta checks"
    )

    @validator('HF_API_KEY')
    def validate_api_key(cls, v):
        if v is None:
            # Try to get from environment if not set in config
            v = os.environ.get('HF_API_KEY')
        return v

def get_secret(key: str) -> Optional[str]:
    """
    Retrieve a secret value from environment or config.
    """
    config = Config()
    if key == "HF_API_KEY":
        return config.HF_API_KEY
    return None
