"""
Secrets management module for llmXive pipeline.
Handles loading, validation, and access to API keys and sensitive configuration.

Supports loading from environment variables and .env files.
Fails loudly if required secrets are missing.
"""
import os
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Define required secrets based on project needs
REQUIRED_SECRETS = {
    "HF_TOKEN": "HuggingFace API token for dataset access and model inference",
    "PROLIFIC_API_KEY": "Prolific API key for rater recruitment (if applicable)",
}

def load_env_file(env_path: Optional[str] = None) -> bool:
    """
    Load environment variables from a .env file.
    
    Args:
        env_path: Path to .env file. If None, looks for .env in project root.
        
    Returns:
        True if file was loaded, False if not found.
    """
    if env_path is None:
        # Look for .env in current working directory or project root
        env_path = Path.cwd() / ".env"
        if not env_path.exists():
            # Try parent directory (project root)
            env_path = Path(__file__).parent.parent / ".env"
    
    if env_path.exists():
        logger.info(f"Loading environment variables from {env_path}")
        load_dotenv(str(env_path))
        return True
    else:
        logger.warning(f"No .env file found at {env_path}. Using environment variables only.")
        return False

def get_secret(key: str, required: bool = True) -> Optional[str]:
    """
    Retrieve a secret from environment variables.
    
    Args:
        key: The environment variable name.
        required: If True, raise ValueError if the secret is missing.
        
    Returns:
        The secret value, or None if not found and not required.
        
    Raises:
        ValueError: If required secret is missing.
    """
    value = os.getenv(key)
    
    if value is None:
        if required:
            raise ValueError(
                f"Missing required secret: {key}. "
                f"Description: {REQUIRED_SECRETS.get(key, 'No description available')}. "
                f"Please set this environment variable or add it to your .env file."
            )
        else:
            logger.debug(f"Optional secret {key} not found.")
            return None
    
    return value

def validate_secrets() -> Dict[str, bool]:
    """
    Validate that all required secrets are present.
    
    Returns:
        Dictionary mapping secret names to their validation status.
        
    Raises:
        ValueError: If any required secret is missing.
    """
    results = {}
    missing = []
    
    for key, description in REQUIRED_SECRETS.items():
        value = os.getenv(key)
        if value and len(value.strip()) > 0:
            results[key] = True
            logger.debug(f"Secret {key} is present.")
        else:
            results[key] = False
            missing.append(key)
    
    if missing:
        missing_desc = "\n".join([
            f"  - {key}: {REQUIRED_SECRETS[key]}"
            for key in missing
        ])
        raise ValueError(
            f"Missing required secrets:\n{missing_desc}\n\n"
            "Please set these environment variables or add them to your .env file."
        )
    
    logger.info("All required secrets validated successfully.")
    return results

def get_hf_token() -> str:
    """
    Get HuggingFace token.
    
    Returns:
        The HuggingFace token string.
        
    Raises:
        ValueError: If HF_TOKEN is not set.
    """
    return get_secret("HF_TOKEN", required=True)

def get_prolific_api_key() -> Optional[str]:
    """
    Get Prolific API key (optional).
    
    Returns:
        The Prolific API key string, or None if not configured.
    """
    return get_secret("PROLIFIC_API_KEY", required=False)

class SecretsManager:
    """
    Context manager for secrets validation and access.
    """
    
    def __init__(self, env_path: Optional[str] = None, validate_on_enter: bool = True):
        """
        Initialize the secrets manager.
        
        Args:
            env_path: Path to .env file.
            validate_on_enter: If True, validate secrets when entering context.
        """
        self.env_path = env_path
        self.validate_on_enter = validate_on_enter
        self._validated = False
    
    def __enter__(self):
        # Load .env file if it exists
        load_env_file(self.env_path)
        
        if self.validate_on_enter:
            validate_secrets()
            self._validated = True
        
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # Cleanup if needed
        return False
    
    def get(self, key: str, required: bool = True) -> Optional[str]:
        """Get a secret value."""
        if not self._validated and required:
            raise RuntimeError("Secrets not validated. Call validate_secrets() or use as context manager.")
        return get_secret(key, required=required)
    
    @property
    def hf_token(self) -> str:
        """Get HuggingFace token."""
        return get_hf_token()
    
    @property
    def prolific_api_key(self) -> Optional[str]:
        """Get Prolific API key."""
        return get_prolific_api_key()

def init_secrets(env_path: Optional[str] = None) -> SecretsManager:
    """
    Initialize secrets management.
    
    Args:
        env_path: Optional path to .env file.
        
    Returns:
        Configured SecretsManager instance.
    """
    load_env_file(env_path)
    return SecretsManager(env_path=env_path, validate_on_enter=False)
