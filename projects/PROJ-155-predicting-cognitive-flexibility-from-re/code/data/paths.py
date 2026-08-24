import os
from code.config import get_config

def get_project_root() -> str:
    """
    Returns the absolute path to the project root.
    Assumes code/data/paths.py is in the code/data directory.
    """
    # Go up two levels from code/data/paths.py
    current_file_dir = os.path.dirname(os.path.abspath(__file__))
    code_dir = os.path.dirname(current_file_dir)
    return os.path.dirname(code_dir)

def get_raw_path() -> str:
    """
    Returns the path to the raw data directory.
    """
    root = get_project_root()
    return os.path.join(root, 'data', 'raw')

def get_processed_path() -> str:
    """
    Returns the path to the processed data directory.
    """
    root = get_project_root()
    return os.path.join(root, 'data', 'processed')

def get_results_path() -> str:
    """
    Returns the path to the results directory.
    """
    root = get_project_root()
    return os.path.join(root, 'data', 'results')

def ensure_dir(path: str) -> None:
    """
    Creates a directory if it does not exist.
    """
    if not os.path.exists(path):
        os.makedirs(path)
