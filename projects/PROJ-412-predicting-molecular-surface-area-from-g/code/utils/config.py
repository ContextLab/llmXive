import os
from pathlib import Path

def get_project_root() -> Path:
    """
    Returns the project root directory.
    Assumes the project root is the parent of the 'code' directory.
    """
    current_file = Path(__file__)
    code_dir = current_file.parent
    return code_dir.parent

def get_data_dir() -> Path:
    """
    Returns the path to the data directory.
    """
    return get_project_root() / "data"

def get_results_dir() -> Path:
    """
    Returns the path to the results directory.
    """
    return get_project_root() / "results"

def load_env_config():
    """
    Loads configuration from environment variables.
    Returns a dictionary of configuration values.
    """
    return {
        "project_root": str(get_project_root()),
        "data_dir": str(get_data_dir()),
        "results_dir": str(get_results_dir()),
    }
