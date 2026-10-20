"""
Utility module for configuration handling.

Provides a simple helper to retrieve environment variables required by the
pipeline. If the variable is not set, a clear RuntimeError is raised so
that the pipeline aborts loudly, satisfying the “no synthetic fallback”
requirement.
"""

import os
from typing import Optional

def get_env_var(name: str, default: Optional[str] = None) -> str:
    """
    Retrieve the value of an environment variable.

    Args:
        name: Name of the environment variable.
        default: Optional default value to return if the variable is not set.
                 If not provided, a RuntimeError is raised.

    Returns:
        The value of the environment variable.

    Raises:
        RuntimeError: If the variable is not set and no default is supplied.
    """
    value = os.getenv(name, default)
    if value is None:
        raise RuntimeError(f"Required environment variable '{name}' is not set.")
    return value
