"""
Environment configuration management for OpenNeuro credentials.

This module handles the loading and validation of OpenNeuro access credentials
required for data ingestion. It supports loading from environment variables
and provides a secure way to access these credentials without hardcoding them.
"""

import os
from pathlib import Path
from typing import Optional, Dict, Any
from dotenv import load_dotenv

from config import ensure_directories


class OpenNeuroConfig:
    """
    Configuration manager for OpenNeuro data access credentials.

    This class provides a centralized way to access OpenNeuro credentials
    loaded from environment variables or a .env file.
    """

    ENV_VARS = {
        'OPENNEURO_USERNAME': 'openneuro_username',
        'OPENNEURO_PASSWORD': 'openneuro_password',
        'OPENNEURO_API_KEY': 'openneuro_api_key',
    }

    def __init__(self, env_file: Optional[Path] = None):
        """
        Initialize the OpenNeuro configuration.

        Args:
            env_file: Optional path to a .env file. If None, looks for .env in the
                     project root.
        """
        ensure_directories()
        
        # Load environment variables from .env file if it exists
        if env_file is None:
            env_file = Path('.env')
        
        load_dotenv(env_file)
        
        self._credentials: Dict[str, Optional[str]] = {}
        for env_var, attr_name in self.ENV_VARS.items():
            self._credentials[attr_name] = os.getenv(env_var)

    @property
    def username(self) -> Optional[str]:
        """Get OpenNeuro username."""
        return self._credentials.get('openneuro_username')

    @property
    def password(self) -> Optional[str]:
        """Get OpenNeuro password."""
        return self._credentials.get('openneuro_password')

    @property
    def api_key(self) -> Optional[str]:
        """Get OpenNeuro API key."""
        return self._credentials.get('openneuro_api_key')

    def is_configured(self) -> bool:
        """
        Check if at least one credential is available.

        Returns:
            True if any credential is set, False otherwise.
        """
        return any(self._credentials.values())

    def validate_credentials(self) -> Dict[str, bool]:
        """
        Validate that required credentials are present.

        Returns:
            Dictionary mapping credential names to validation status.
        """
        return {
            'username': self.username is not None,
            'password': self.password is not None,
            'api_key': self.api_key is not None,
        }

    def get_credentials(self) -> Dict[str, Optional[str]]:
        """
        Get all credentials as a dictionary.

        Returns:
            Dictionary with credential names as keys and values.
        """
        return self._credentials.copy()

    def __repr__(self) -> str:
        """String representation (hides sensitive values)."""
        masked = {
            k: '***' if v else 'None' 
            for k, v in self._credentials.items()
        }
        return f"OpenNeuroConfig({masked})"


def get_openneuro_config(env_file: Optional[Path] = None) -> OpenNeuroConfig:
    """
    Factory function to get an OpenNeuroConfig instance.

    Args:
        env_file: Optional path to a .env file.

    Returns:
        Configured OpenNeuroConfig instance.
    """
    return OpenNeuroConfig(env_file)


def main():
    """
    Main function to demonstrate configuration loading.
    """
    config = get_openneuro_config()
    
    print("OpenNeuro Configuration Status:")
    print("-" * 40)
    
    if config.is_configured():
        validation = config.validate_credentials()
        for cred_name, is_valid in validation.items():
            status = "✓" if is_valid else "✗"
            print(f"{status} {cred_name.capitalize()}: {'Set' if is_valid else 'Not set'}")
        
        print(f"\nConfiguration is ready for OpenNeuro access.")
    else:
        print("No credentials found.")
        print("\nPlease set the following environment variables:")
        print("  - OPENNEURO_USERNAME")
        print("  - OPENNEURO_PASSWORD")
        print("  - OPENNEURO_API_KEY")
        print("\nOr create a .env file in the project root with:")
        print("  OPENNEURO_USERNAME=your_username")
        print("  OPENNEURO_PASSWORD=your_password")
        print("  OPENNEURO_API_KEY=your_api_key")
        
        return 1
    
    return 0


if __name__ == '__main__':
    exit(main())
