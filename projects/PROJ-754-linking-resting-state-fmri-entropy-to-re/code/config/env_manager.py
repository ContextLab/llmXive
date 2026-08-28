"""
Environment variable management for the llmXive science pipeline.

Handles HCP_TOKEN validation, project root discovery, and graceful failure
on missing credentials.
"""
import os
import sys
from pathlib import Path
from typing import Optional


class EnvironmentError(Exception):
    """Custom exception for environment configuration errors."""
    pass


def get_project_root() -> Path:
    """
    Determine the project root directory.
    
    Looks for a .git directory or a specific marker file (e.g., requirements.txt)
    traversing up from the current script location.
    
    Returns:
        Path: Absolute path to the project root.
    
    Raises:
        EnvironmentError: If project root cannot be determined.
    """
    current = Path(__file__).resolve()
    
    # Strategy 1: Look for .git directory
    for parent in [current, *current.parents]:
        if (parent / ".git").is_dir():
            return parent
    
    # Strategy 2: Look for requirements.txt (common in Python projects)
    for parent in [current, *current.parents]:
        if (parent / "requirements.txt").is_file():
            return parent
    
    # Strategy 3: Default to 'code' parent if running from within code/
    # This handles cases where the project root is the immediate parent of code/
    if current.name == "code":
        return current.parent
    
    raise EnvironmentError(
        "Could not determine project root. "
        "Ensure you are running from within a git repository or a directory "
        "containing 'requirements.txt'."
    )


def get_hcp_token() -> str:
    """
    Retrieve the HCP_TOKEN from environment variables.
    
    This function strictly requires the HCP_TOKEN to be present.
    If missing, it raises a clear EnvironmentError with instructions.
    
    Returns:
        str: The HCP token value.
    
    Raises:
        EnvironmentError: If HCP_TOKEN is not set.
    """
    token = os.getenv("HCP_TOKEN")
    
    if not token:
        raise EnvironmentError(
            "HCP_TOKEN environment variable is not set.\n"
            "Please set it before running the pipeline:\n"
            "  export HCP_TOKEN='your_token_here'\n"
            "Or add it to your .env file if using python-dotenv."
        )
    
    if not token.strip():
        raise EnvironmentError(
            "HCP_TOKEN environment variable is set but empty.\n"
            "Please provide a valid token."
        )
    
    return token.strip()


def validate_hcp_credentials() -> bool:
    """
    Validate that HCP credentials are present and non-empty.
    
    This is a safety check to fail fast before attempting data downloads.
    
    Returns:
        bool: True if credentials are valid.
    
    Raises:
        EnvironmentError: If credentials are missing or invalid.
    """
    try:
        token = get_hcp_token()
        # Basic length check to ensure it's not a placeholder
        if len(token) < 10:
            raise EnvironmentError(
                f"HCP_TOKEN appears too short ({len(token)} chars). "
                "Please verify your credentials."
            )
        return True
    except EnvironmentError:
        raise


def get_optional_env(key: str, default: Optional[str] = None) -> Optional[str]:
    """
    Retrieve an optional environment variable.
    
    Unlike get_hcp_token, this does not raise an error if the variable is missing.
    
    Args:
        key: The environment variable name.
        default: Default value if the variable is not set.
    
    Returns:
        The value of the environment variable or the default.
    """
    return os.getenv(key, default)


def check_environment() -> dict:
    """
    Perform a comprehensive check of the required environment state.
    
    Returns:
        dict: A dictionary containing the status of checks and any error messages.
            {
                "project_root": Path or None,
                "hcp_token_set": bool,
                "errors": list of error messages
            }
    """
    result = {
        "project_root": None,
        "hcp_token_set": False,
        "errors": []
    }
    
    # Check project root
    try:
        result["project_root"] = get_project_root()
    except EnvironmentError as e:
        result["errors"].append(f"Project root error: {str(e)}")
    
    # Check HCP token
    try:
        get_hcp_token()
        result["hcp_token_set"] = True
    except EnvironmentError as e:
        result["errors"].append(f"HCP token error: {str(e)}")
    
    return result


def main():
    """
    Command-line entry point for environment checking.
    
    Usage:
        python -m config.env_manager
    """
    print("Checking environment configuration...")
    print("-" * 40)
    
    status = check_environment()
    
    if status["project_root"]:
        print(f"✓ Project Root: {status['project_root']}")
    else:
        print("✗ Project Root: NOT FOUND")
    
    if status["hcp_token_set"]:
        # Mask the token for security in logs
        token = get_hcp_token()
        masked = f"{token[:4]}...{token[-4:]}" if len(token) > 8 else "***"
        print(f"✓ HCP Token: Set ({masked})")
    else:
        print("✗ HCP Token: MISSING")
    
    print("-" * 40)
    
    if status["errors"]:
        print("Errors encountered:")
        for error in status["errors"]:
            print(f"  - {error}")
        sys.exit(1)
    else:
        print("Environment check passed.")
        sys.exit(0)


if __name__ == "__main__":
    main()
