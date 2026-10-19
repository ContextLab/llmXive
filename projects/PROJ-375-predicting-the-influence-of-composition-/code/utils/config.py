"""
Configuration utilities for the project.
Provides helper functions to access environment variables.
"""

import os
from typing import Optional


def get_env_var(name: str, default: Optional[str] = None) -> Optional[str]:
    """
    Retrieve an environment variable value.

    Args:
        name: Name of the environment variable.
        default: Value to return if the variable is not set. If omitted,
                 None is returned.

    Returns:
        The string value of the environment variable, or ``default`` if it
        is not set.
    """
    return os.getenv(name, default)
