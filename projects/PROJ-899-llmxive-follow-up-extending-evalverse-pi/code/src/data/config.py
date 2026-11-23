import os
from pathlib import Path
from typing import Dict, Any, Optional
from src.config import get_project_root, get_data_root, get_state_root, get_reports_root, get_figures_root, get_cache_dir

def get_raw_data_path() -> str:
    return os.path.join(get_data_root(), "raw")

def get_processed_data_path() -> str:
    return os.path.join(get_data_root(), "processed")

def get_state_path() -> str:
    return get_state_root()

def get_figures_path() -> str:
    return get_figures_root()

def get_reports_path() -> str:
    return get_reports_root()

def get_cache_path() -> str:
    return get_cache_dir()

def ensure_directories() -> None:
    """Ensure all data directories exist."""
    from src.utils import ensure_directories
    ensure_directories()

def is_data_directory_ready() -> bool:
    """Check if the data directory structure is ready."""
    dirs = [get_raw_data_path(), get_processed_data_path()]
    return all(os.path.isdir(d) for d in dirs)

def get_data_directories() -> Dict[str, str]:
    """Return a dict of all data paths."""
    return {
        "raw": get_raw_data_path(),
        "processed": get_processed_data_path(),
        "state": get_state_path(),
        "figures": get_figures_path(),
        "reports": get_reports_path(),
        "cache": get_cache_path()
    }

def get_data_summary() -> Dict[str, Any]:
    """Get a summary of the data directory status."""
    dirs = get_data_directories()
    status = {}
    for name, path in dirs.items():
        status[name] = {
            "path": path,
            "exists": os.path.exists(path),
            "is_dir": os.path.isdir(path)
        }
    return status
