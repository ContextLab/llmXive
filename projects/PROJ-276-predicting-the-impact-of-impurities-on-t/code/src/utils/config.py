"""
Configuration management for the MgB2 Impurity Impact project.

Handles environment variable loading, API key validation, and project settings.
"""
import os
from pathlib import Path
from typing import Optional, Dict, Any
import json

from .logging import get_project_logger

logger = get_project_logger(__name__)


class ConfigError(Exception):
    """Custom exception for configuration errors."""
    pass


def load_env_file(env_path: Optional[Path] = None) -> Dict[str, str]:
    """
    Load environment variables from a .env file if it exists.
    
    Args:
        env_path: Path to the .env file. Defaults to project root/.env.
        
    Returns:
        Dictionary of loaded environment variables.
    """
    if env_path is None:
        env_path = Path(__file__).parent.parent.parent.parent / ".env"
        
    env_vars = {}
    
    if env_path.exists():
        logger.info(f"Loading environment variables from {env_path}")
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                # Skip empty lines and comments
                if not line or line.startswith('#'):
                    continue
                # Parse KEY=VALUE
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")
                    env_vars[key] = value
    else:
        logger.warning(f"No .env file found at {env_path}")
        
    return env_vars


def get_api_key(service_name: str, required: bool = True) -> Optional[str]:
    """
    Retrieve an API key for a specific service from environment variables.
    
    This function checks the environment for a key in the format:
    {SERVICE_NAME}_API_KEY (uppercase)
    
    Args:
        service_name: Name of the service (e.g., "MATERIALS_PROJECT", "HUGGINGFACE").
        required: If True, raises ConfigError if key is missing.
        
    Returns:
        The API key string if found, None otherwise (unless required=True).
        
    Raises:
        ConfigError: If the key is required but not found.
    """
    # Normalize service name to uppercase with underscores
    env_var_name = f"{service_name.upper().replace('-', '_')}_API_KEY"
    
    # First check if already in os.environ (from .env loading or system)
    api_key = os.environ.get(env_var_name)
    
    if api_key is None:
        # Try to load from .env file explicitly
        env_vars = load_env_file()
        if env_var_name in env_vars:
            api_key = env_vars[env_var_name]
            # Set it in os.environ for future access
            os.environ[env_var_name] = api_key
    
    if required and api_key is None:
        raise ConfigError(
            f"Required API key '{env_var_name}' not found. "
            f"Please set it in your environment or add it to a .env file."
        )
        
    if api_key:
        logger.info(f"API key found for {service_name}")
    else:
        logger.warning(f"No API key found for {service_name}")
        
    return api_key


def get_materials_project_api_key() -> Optional[str]:
    """
    Get the Materials Project API key.
    
    Returns:
        The API key string or None if not configured.
    """
    return get_api_key("materials_project", required=False)


def get_huggingface_token() -> Optional[str]:
    """
    Get the HuggingFace token for dataset access.
    
    Returns:
        The token string or None if not configured.
    """
    return get_api_key("huggingface", required=False)


def validate_materials_project_connection(api_key: Optional[str] = None) -> bool:
    """
    Validate that the Materials Project API key is configured.
    
    Args:
        api_key: Optional API key to validate. If None, retrieves from env.
        
    Returns:
        True if key is present and non-empty, False otherwise.
    """
    if api_key is None:
        api_key = get_materials_project_api_key()
        
    is_valid = api_key is not None and len(api_key) > 0
    
    if is_valid:
        logger.info("Materials Project API key is configured.")
    else:
        logger.warning("Materials Project API key is NOT configured. "
                     "Data ingestion from Materials Project will fail.")
                     
    return is_valid


def get_project_root() -> Path:
    """
    Get the root directory of the project.
    
    Returns:
        Path object pointing to the project root.
    """
    # Assuming this file is at code/src/utils/config.py
    # Project root is 4 levels up
    return Path(__file__).parent.parent.parent.parent


def get_config_summary() -> Dict[str, Any]:
    """
    Get a summary of current configuration status (without exposing secrets).
    
    Returns:
        Dictionary with configuration status for each service.
    """
    mp_key = get_materials_project_api_key()
    hf_token = get_huggingface_token()
    
    return {
        "materials_project": {
            "configured": mp_key is not None and len(mp_key) > 0,
            "key_length": len(mp_key) if mp_key else 0
        },
        "huggingface": {
            "configured": hf_token is not None and len(hf_token) > 0,
            "key_length": len(hf_token) if hf_token else 0
        },
        "project_root": str(get_project_root())
    }


def main():
    """
    Main entry point for running config validation as a script.
    
    Usage: python -m src.utils.config
    """
    print("=== Project Configuration Status ===")
    summary = get_config_summary()
    print(json.dumps(summary, indent=2))
    
    # Validate critical services
    if not summary["materials_project"]["configured"]:
        print("\n⚠️  WARNING: Materials Project API key not configured.")
        print("   Add it to a .env file as: MATERIALS_PROJECT_API_KEY=your_key")
        return 1
        
    print("\n✅ All critical configurations are valid.")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())
