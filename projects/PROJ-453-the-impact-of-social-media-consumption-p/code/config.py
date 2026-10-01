import os
from pathlib import Path
from typing import List, Optional

# Core constants
RANDOM_SEED = 42
DATA_ROOT = "data"
RESULTS_ROOT = "results"

def ensure_directories() -> None:
    """
    Create all required project directories if they do not exist.
    """
    dirs = [
        DATA_ROOT,
        f"{DATA_ROOT}/raw",
        f"{DATA_ROOT}/processed",
        RESULTS_ROOT,
        f"{RESULTS_ROOT}/models",
        f"{RESULTS_ROOT}/figures",
        "code",
        "tests",
        "contracts",
        "research",
        "logs"
    ]
    for d in dirs:
        Path(d).mkdir(parents=True, exist_ok=True)

def get_data_path(filename: str, subfolder: Optional[str] = None) -> Path:
    """
    Construct a path to a data file.
    
    Args:
        filename: Name of the file.
        subfolder: Optional subfolder within data root (e.g., 'raw', 'processed').
    
    Returns:
        Absolute path to the file.
    """
    if subfolder:
        return Path(DATA_ROOT) / subfolder / filename
    return Path(DATA_ROOT) / filename

def get_results_path(filename: str, subfolder: Optional[str] = None) -> Path:
    """
    Construct a path to a results file.
    
    Args:
        filename: Name of the file.
        subfolder: Optional subfolder within results root (e.g., 'models', 'figures').
    
    Returns:
        Absolute path to the file.
    """
    if subfolder:
        return Path(RESULTS_ROOT) / subfolder / filename
    return Path(RESULTS_ROOT) / filename

def get_logs_path(filename: str) -> Path:
    """
    Construct a path to a log file.
    
    Args:
        filename: Name of the log file.
    
    Returns:
        Absolute path to the log file.
    """
    return Path("logs") / filename
