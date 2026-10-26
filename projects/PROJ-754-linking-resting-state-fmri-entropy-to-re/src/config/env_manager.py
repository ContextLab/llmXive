"""
Wrapper around the real environment‑manager implementation.

The original implementation lives in ``code.src.config.env_manager``.  This module
simply re‑exports the public symbols so that imports such as
``from src.config.env_manager import get_hcp_token`` continue to work.
"""

from code.src.config.env_manager import (
    EnvironmentError,
    get_project_root,
    get_hcp_token,
    validate_hcp_credentials,
    get_optional_env,
    check_environment,
    main,
)

__all__ = [
    "EnvironmentError",
    "get_project_root",
    "get_hcp_token",
    "validate_hcp_credentials",
    "get_optional_env",
    "check_environment",
    "main",
]
