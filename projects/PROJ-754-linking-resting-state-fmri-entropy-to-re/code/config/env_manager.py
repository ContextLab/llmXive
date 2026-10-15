"""
env_manager.py
----------------
Utility functions for managing required environment variables and project
configuration. Provides clear error messages and a simple CLI for checking
the environment before running the pipeline.
"""
import os
import sys
from pathlib import Path
from typing import Optional, Dict, List

# ----------------------------------------------------------------------
# Custom exception type used throughout the project
# ----------------------------------------------------------------------
class EnvironmentError(Exception):
    """Raised when a required environment variable is missing or invalid."""
    pass

# ----------------------------------------------------------------------
# Helper: locate the project root (directory that contains the top‑level
# ``code`` folder or a ``.git`` directory).  This function walks up the
# directory hierarchy from this file until it finds one of the markers.
# ----------------------------------------------------------------------
def get_project_root() -> Path:
    """Return the absolute path to the project root."""
    current = Path(__file__).resolve()
    # Walk up until we find a directory containing a ``code`` folder
    # or a ``.git`` directory.
    for parent in [current] + list(current.parents):
        if (parent / "code").is_dir() or (parent / ".git").is_dir():
            return parent
    # Fallback: two levels up (as originally documented)
    return current.parent.parent

# ----------------------------------------------------------------------
# Helper: retrieve the HCP token from the environment.
# ----------------------------------------------------------------------
def get_hcp_token() -> str:
    """
    Retrieve the HCP_TOKEN environment variable.

    Returns
    -------
    str
        The token string.

    Raises
    ------
    EnvironmentError
        If the variable is missing, empty, or contains only whitespace.
    """
    token = os.getenv("HCP_TOKEN")
    if token is None:
        raise EnvironmentError("HCP_TOKEN is required but not set.")
    token = token.strip()
    if not token:
        raise EnvironmentError("HCP_TOKEN is required but is empty or whitespace.")
    return token

# ----------------------------------------------------------------------
# Validate that the token looks plausible.  The HCP token is a long
# alphanumeric string; we enforce a minimum length of 10 characters.
# ----------------------------------------------------------------------
def validate_hcp_credentials() -> bool:
    """
    Validate that HCP credentials are present and non‑empty.

    Returns
    -------
    bool
        True if validation succeeds.

    Raises
    ------
    EnvironmentError
        If the token is missing, empty, or too short.
    """
    token = get_hcp_token()
    if len(token) < 10:
        raise EnvironmentError(
            f"HCP_TOKEN appears to be too short (length {len(token)})."
        )
    return True

# ----------------------------------------------------------------------
# Generic optional environment variable accessor.
# ----------------------------------------------------------------------
def get_optional_env(var_name: str, default: Optional[str] = None) -> Optional[str]:
    """
    Retrieve an optional environment variable.

    Parameters
    ----------
    var_name : str
        Name of the environment variable.
    default : Optional[str], optional
        Value to return if the variable is not set.

    Returns
    -------
    Optional[str]
        The variable's value or ``default`` if not set.
    """
    return os.getenv(var_name, default)

# ----------------------------------------------------------------------
# Comprehensive check that returns a dictionary describing the status.
# ----------------------------------------------------------------------
def check_environment() -> Dict[str, object]:
    """
    Perform a comprehensive check of required environment variables.

    Returns
    -------
    dict
        ``{
            "project_root": Path,
            "hcp_token_set": bool,
            "errors": list[str]
         }``
    """
    errors: List[str] = []
    root = get_project_root()
    token_set = False
    try:
        validate_hcp_credentials()
        token_set = True
    except EnvironmentError as exc:
        errors.append(str(exc))

    return {
        "project_root": root,
        "hcp_token_set": token_set,
        "errors": errors,
    }

# ----------------------------------------------------------------------
# CLI entry point used by the test suite.
# ----------------------------------------------------------------------
def main() -> None:
    """
    CLI entry point.  Prints a short status message and exits with
    ``0`` on success or ``1`` on failure.
    """
    status = check_environment()
    if not status["errors"]:
        print("Environment check passed")
        sys.exit(0)
    else:
        print("Errors encountered:")
        for err in status["errors"]:
            print(f"- {err}")
        sys.exit(1)
