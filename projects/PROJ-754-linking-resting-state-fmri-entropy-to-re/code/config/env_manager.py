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
    Assumes the project structure is: code/config/env_manager.py
    So root is two levels up from this file.
    """
    current_file = Path(__file__).resolve()
    # Assuming structure: <root>/code/config/env_manager.py
    project_root = current_file.parent.parent.parent
    return project_root


def get_hcp_token() -> str:
    """
    Retrieve the HCP_TOKEN from environment variables.

    Returns:
        str: The HCP token value.

    Raises:
        ValueError: If HCP_TOKEN is missing or empty.
    """
    token = os.getenv("HCP_TOKEN")
    if not token:
        raise ValueError("HCP_TOKEN is required but not found in environment variables.")
    return token


def validate_hcp_credentials() -> bool:
    """
    Validate that HCP credentials are present and non-empty.

    Returns:
        bool: True if valid, raises ValueError if invalid.

    Raises:
        ValueError: If HCP_TOKEN is missing or invalid.
    """
    try:
        token = get_hcp_token()
        # Basic validation: token should not be empty or just whitespace
        if not token or not token.strip():
            raise ValueError("HCP_TOKEN is required but not found in environment variables.")
        return True
    except ValueError:
        raise


def get_optional_env(var_name: str, default: Optional[str] = None) -> Optional[str]:
    """
    Retrieve an optional environment variable.

    Args:
        var_name: Name of the environment variable.
        default: Default value if the variable is not set.

    Returns:
        Optional[str]: The value of the environment variable or the default.
    """
    return os.getenv(var_name, default)


def check_environment() -> None:
    """
    Perform a comprehensive check of the required environment variables.

    Raises:
        EnvironmentError: If any required environment variable is missing or invalid.
    """
    try:
        validate_hcp_credentials()
        # Future checks for other required variables can be added here
    except ValueError as e:
        raise EnvironmentError(str(e)) from e


def main() -> None:
    """
    Main entry point for command-line execution of environment checks.
    """
    print("Checking environment configuration...")
    try:
        check_environment()
        print("✓ Environment configuration is valid.")
        print(f"  HCP_TOKEN present: Yes (length: {len(get_hcp_token())} chars)")
    except EnvironmentError as e:
        print(f"✗ Environment configuration error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()