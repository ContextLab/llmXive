import os
from pathlib import Path
import yaml

def get_project_root() -> Path:
    """
    Returns the project root directory path.
    Assumes the project root is the parent of the 'code' directory.
    """
    current_file = Path(__file__).resolve()
    # Navigate up to find the project root (usually parent of 'code')
    if current_file.name == "config.py":
        # If running from code/utils/config.py
        return current_file.parent.parent
    return Path.cwd()

def get_data_dir() -> Path:
    """Returns the path to the data directory."""
    return get_project_root() / "data"

def get_results_dir() -> Path:
    """Returns the path to the results directory."""
    return get_project_root() / "results"

def load_env_config() -> dict:
    """
    Loads configuration from environment variables or a config file.
    
    Returns:
        A dictionary of configuration values.
    """
    config = {
        "LOG_LEVEL": os.getenv("LOG_LEVEL", "INFO"),
        "SEED": os.getenv("SEED", "42"),
        "DATA_DIR": str(get_data_dir()),
        "RESULTS_DIR": str(get_results_dir())
    }
    return config
