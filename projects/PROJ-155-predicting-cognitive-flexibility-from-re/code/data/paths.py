import os
from code.config import get_config

def get_project_root() -> str:
    """Returns the root directory of the project."""
    return get_config()["project_root"]

def get_raw_path() -> str:
    """Returns the path to the raw data directory."""
    return os.path.join(get_project_root(), get_config()["data_raw"])

def get_processed_path() -> str:
    """Returns the path to the processed data directory."""
    return os.path.join(get_project_root(), get_config()["data_processed"])

def get_results_path() -> str:
    """Returns the path to the results directory."""
    return os.path.join(get_project_root(), get_config()["data_results"])

def ensure_dir(path: str) -> None:
    """Creates the directory if it does not exist."""
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True)
