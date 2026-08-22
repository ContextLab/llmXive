"""
Environment configuration management for OpenNeuro credentials.

This module handles the secure loading and validation of OpenNeuro API
credentials from environment variables or a .env file. It ensures that
the pipeline can access the OpenNeuro dataset API without hardcoding secrets.
"""
import os
from pathlib import Path
from typing import Optional, Dict, Any

from dotenv import load_dotenv
from config import ensure_directories

# Constants for environment variable names
OPENNEURO_API_KEY_ENV = "OPENNEURO_API_KEY"
OPENNEURO_BASE_URL_ENV = "OPENNEURO_BASE_URL"
DEFAULT_OPENNEURO_BASE_URL = "https://openneuro.org"
DOTENV_FILE = ".env"


class OpenNeuroConfig:
    """
    Configuration container for OpenNeuro access credentials.

    Attributes:
        api_key (str): The API key for OpenNeuro access.
        base_url (str): The base URL for the OpenNeuro API.
    """

    def __init__(self, api_key: str, base_url: str = DEFAULT_OPENNEURO_BASE_URL):
        if not api_key:
            raise ValueError("OpenNeuro API key cannot be empty.")
        self.api_key = api_key
        self.base_url = base_url

    @property
    def headers(self) -> Dict[str, str]:
        """Returns the standard headers for authenticated requests."""
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

    def __repr__(self) -> str:
        # Mask the API key for safe logging
        masked_key = self.api_key[:4] + "..." + self.api_key[-4:] if len(self.api_key) > 8 else "***"
        return f"OpenNeuroConfig(api_key={masked_key}, base_url={self.base_url})"


def get_openneuro_config() -> Optional[OpenNeuroConfig]:
    """
    Loads and validates OpenNeuro configuration from environment variables.

    Attempts to load variables from a .env file in the project root first,
    then falls back to the system environment.

    Returns:
        OpenNeuroConfig: The validated configuration object.

    Raises:
        ValueError: If the required API key is missing.
    """
    # Ensure .env file is loaded if it exists
    project_root = Path(__file__).parent.parent
    env_path = project_root / DOTENV_FILE
    if env_path.exists():
        load_dotenv(env_path)

    api_key = os.getenv(OPENNEURO_API_KEY_ENV)
    base_url = os.getenv(OPENNEURO_BASE_URL_ENV, DEFAULT_OPENNEURO_BASE_URL)

    if not api_key:
        raise ValueError(
            f"OpenNeuro API key not found. Please set the {OPENNEURO_API_KEY_ENV} "
            f"environment variable or add it to a {DOTENV_FILE} file in the project root."
        )

    return OpenNeuroConfig(api_key=api_key, base_url=base_url)


def main():
    """
    CLI entry point to test the environment configuration loading.
    """
    ensure_directories()
    try:
        config = get_openneuro_config()
        print(f"Successfully loaded OpenNeuro configuration: {config}")
        return 0
    except ValueError as e:
        print(f"Configuration Error: {e}")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
