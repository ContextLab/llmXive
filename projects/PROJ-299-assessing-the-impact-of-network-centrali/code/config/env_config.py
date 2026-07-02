"""
Environment configuration management for the llmXive ADNI project.

This module handles loading, validating, and accessing environment variables,
specifically ADNI credentials and project paths.
"""
import os
from pathlib import Path
from typing import Optional, Dict, Any
from dotenv import load_dotenv
from dotenv.main import DotEnv


# Define the project root relative to this file (assuming code/config/env_config.py)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
ENV_FILE_PATH = PROJECT_ROOT / ".env"


def load_environment() -> bool:
    """
    Loads the .env file from the project root if it exists.

    Returns:
        bool: True if the file was loaded successfully or already loaded, False if not found.
    """
    if ENV_FILE_PATH.exists():
        load_dotenv(dotenv_path=ENV_FILE_PATH)
        return True
    return False


def validate_adni_credentials() -> Dict[str, Any]:
    """
    Validates the presence of required ADNI credentials in the environment.

    Required keys:
        - ADNI_USER: ADNI portal username
        - ADNI_PASS: ADNI portal password
        - ADNI_PROJECT_ID: (Optional but recommended) Project ID if applicable

    Returns:
        Dict[str, Any]: A dictionary containing the validated credentials if successful.

    Raises:
        ValueError: If any required credential is missing or empty.
    """
    required_keys = ["ADNI_USER", "ADNI_PASS"]
    missing_keys = []

    for key in required_keys:
        value = os.getenv(key)
        if not value:
            missing_keys.append(key)

    if missing_keys:
        raise ValueError(
            f"Missing required ADNI credentials in environment or .env file: {', '.join(missing_keys)}. "
            f"Please ensure {ENV_FILE_PATH} exists and contains these keys."
        )

    return {
        "user": os.getenv("ADNI_USER"),
        "password": os.getenv("ADNI_PASS"),
        "project_id": os.getenv("ADNI_PROJECT_ID"),
    }


def get_config() -> Dict[str, Any]:
    """
    Loads environment variables and validates ADNI credentials.

    Returns:
        Dict[str, Any]: A dictionary containing configuration including credentials.
    """
    load_environment()
    return validate_adni_credentials()


# Convenience function for CLI usage or direct script execution
def check_env() -> None:
    """
    Checks the environment and prints the status.
    Raises ValueError if validation fails.
    """
    try:
        creds = get_config()
        print("Environment configuration valid.")
        print(f"ADNI User: {creds['user']}")
        # Mask password for security
        print(f"ADNI Password: {'*' * len(creds['password'])}")
        if creds['project_id']:
            print(f"Project ID: {creds['project_id']}")
    except ValueError as e:
        print(f"Configuration Error: {e}")
        raise


if __name__ == "__main__":
    check_env()
