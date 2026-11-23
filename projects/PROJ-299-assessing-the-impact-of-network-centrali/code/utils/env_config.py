import os
from pathlib import Path
from typing import Optional, Dict, Any
from dotenv import load_dotenv
from dotenv.main import DotEnv

# Define the required ADNI environment variables
REQUIRED_ADNI_KEYS = [
    "ADNI_USERNAME",
    "ADNI_PASSWORD",
    "ADNI_PROJECT_ID"
]

def load_environment(env_path: Optional[Path] = None) -> DotEnv:
    """
    Load environment variables from a .env file.
    
    Args:
        env_path: Path to the .env file. If None, searches in the project root.
    
    Returns:
        DotEnv object containing the loaded variables.
    
    Raises:
        FileNotFoundError: If the specified .env file does not exist.
    """
    if env_path is None:
        # Default to .env in the project root (parent of code/)
        env_path = Path(__file__).parent.parent.parent / ".env"
    
    if not env_path.exists():
        raise FileNotFoundError(f"Environment file not found at {env_path}")
    
    # Load the environment variables
    loaded = load_dotenv(dotenv_path=env_path)
    return loaded

def validate_adni_credentials() -> Dict[str, str]:
    """
    Validate the presence of required ADNI credentials in the environment.
    
    Returns:
        A dictionary mapping key names to their values.
    
    Raises:
        ValueError: If any required ADNI credential is missing or empty.
    """
    # First, ensure the .env file is loaded
    try:
        load_environment()
    except FileNotFoundError:
        # If .env is missing, we check the system env directly (for CI/CD scenarios)
        pass

    missing_keys = []
    credentials = {}

    for key in REQUIRED_ADNI_KEYS:
        value = os.getenv(key)
        if not value or value.strip() == "":
            missing_keys.append(key)
        else:
            credentials[key] = value

    if missing_keys:
        raise ValueError(
            f"Missing or empty required ADNI credentials: {', '.join(missing_keys)}. "
            "Please ensure these are set in the .env file or system environment variables."
        )

    return credentials

def get_config() -> Dict[str, Any]:
    """
    Retrieve the full configuration dictionary including ADNI credentials.
    
    Returns:
        Dictionary containing configuration settings.
    """
    try:
        adni_creds = validate_adni_credentials()
    except ValueError as e:
        # Re-raise to allow caller to handle the error appropriately
        raise e

    return {
        "adni": adni_creds,
        "data_paths": {
            "raw": Path("data/raw"),
            "processed": Path("data/processed"),
            "analysis": Path("data/analysis"),
            "outputs": Path("outputs")
        },
        "logging": {
            "path": Path("logs/pipeline.log")
        }
    }

def check_env() -> bool:
    """
    Perform a lightweight check to see if the environment is ready.
    
    Returns:
        True if all required ADNI credentials are present, False otherwise.
    """
    try:
        validate_adni_credentials()
        return True
    except ValueError:
        return False
