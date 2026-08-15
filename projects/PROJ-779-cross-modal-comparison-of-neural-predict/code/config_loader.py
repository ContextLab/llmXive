"""
Configuration loader for the llmXive pipeline.

Loads environment variables from a `.env` file (if present) and provides
a mechanism to access them with defaults.
"""
import os
from pathlib import Path
from typing import Any, Dict, Optional

# Import logger from existing utility
from code.utils.logger import get_logger

logger = get_logger(__name__)

# Default configuration values
DEFAULTS: Dict[str, Any] = {
    "OPENNEURO_API_KEY": "",
    "LOG_LEVEL": "INFO",
    "DATA_ROOT": "data",
    "CODE_ROOT": "code",
    "RESULTS_ROOT": "data/results",
    "PROCESSED_ROOT": "data/processed",
    "FIGURES_ROOT": "figures",
    "RANDOM_SEED": "42",
    "MAX_WORKERS": "1",  # CPU constrained
}


def load(env_path: Optional[str] = None) -> Dict[str, str]:
    """
    Load environment variables from a .env file and merge with defaults.

    Args:
        env_path: Path to the .env file. If None, looks for .env in the
                  project root (parent of code/).

    Returns:
        Dictionary of loaded environment variables.

    Raises:
        FileNotFoundError: If the specified .env path does not exist.
    """
    if env_path is None:
        # Default to project root .env (assuming script runs from project root)
        # If code is in 'code/', project root is one level up
        current_dir = Path(__file__).resolve().parent
        project_root = current_dir.parent
        env_path = str(project_root / ".env")

    env_file = Path(env_path)

    if not env_file.exists():
        logger.warning(f"Environment file not found at {env_path}. Using defaults.")
        # Return a copy of defaults to avoid modifying global state
        return {k: str(v) for k, v in DEFAULTS.items()}

    try:
        # Use python-dotenv to load the file
        # We use load_dotenv with stream=False to load into os.environ
        from dotenv import load_dotenv
        
        loaded = load_dotenv(dotenv_path=env_path, override=True)
        
        if not loaded:
            logger.warning(f"Failed to load environment variables from {env_path}")
            return {k: str(v) for k, v in DEFAULTS.items()}
        
        logger.info(f"Loaded environment variables from {env_path}")
        
        # Merge with defaults: env vars take precedence, but ensure all keys exist
        config = {k: str(v) for k, v in DEFAULTS.items()}
        for key in DEFAULTS.keys():
            if key in os.environ:
                config[key] = os.environ[key]
        
        return config

    except Exception as e:
        logger.error(f"Error loading environment file: {e}")
        # Fallback to defaults on error to prevent pipeline crash
        return {k: str(v) for k, v in DEFAULTS.items()}


def get_config_value(key: str, default: Optional[str] = None) -> str:
    """
    Get a specific configuration value from the environment.

    Args:
        key: The environment variable key.
        default: Default value if key is not found.

    Returns:
        The value as a string.
    """
    # Ensure .env is loaded first
    load()
    
    value = os.environ.get(key)
    if value is None and default is not None:
        return default
    if value is None:
        # Fallback to global defaults if not in env and no specific default
        return str(DEFAULTS.get(key, ""))
    return value


# Convenience function to ensure .env is loaded on import
def _init():
    """Initialize configuration on module load."""
    load()
    logger.debug("Configuration loader initialized.")

# Auto-load on import
_init()
