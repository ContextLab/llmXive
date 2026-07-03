"""
Configuration management for the llmXive research pipeline.

This module handles API keys, rate limiting constants, and research
parameters required for GitHub API interactions and data analysis.
"""

import os
from typing import Optional


def _get_env_int(key: str, default: int) -> int:
    """Retrieve an integer from the environment or return default."""
    value = os.getenv(key)
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


def _get_env_str(key: str, default: Optional[str] = None) -> Optional[str]:
    """Retrieve a string from the environment or return default."""
    value = os.getenv(key)
    return value if value is not None else default


# GitHub API Configuration
GITHUB_TOKEN: str = _get_env_str("GITHUB_TOKEN", "")

# Rate Limiting (FR-007)
RATE_LIMIT_HOURLY: int = _get_env_int("RATE_LIMIT_HOURLY", 5000)
BACKOFF_INITIAL: int = _get_env_int("BACKOFF_INITIAL", 1)
BACKOFF_MAX: int = _get_env_int("BACKOFF_MAX", 60)

# Research Parameters
STRATIFICATION_SEED: int = _get_env_int("STRATIFICATION_SEED", 42)
MAX_REVIEW_DAYS: int = _get_env_int("MAX_REVIEW_DAYS", 30)

# Derived constants (not in schema but useful for downstream code)
BACKOFF_MULTIPLIER: float = 2.0