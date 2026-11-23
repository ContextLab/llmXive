import os
from pathlib import Path
from typing import Dict, Any, Optional

# Project Root
def get_project_root() -> Path:
    return Path(__file__).resolve().parent.parent.parent

def get_data_root() -> str:
    return os.path.join(get_project_root(), "data")

def get_state_root() -> str:
    return os.path.join(get_project_root(), "state")

def get_reports_root() -> str:
    return os.path.join(get_project_root(), "reports")

def get_figures_root() -> str:
    return os.path.join(get_project_root(), "figures")

def get_cache_dir() -> str:
    return os.path.join(get_project_root(), "cache")

def get_raw_data_dir() -> str:
    return os.path.join(get_data_root(), "raw")

def get_processed_data_dir() -> str:
    return os.path.join(get_data_root(), "processed")

# Constants
DATASET_URL = "https://zenodo.org/record/1234567/files/evalverse.tar.gz"
DATASET_DOI = "10.5281/zenodo.1234567"
RANDOM_SEED = 42

def ensure_environment() -> bool:
    """Ensure the environment is set up correctly."""
    dirs = [get_data_root(), get_state_root(), get_reports_root(), get_figures_root()]
    for d in dirs:
        Path(d).mkdir(parents=True, exist_ok=True)
    return True

def get_config_summary() -> Dict[str, Any]:
    """Return a summary of the configuration."""
    return {
        "project_root": str(get_project_root()),
        "data_root": get_data_root(),
        "dataset_url": DATASET_URL,
        "dataset_doi": DATASET_DOI,
        "random_seed": RANDOM_SEED
    }
