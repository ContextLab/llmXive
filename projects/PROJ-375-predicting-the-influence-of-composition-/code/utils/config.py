"""
Utility module for configuration handling.

Provides a simple helper to fetch environment variables.
"""

import os
from typing import Optional


def get_env_var(var_name: str, default: Optional[str] = None) -> Optional[str]:
    """
    Retrieve an environment variable.

    Args:
        var_name: Name of the environment variable.
        default: Value to return if the variable is not set.

    Returns:
        The value of the environment variable, or ``default`` if it is not set.
    """
    return os.getenv(var_name, default)
