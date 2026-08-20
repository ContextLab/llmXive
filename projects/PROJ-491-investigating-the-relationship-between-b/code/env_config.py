"""
Environment configuration management for OpenNeuro credentials.

This module handles the loading, validation, and retrieval of OpenNeuro
API credentials from environment variables or a .env file.
"""
import os
from pathlib import Path
from typing import Optional, Dict, Any
from dotenv import load_dotenv
from config import ensure_directories


class OpenNeuroConfig:
    """Configuration holder for OpenNeuro access credentials."""

    def __init__(self, api_key: str, anonymous_access: bool = False):
        """
        Initialize the OpenNeuro configuration.

        Args:
            api_key: The OpenNeuro API key for authenticated access.
            anonymous_access: If True, allow anonymous downloads (some datasets require auth).
        """
        if not api_key:
            raise ValueError("OpenNeuro API key cannot be empty.")
        
        self.api_key = api_key
        self.anonymous_access = anonymous_access
        self.base_url = "https://openneuro.org"
        self.graphql_endpoint = f"{self.base_url}/crn/graphql"

    def get_headers(self) -> Dict[str, str]:
        """Return headers required for authenticated requests."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        return headers

    @classmethod
    def from_env(cls, env_file: Optional[Path] = None) -> "OpenNeuroConfig":
        """
        Load configuration from environment variables.

        Args:
            env_file: Optional path to a .env file. If None, searches in current dir.

        Returns:
            OpenNeuroConfig instance.

        Raises:
            ValueError: If required environment variables are missing.
        """
        if env_file and env_file.exists():
            load_dotenv(env_file)
        else:
            load_dotenv()

        api_key = os.getenv("OPENNEURO_API_KEY")
        
        if not api_key:
            raise ValueError(
                "OPENNEURO_API_KEY environment variable is not set. "
                "Please set it in your environment or create a .env file."
            )

        # Optional: Check for anonymous access flag if needed
        anonymous_str = os.getenv("OPENNEURO_ANONYMOUS", "false").lower()
        anonymous_access = anonymous_str == "true"

        return cls(api_key=api_key, anonymous_access=anonymous_access)


def get_openneuro_config(env_file: Optional[Path] = None) -> OpenNeuroConfig:
    """
    Factory function to retrieve the OpenNeuro configuration.

    This is the primary entry point for other modules to access credentials.
    It ensures the .env file exists (if provided) and loads the config.

    Args:
        env_file: Path to the .env file. Defaults to looking in the project root.

    Returns:
        OpenNeuroConfig object.

    Raises:
        ValueError: If credentials are missing or invalid.
    """
    if env_file is None:
        env_file = Path.cwd() / ".env"
    
    # Ensure the .env file exists? No, we just try to load.
    # If it doesn't exist, load_dotenv does nothing, and we rely on OS env vars.
    
    return OpenNeuroConfig.from_env(env_file=env_file)


def main():
    """
    CLI entry point to validate and print configuration status.
    Used for manual verification of the setup.
    """
    ensure_directories()
    
    try:
        config = get_openneuro_config()
        print("OpenNeuro configuration loaded successfully.")
        print(f"  Base URL: {config.base_url}")
        print(f"  API Key: {config.api_key[:4]}...{config.api_key[-4:]}")
        print(f"  Anonymous Access: {config.anonymous_access}")
        return 0
    except ValueError as e:
        print(f"Configuration Error: {e}")
        return 1
    except Exception as e:
        print(f"Unexpected error: {e}")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
