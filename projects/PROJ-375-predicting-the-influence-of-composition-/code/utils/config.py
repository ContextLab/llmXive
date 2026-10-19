"""
Utility module for configuration handling.

Provides a simple wrapper to fetch environment variables with optional default values.
"""

import os
from typing import Optional


def get_env_var(name: str, default: Optional[str] = None) -> Optional[str]:
    """
    Retrieve the value of an environment variable.

    Args:
        name: Name of the environment variable.
        default: Value to return if the variable is not set. Defaults to None.

    Returns:
        The environment variable value as a string, or the default if not set.
    """
    return os.getenv(name, default)
