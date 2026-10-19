"""
Utility module for configuration handling.
Provides a simple wrapper to retrieve environment variables.
"""
import os
from typing import Optional

def get_env_var(name: str, default: Optional[str] = None) -> Optional[str]:
    """
    Retrieve an environment variable value.

    Args:
        name: The name of the environment variable.
        default: Value to return if the variable is not set. If not provided,
                 None is returned.

    Returns:
        The value of the environment variable, or ``default`` if it is not set.
    """
    return os.getenv(name, default)
