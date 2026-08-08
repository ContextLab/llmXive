"""
Configuration management for the LLM Refactoring Research pipeline.
Defines environment variables and default constants with type validation.
"""
import os
import secrets
from typing import Optional

from pydantic import BaseSettings, Field, validator


class Config(BaseSettings):
    """
    Main configuration class for the project.
    Loads values from environment variables or uses defaults.
    """
    # HF API Key
    HF_API_KEY: str = Field(
        default="",
        description="Hugging Face API key for dataset and model access"
    )

    # Random Seed for reproducibility
    RANDOM_SEED: int = Field(
        default=42,
        ge=0,
        description="Random seed for all random operations"
    )

    # Execution Limits
    MAX_ATTEMPTS: int = Field(
        default=400,
        gt=0,
        description="Maximum number of attempts to fetch valid samples"
    )

    MIN_VALID_FUNCTIONS: int = Field(
        default=100,
        gt=0,
        description="Minimum number of valid functions required to proceed"
    )

    BATCH_SIZE: int = Field(
        default=10,
        ge=1,
        le=50,
        description="Batch size for LLM API calls"
    )

    # Timeouts
    API_TIMEOUT: int = Field(
        default=60,
        gt=0,
        description="Timeout in seconds for API calls"
    )

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"

    @validator('HF_API_KEY')
    def validate_api_key(cls, v):
        if not v:
            # Check if it's set in the environment directly (fallback for CI)
            env_key = os.getenv("HF_API_KEY")
            if env_key:
                return env_key
            raise ValueError(
                "HF_API_KEY must be set via environment variable or .env file. "
                "Set it to your Hugging Face token to proceed."
            )
        return v


# Singleton instance for easy access
config = Config()

# Helper to load secrets securely
def get_secret(key: str, default: Optional[str] = None) -> str:
    """
    Retrieve a secret value from environment variables.
    Uses secrets module for secure handling if needed, but primarily
    relies on OS environment variables for production safety.
    """
    val = os.getenv(key, default)
    if val is None:
        raise ValueError(f"Required secret {key} is not set in environment.")
    return val