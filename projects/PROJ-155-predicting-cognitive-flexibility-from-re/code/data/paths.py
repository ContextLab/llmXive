import os
from code.config import get_config

def get_project_root() -> str:
    """Get the project root directory."""
    # Assuming the project root is the parent of the 'code' directory
    # or we can use an environment variable or config.
    # For now, we assume the standard structure relative to this file.
    current_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.dirname(current_dir)

def get_raw_path() -> str:
    """Get the path to the raw data directory."""
    project_root = get_project_root()
    raw_path = os.path.join(project_root, "data", "raw")
    os.makedirs(raw_path, exist_ok=True)
    return raw_path

def get_processed_path() -> str:
    """Get the path to the processed data directory."""
    project_root = get_project_root()
    processed_path = os.path.join(project_root, "data", "processed")
    os.makedirs(processed_path, exist_ok=True)
    return processed_path

def get_results_path() -> str:
    """Get the path to the results directory."""
    project_root = get_project_root()
    results_path = os.path.join(project_root, "data", "results")
    os.makedirs(results_path, exist_ok=True)
    return results_path

def ensure_dir(dir_path: str) -> str:
    """Ensure a directory exists, creating it if necessary."""
    os.makedirs(dir_path, exist_ok=True)
    return dir_path
