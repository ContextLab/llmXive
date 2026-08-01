import os
from pathlib import Path
from typing import Dict, Any, Optional
from src.config import get_project_root, get_data_root, get_state_root, get_reports_root, get_figures_root, get_cache_dir

def get_raw_data_path() -> Path:
    return get_data_root() / "raw"

def get_processed_data_path() -> Path:
    return get_data_root() / "processed"

def get_state_path() -> Path:
    return get_state_root()

def get_figures_path() -> Path:
    return get_figures_root()

def get_reports_path() -> Path:
    return get_reports_root()

def get_cache_path() -> Path:
    return get_cache_dir()

def ensure_directories():
    """Ensure all data-related directories exist."""
    dirs = [
        get_raw_data_path(),
        get_processed_data_path(),
        get_state_path(),
        get_figures_path(),
        get_reports_path(),
        get_cache_path()
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

def is_data_directory_ready() -> bool:
    """Check if all required data directories exist."""
    dirs = [
        get_raw_data_path(),
        get_processed_data_path(),
        get_state_path(),
        get_reports_path()
    ]
    return all(d.exists() and d.is_dir() for d in dirs)

def get_data_directories() -> Dict[str, Path]:
    return {
        "raw": get_raw_data_path(),
        "processed": get_processed_data_path(),
        "state": get_state_path(),
        "figures": get_figures_path(),
        "reports": get_reports_path(),
        "cache": get_cache_path()
    }

def get_data_summary() -> Dict[str, Any]:
    dirs = get_data_directories()
    return {path.name: str(path) for path in dirs.values()}
