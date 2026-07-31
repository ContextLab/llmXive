import os
from pathlib import Path
from typing import Optional, Dict, Any
from dotenv import load_dotenv
from dotenv.main import DotEnv

# Define the project root relative to this file
PROJECT_ROOT = Path(__file__).parent.parent.parent
ENV_FILE_PATH = PROJECT_ROOT / ".env"

# Required keys for ADNI authentication
REQUIRED_ADNI_KEYS = {
    "ADNI_USERNAME",
    "ADNI_PASSWORD",
    "ADNI_IDGK_URL"
}

def load_environment() -> bool:
    """
    Loads environment variables from the .env file if it exists.
    
    Returns:
        bool: True if .env was found and loaded, False otherwise.
    """
    if ENV_FILE_PATH.exists():
        load_dotenv(dotenv_path=ENV_FILE_PATH)
        return True
    return False

def validate_adni_credentials() -> Dict[str, Any]:
    """
    Validates the presence of required ADNI credentials in the environment.
    
    Returns:
        Dict[str, Any]: A dictionary containing:
            - 'valid': bool indicating if all keys are present and non-empty
            - 'missing': list of missing or empty key names
            - 'values': dict of present values (masked for security)
    
    Raises:
        ValueError: If validation fails (missing keys).
    """
    missing_keys = []
    values = {}
    
    for key in REQUIRED_ADNI_KEYS:
        val = os.getenv(key)
        if not val or not val.strip():
            missing_keys.append(key)
        else:
            # Mask the value for logging/debugging safety
            values[key] = f"{val[:2]}***{val[-2:]}" if len(val) > 4 else "***"
    
    if missing_keys:
        raise ValueError(
            f"Missing required ADNI environment variables: {', '.join(missing_keys)}. "
            f"Please create a .env file at {ENV_FILE_PATH} with these keys."
        )
    
    return {
        "valid": True,
        "missing": [],
        "values": values
    }

def get_config(key: str, default: Optional[str] = None) -> Optional[str]:
    """
    Retrieves a configuration value from the environment.
    
    Args:
        key: The environment variable key.
        default: Optional default value if key is not found.
    
    Returns:
        The value or default.
    """
    return os.getenv(key, default)

def check_env() -> None:
    """
    Convenience function to load environment and validate ADNI credentials.
    Raises ValueError if validation fails.
    """
    load_environment()
    validate_adni_credentials()
