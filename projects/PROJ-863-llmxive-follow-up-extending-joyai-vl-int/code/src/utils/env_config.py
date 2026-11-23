import os
from typing import Optional, Tuple
from pathlib import Path
import sys

# Define required environment variables
REQUIRED_ENV_VARS = [
    "JOYAI_VL_MODEL_PATH",
    "DATA_SEED"
]

def get_required_env_vars() -> Tuple[str, ...]:
    """
    Returns a tuple of required environment variable names.
    """
    return tuple(REQUIRED_ENV_VARS)

def validate_environment() -> Optional[str]:
    """
    Validates that all required environment variables are set.
    Returns an error message if validation fails, None if successful.
    """
    missing_vars = []
    for var in REQUIRED_ENV_VARS:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        return f"Missing required environment variables: {', '.join(missing_vars)}"
    
    # Validate DATA_SEED is an integer
    seed_str = os.getenv("DATA_SEED")
    if seed_str is not None:
        try:
            int(seed_str)
        except ValueError:
            return f"DATA_SEED must be an integer, got: {seed_str}"
    
    # Validate JOYAI_VL_MODEL_PATH exists if it looks like a local path
    model_path = os.getenv("JOYAI_VL_MODEL_PATH")
    if model_path and not model_path.startswith(("http://", "https://", "hf://")):
        # Check if it's a local path
        path_obj = Path(model_path)
        if not path_obj.exists():
            # We don't fail immediately here because the model might be downloaded later,
            # but we log a warning or raise a specific error if the project logic requires it immediately.
            # For now, we just ensure the variable is set.
            pass 
    
    return None

def load_environment_config() -> dict:
    """
    Loads environment variables into a dictionary.
    Raises ValueError if validation fails.
    """
    error = validate_environment()
    if error:
        raise ValueError(error)
    
    return {
        "JOYAI_VL_MODEL_PATH": os.getenv("JOYAI_VL_MODEL_PATH"),
        "DATA_SEED": int(os.getenv("DATA_SEED")),
    }

def setup_environment(env_file_path: Optional[Path] = None) -> dict:
    """
    Loads environment variables from a .env file if provided, 
    validates the environment, and returns the config dictionary.
    
    Args:
        env_file_path: Path to the .env file. If None, attempts to find 
                       .env in the project root.
    
    Returns:
        dict: Configuration dictionary with validated values.
    
    Raises:
        ValueError: If required variables are missing or invalid.
        FileNotFoundError: If the specified .env file is not found.
    """
    if env_file_path is None:
        # Default to .env in the project root (parent of code/)
        # Assuming this script is run from code/ or root
        project_root = Path(__file__).resolve().parents[2]
        env_file_path = project_root / ".env"
    
    if env_file_path.exists():
        with open(env_file_path, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    if "=" in line:
                        key, value = line.split("=", 1)
                        os.environ[key.strip()] = value.strip()
    
    return load_environment_config()
