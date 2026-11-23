import os
from pathlib import Path

def get_project_root() -> Path:
    """
    Get the project root directory.
    
    Assumes the project root is the parent of the 'code' directory.
    Falls back to the current working directory if 'code' is not found.
    
    Returns:
        Path: The project root directory.
    """
    current_file = Path(__file__).resolve()
    # Navigate up from code/utils/config.py to project root
    project_root = current_file.parent.parent.parent
    
    if (project_root / "code").exists():
        return project_root
    
    # Fallback to current working directory
    return Path.cwd()

def get_data_dir() -> Path:
    """Get the data directory path."""
    return get_project_root() / "data"

def get_results_dir() -> Path:
    """Get the results directory path."""
    return get_project_root() / "results"

def load_env_config():
    """
    Load configuration from environment variables.
    
    Returns:
        dict: Configuration dictionary from environment variables.
    """
    config = {}
    # Example: Load specific env vars if needed
    # config['TIME_BUDGET'] = os.getenv('TIME_BUDGET', '6.0')
    return config
