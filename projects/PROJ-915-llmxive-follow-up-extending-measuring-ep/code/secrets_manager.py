"""
Secrets management module for llmXive pipeline.
Handles loading, validation, and retrieval of API keys and sensitive configuration.
"""
import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any

from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Required secrets for the pipeline
REQUIRED_SECRETS = {
    "HF_TOKEN": "HuggingFace API token for dataset/model access",
    "PROLIFIC_API_KEY": "Prolific API key for rater recruitment",
}

# Optional secrets that may be needed for specific features
OPTIONAL_SECRETS = {
    "GOOGLE_API_KEY": "Google API key for additional services (if used)",
}

class SecretsManager:
    """
    Manages secrets loading from environment variables and .env files.
    Ensures required secrets are present before pipeline execution.
    """

    def __init__(self, env_path: Optional[Path] = None):
        """
        Initialize the secrets manager.

        Args:
            env_path: Path to .env file. If None, looks for .env in project root.
        """
        self._secrets: Dict[str, str] = {}
        self._env_path = env_path or Path.cwd() / ".env"
        self._load_secrets()

    def _load_secrets(self) -> None:
        """Load secrets from .env file and environment variables."""
        # Load from .env file if it exists
        if self._env_path.exists():
            logger.info(f"Loading secrets from {self._env_path}")
            load_dotenv(self._env_path, override=True)
        else:
            logger.warning(f"No .env file found at {self._env_path}")

        # Load all secrets from environment
        for key in list(REQUIRED_SECRETS.keys()) + list(OPTIONAL_SECRETS.keys()):
            value = os.getenv(key)
            if value:
                self._secrets[key] = value
                logger.debug(f"Loaded secret: {key}")

    def get_secret(self, key: str, required: bool = True) -> Optional[str]:
        """
        Retrieve a secret by key.

        Args:
            key: The secret key name.
            required: If True, raises ValueError if secret is missing.

        Returns:
            The secret value, or None if not found and not required.

        Raises:
            ValueError: If a required secret is missing.
        """
        if key in self._secrets:
            return self._secrets[key]

        # Try to get from environment (in case it was set after initialization)
        value = os.getenv(key)
        if value:
            self._secrets[key] = value
            return value

        if required:
            raise ValueError(f"Required secret '{key}' is missing. "
                             f"Please set it in your .env file or environment variables.")
        return None

    def validate_secrets(self) -> bool:
        """
        Validate that all required secrets are present.

        Returns:
            True if all required secrets are present, False otherwise.
        """
        missing = []
        for key, description in REQUIRED_SECRETS.items():
            if key not in self._secrets:
                missing.append(f"{key}: {description}")

        if missing:
            logger.error("Missing required secrets:")
            for item in missing:
                logger.error(f"  - {item}")
            logger.error("\nPlease add these to your .env file:")
            for key in missing:
                secret_name = key.split(":")[0]
                logger.error(f"{secret_name}=<your_value>")
            return False

        logger.info("All required secrets are present.")
        return True

    def get_hf_token(self) -> str:
        """Get the HuggingFace token."""
        return self.get_secret("HF_TOKEN", required=True)

    def get_prolific_api_key(self) -> str:
        """Get the Prolific API key."""
        return self.get_secret("PROLIFIC_API_KEY", required=True)

    def get_optional_secret(self, key: str) -> Optional[str]:
        """Get an optional secret, returning None if not present."""
        return self.get_secret(key, required=False)

    def list_available_secrets(self) -> list:
        """List all available secret keys (without values)."""
        return list(self._secrets.keys())


def load_env_file(env_path: Optional[Path] = None) -> bool:
    """
    Load environment variables from a .env file.

    Args:
        env_path: Path to .env file. If None, uses project root.

    Returns:
        True if file was loaded successfully, False otherwise.
    """
    path = env_path or Path.cwd() / ".env"
    if not path.exists():
        logger.warning(f"No .env file found at {path}")
        return False

    result = load_dotenv(path, override=True)
    logger.info(f"Loaded environment from {path}: {result}")
    return result


def get_secret(key: str, required: bool = True) -> Optional[str]:
    """
    Convenience function to get a secret directly.

    Args:
        key: The secret key name.
        required: If True, raises ValueError if secret is missing.

    Returns:
        The secret value, or None if not found and not required.
    """
    value = os.getenv(key)
    if value:
        return value

    if required:
        raise ValueError(f"Required secret '{key}' is missing.")
    return None


def validate_secrets() -> bool:
    """
    Validate that all required secrets are present in the environment.

    Returns:
        True if all required secrets are present, False otherwise.
    """
    missing = []
    for key in REQUIRED_SECRETS.keys():
        if not os.getenv(key):
            missing.append(f"{key} ({REQUIRED_SECRETS[key]})")

    if missing:
        logger.error("Missing required secrets:")
        for item in missing:
            logger.error(f"  - {item}")
        logger.error("\nPlease add these to your .env file or environment variables.")
        return False

    logger.info("All required secrets are present.")
    return True


def get_hf_token() -> str:
    """Get the HuggingFace token from environment."""
    return get_secret("HF_TOKEN", required=True)


def get_prolific_api_key() -> str:
    """Get the Prolific API key from environment."""
    return get_secret("PROLIFIC_API_KEY", required=True)


def init_secrets(env_path: Optional[Path] = None) -> SecretsManager:
    """
    Initialize and return a SecretsManager instance.

    Args:
        env_path: Optional path to .env file.

    Returns:
        Initialized SecretsManager instance.

    Raises:
        ValueError: If required secrets are missing.
    """
    manager = SecretsManager(env_path)
    if not manager.validate_secrets():
        raise ValueError("Initialization failed: missing required secrets.")
    return manager
