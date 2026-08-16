import os
from code.config import get_config

def get_project_root() -> str:
    """Return the absolute path to the project root."""
    config = get_config()
    root = config.get("project_root", None)
    if root is None:
        # Fallback to current working directory if not set in config
        # In a real deployment, this should be set in config.py
        root = os.getcwd()
    return os.path.abspath(root)

def get_raw_path() -> str:
    """Return the path to the raw data directory."""
    return os.path.join(get_project_root(), "data", "raw")

def get_processed_path() -> str:
    """Return the path to the processed data directory."""
    return os.path.join(get_project_root(), "data", "processed")

def get_results_path() -> str:
    """Return the path to the results directory."""
    return os.path.join(get_project_root(), "data", "results")

def ensure_dir(path: str) -> None:
    """Ensure the directory exists, creating it if necessary."""
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)
