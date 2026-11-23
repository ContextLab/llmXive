import os
from typing import Optional
from dataclasses import dataclass


class EnvironmentError(Exception):
    """Custom exception for environment configuration errors."""
    pass


@dataclass
class EnvConfig:
    """Container for validated environment configuration."""
    openneuro_api_key: str
    data_dir: str


def _validate_required(var_name: str, value: Optional[str]) -> str:
    """Validate that an environment variable is present and non-empty.
    
    Args:
        var_name: Name of the environment variable for error messages.
        value: The value retrieved from the environment.
        
    Returns:
        The validated string value.
        
    Raises:
        EnvironmentError: If the variable is missing or empty.
    """
    if value is None or value.strip() == "":
        raise EnvironmentError(
            f"Required environment variable '{var_name}' is not set or is empty."
        )
    return value.strip()


def get_config() -> EnvConfig:
    """Load and validate all required environment variables.
    
    Returns:
        EnvConfig object containing validated configuration values.
        
    Raises:
        EnvironmentError: If any required variable is missing or invalid.
    """
    api_key = _validate_required(
        "OPENNEURO_API_KEY", 
        os.getenv("OPENNEURO_API_KEY")
    )
    
    data_dir = _validate_required(
        "DATA_DIR", 
        os.getenv("DATA_DIR")
    )
    
    return EnvConfig(
        openneuro_api_key=api_key,
        data_dir=data_dir
    )


def get_openneuro_api_key() -> str:
    """Retrieve and validate the OpenNeuro API key.
    
    Returns:
        The validated API key string.
        
    Raises:
        EnvironmentError: If the key is missing or empty.
    """
    return _validate_required(
        "OPENNEURO_API_KEY", 
        os.getenv("OPENNEURO_API_KEY")
    )


def get_data_dir() -> str:
    """Retrieve and validate the data directory path.
    
    Returns:
        The validated data directory path string.
        
    Raises:
        EnvironmentError: If the path is missing or empty.
    """
    return _validate_required(
        "DATA_DIR", 
        os.getenv("DATA_DIR")
    )
