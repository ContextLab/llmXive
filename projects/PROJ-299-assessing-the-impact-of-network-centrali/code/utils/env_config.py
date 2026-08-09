"""
Environment configuration management for ADNI credentials.

Loads credentials from .env file and validates presence of required keys.
"""
import os
from pathlib import Path
from typing import Optional, Dict, Any
from dotenv import load_dotenv
from dotenv.main import DotEnv


# Required ADNI environment variables
REQUIRED_ENV_KEYS = [
    "ADNI_USERNAME",
    "ADNI_PASSWORD",
    "ADNI_PROJECT_ID",
    "LONI_IDGK_URL"
]

# Optional environment variables with defaults
OPTIONAL_ENV_KEYS: Dict[str, Any] = {
    "ADNI_DATA_DIR": "data/raw",
    "LOG_LEVEL": "INFO",
    "MAX_WORKERS": "4"
}


def load_environment(env_path: Optional[Path] = None) -> bool:
    """
    Load environment variables from a .env file.
    
    Args:
        env_path: Path to .env file. If None, searches in project root.
        
    Returns:
        True if loading was successful, False otherwise.
    """
    if env_path is None:
        # Default to project root .env
        project_root = Path(__file__).resolve().parent.parent.parent
        env_path = project_root / ".env"
    
    if not env_path.exists():
        raise FileNotFoundError(f"Environment file not found: {env_path}")
    
    return load_dotenv(dotenv_path=env_path, override=True)


def validate_adni_credentials() -> bool:
    """
    Validate that all required ADNI credentials are present in the environment.
    
    Returns:
        True if all required keys are present and non-empty.
        
    Raises:
        ValueError: If any required credential is missing or empty.
    """
    missing_keys = []
    empty_keys = []
    
    for key in REQUIRED_ENV_KEYS:
        value = os.getenv(key)
        if value is None:
            missing_keys.append(key)
        elif value.strip() == "":
            empty_keys.append(key)
    
    if missing_keys:
        raise ValueError(
            f"Missing required ADNI environment variables: {', '.join(missing_keys)}. "
            "Please ensure your .env file contains these keys with valid values."
        )
    
    if empty_keys:
        raise ValueError(
            f"Empty ADNI environment variables: {', '.join(empty_keys)}. "
            "Please provide non-empty values for these keys in your .env file."
        )
    
    return True


def get_config() -> Dict[str, str]:
    """
    Retrieve all ADNI-related configuration values.
    
    Returns:
        Dictionary containing all ADNI configuration values.
        
    Raises:
        ValueError: If required credentials are missing (validates first).
    """
    # Validate credentials first
    validate_adni_credentials()
    
    config = {}
    
    # Add required keys
    for key in REQUIRED_ENV_KEYS:
        config[key] = os.getenv(key, "")
    
    # Add optional keys with defaults
    for key, default in OPTIONAL_ENV_KEYS.items():
        config[key] = os.getenv(key, default)
    
    return config


def check_env() -> Dict[str, Any]:
    """
    Check the current environment status.
    
    Returns:
        Dictionary with environment check results including:
        - 'valid': bool indicating if all required keys are present
        - 'missing': list of missing keys
        - 'empty': list of empty keys
        - 'loaded_keys': list of all loaded keys
    """
    result = {
        "valid": True,
        "missing": [],
        "empty": [],
        "loaded_keys": []
    }
    
    # Check all required keys
    for key in REQUIRED_ENV_KEYS:
        value = os.getenv(key)
        if value is None:
            result["missing"].append(key)
            result["valid"] = False
        elif value.strip() == "":
            result["empty"].append(key)
            result["valid"] = False
        else:
            result["loaded_keys"].append(key)
    
    # Check optional keys
    for key in OPTIONAL_ENV_KEYS.keys():
        if os.getenv(key):
            result["loaded_keys"].append(key)
    
    return result
