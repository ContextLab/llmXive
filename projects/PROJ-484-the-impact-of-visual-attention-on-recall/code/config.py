"""
Configuration management module for the Visual Attention Recall project.

Loads environment variables from a .env file (if present) and provides
centralized access to project configuration values.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Determine the project root directory (parent of the 'code' directory)
# This ensures paths are relative to the project root regardless of CWD
PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_FILE_PATH = PROJECT_ROOT / "code" / ".env"

# Load environment variables from .env file if it exists
# load_dotenv returns True if successful, False otherwise
load_dotenv(dotenv_path=ENV_FILE_PATH, override=True)

def get_config():
    """
    Retrieves the current configuration from environment variables.

    Returns:
        dict: A dictionary containing the configuration values.
    """
    return {
        "data_path": os.getenv("DATA_PATH", "./data"),
        "random_seed": int(os.getenv("RANDOM_SEED", 42)),
    }

# Convenience accessors
def get_data_path():
    """
    Returns the configured data path.

    Returns:
        str: The path to the data directory.
    """
    return os.getenv("DATA_PATH", "./data")

def get_random_seed():
    """
    Returns the configured random seed.

    Returns:
        int: The random seed value.
    """
    return int(os.getenv("RANDOM_SEED", 42))

# Validate configuration on import to catch errors early
def validate_config():
    """
    Validates that required configuration values are present and valid.

    Raises:
        ValueError: If a required configuration value is missing or invalid.
    """
    data_path = os.getenv("DATA_PATH")
    if not data_path:
        raise ValueError("DATA_PATH environment variable is not set.")

    try:
        seed = int(os.getenv("RANDOM_SEED", 42))
        if seed < 0:
            raise ValueError("RANDOM_SEED must be a non-negative integer.")
    except ValueError as e:
        raise ValueError(f"Invalid RANDOM_SEED: {e}")

    # Check if the data path exists (optional but recommended)
    data_dir = Path(data_path)
    if not data_dir.exists():
        # Log a warning instead of failing, as the directory might be created later
        print(f"Warning: Data directory '{data_path}' does not exist yet.")

# Run validation immediately
validate_config()
