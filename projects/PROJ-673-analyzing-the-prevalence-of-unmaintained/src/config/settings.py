"""
Environment configuration management for the NPM dependency analysis pipeline.

This module handles loading configuration from environment variables and
provides default values for API keys, tokens, and rate limits.
"""

import os
from typing import Optional


class Config:
    """
    Configuration class holding all environment-dependent settings.

    Attributes:
        npm_api_key: API key for NPM registry access (default: empty string)
        github_token: GitHub token for repository metadata access (default: empty string)
        rate_limit: Maximum requests per minute for API calls (default: 60)
    """

    def __init__(
        self,
        npm_api_key: Optional[str] = None,
        github_token: Optional[str] = None,
        rate_limit: Optional[int] = None,
    ):
        """
        Initialize configuration from environment variables or provided values.

        Args:
            npm_api_key: NPM API key. If None, reads from NPM_API_KEY env var.
            github_token: GitHub token. If None, reads from GITHUB_TOKEN env var.
            rate_limit: Rate limit (requests/min). If None, reads from RATE_LIMIT env var.
        """
        self.npm_api_key = npm_api_key or os.getenv("NPM_API_KEY", "")
        self.github_token = github_token or os.getenv("GITHUB_TOKEN", "")
        
        # Default rate limit is 60 requests per minute
        env_rate_limit = os.getenv("RATE_LIMIT")
        if rate_limit is not None:
            self.rate_limit = rate_limit
        elif env_rate_limit:
            try:
                self.rate_limit = int(env_rate_limit)
            except ValueError:
                self.rate_limit = 60
        else:
            self.rate_limit = 60

    def is_valid(self) -> bool:
        """
        Check if the configuration has valid API credentials.

        Note: Empty API keys are allowed but may cause API calls to fail
        depending on the service requirements.
        """
        return True  # Configuration is always structurally valid

    def __repr__(self) -> str:
        return (
            f"Config(npm_api_key={'***' if self.npm_api_key else 'None'}, "
            f"github_token={'***' if self.github_token else 'None'}, "
            f"rate_limit={self.rate_limit})"
        )


# Global configuration instance (lazy initialization)
_config_instance: Optional[Config] = None


def get_config() -> Config:
    """
    Get the global configuration instance.

    Returns:
        Config: The singleton configuration instance.
    
    Example:
        >>> cfg = get_config()
        >>> print(cfg.rate_limit)
        60
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = Config()
    return _config_instance


def reset_config() -> None:
    """
    Reset the global configuration instance.
    
    Useful for testing or re-loading configuration from environment.
    """
    global _config_instance
    _config_instance = None


# Default values for documentation/reference
DEFAULT_RATE_LIMIT = 60  # requests per minute
DEFAULT_NPM_API_KEY = ""  # NPM public API often doesn't require a key
DEFAULT_GITHUB_TOKEN = ""  # Optional for public repositories, required for rate limit increase