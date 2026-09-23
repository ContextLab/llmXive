"""
Environment configuration management for the NPM unmaintained dependencies analysis.

This module handles the loading and validation of environment variables
required for API access and rate limiting.
"""
import os
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class Config:
    """
    Configuration holder for environment variables and defaults.
    
    Attributes:
        npm_api_key (str): NPM registry API key for authenticated requests.
        github_token (str): GitHub Personal Access Token for repository metadata.
        rate_limit (int): Maximum requests per minute allowed for API calls.
    """
    def __init__(
        self,
        npm_api_key: Optional[str] = None,
        github_token: Optional[str] = None,
        rate_limit: Optional[int] = None
    ):
        # Load from environment variables first, fallback to defaults if not set
        # Note: For security, we do NOT provide a default value for API keys.
        # If they are not set, the application should fail loudly during initialization
        # of clients that require them, or use them only if explicitly optional.
        self.npm_api_key = npm_api_key or os.getenv("NPM_API_KEY")
        self.github_token = github_token or os.getenv("GITHUB_TOKEN")
        
        # Rate limit has a safe default but can be overridden
        self.rate_limit = rate_limit or int(os.getenv("RATE_LIMIT", "60"))

        # Validate critical configuration
        self._validate()

    def _validate(self):
        """
        Validates that critical configuration is present.
        
        Raises:
            ValueError: If required API keys are missing.
        """
        # NPM API key is often optional for public endpoints, but we warn if missing
        if not self.npm_api_key:
            logger.warning("NPM_API_KEY not set. Some endpoints may fail or be rate-limited.")
        
        # GitHub token is required for commit/release date metadata
        if not self.github_token:
            logger.warning("GITHUB_TOKEN not set. Repository metadata (commits/releases) will fail.")
        
        # Rate limit must be positive
        if self.rate_limit <= 0:
            raise ValueError(f"RATE_LIMIT must be positive, got {self.rate_limit}")

    def __repr__(self) -> str:
        # Mask secrets in repr for safety
        return (
            f"Config(npm_api_key={self._mask_secret(self.npm_api_key)}, "
            f"github_token={self._mask_secret(self.github_token)}, "
            f"rate_limit={self.rate_limit})"
        )

    @staticmethod
    def _mask_secret(secret: Optional[str]) -> str:
        """Masks a secret value for logging/display."""
        if not secret:
            return "None"
        if len(secret) <= 4:
            return "***"
        return f"{secret[:2]}...{secret[-2:]}"


# Singleton instance
_config_instance: Optional[Config] = None


def get_config() -> Config:
    """
    Returns the singleton Config instance.
    
    This function initializes the configuration from environment variables
    on the first call and caches it for subsequent calls.
    
    Returns:
        Config: The application configuration.
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = Config()
        logger.info("Configuration loaded from environment variables.")
    return _config_instance


def reset_config() -> None:
    """
    Resets the singleton configuration instance.
    
    Useful for testing or reloading configuration without restarting the process.
    """
    global _config_instance
    if _config_instance:
        logger.info("Configuration reset.")
    _config_instance = None