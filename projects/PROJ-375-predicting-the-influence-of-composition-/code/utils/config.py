"""
Utility module for configuration helpers.

Currently provides a simple wrapper to fetch environment variables.
"""

import os
from typing import Optional


def get_env_var(name: str) -> Optional[str]:
    """
    Retrieve the value of an environment variable.

    Returns ``None`` if the variable is not set. The caller can decide
    whether to raise an error or use a default.
    """
    return os.getenv(name)
