"""
env_manager.py
---------------
Utilities for checking and retrieving required environment variables.
The module is deliberately lightweight and raises a custom
``EnvironmentError`` (defined here) for any problem with the
``HCP_TOKEN`` credential.
"""
import os
import sys
from pathlib import Path
from typing import Optional, Dict

class EnvironmentError(RuntimeError):
    """Custom exception raised when required environment variables are missing
    or malformed."""
    pass

def get_project_root() -> Path:
    """
    Return the absolute path to the project root.

    The project root is assumed to be two directories up from this file,
    i.e. ``code/config`` -> ``code`` -> project root.
    """
    return Path(__file__).resolve().parents[2]

def get_hcp_token() -> str:
    """
    Retrieve the HCP_TOKEN environment variable.

    Raises
    ------
    EnvironmentError
        If the variable is missing, empty, or contains only whitespace.
    """
    token = os.getenv("HCP_TOKEN")
    if token is None:
        raise EnvironmentError("HCP_TOKEN is not set in the environment.")
    if not token.strip():
        raise EnvironmentError("HCP_TOKEN is required but is empty or whitespace.")
    return token

def validate_hcp_credentials() -> bool:
    """
    Validate that HCP credentials are present and meet a minimal length
    requirement.

    Returns
    -------
    bool
        ``True`` if validation succeeds.

    Raises
    ------
    EnvironmentError
        If the token is missing, empty, whitespace, or shorter than 10
        characters (arbitrary safety threshold).
    """
    token = get_hcp_token()
    if len(token.strip()) < 10:
        raise EnvironmentError(
            f"HCP_TOKEN appears too short (len={len(token)}). "
            "It must be at least 10 characters long."
        )
    return True

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
    errors = []
    root = get_project_root()
    token_set = True
    try:
        _ = get_hcp_token()
    except EnvironmentError as exc:
        token_set = False
        errors.append(str(exc))

    return {
        "project_root": root,
        "hcp_token_set": token_set,
        "errors": errors,
    }

def main() -> None:
    """
    CLI entry point. Prints a short status message and exits with
    ``0`` on success or ``1`` on failure.
    """
    status = check_environment()
    if status["errors"]:
        print("Errors encountered during environment check:")
        for err in status["errors"]:
            print(f" - {err}")
        sys.exit(1)
    else:
        print("Environment check passed. All required variables are set.")
        sys.exit(0)
