import os
from pathlib import Path
from typing import Dict, Any, Optional

# Import project root helpers from parent config if available, otherwise fallback
try:
    from src.config import get_project_root
except ImportError:
    def get_project_root() -> Path:
        """Fallback to current working directory if src.config is not available."""
        return Path.cwd()

# Define relative paths for data subdirectories
DATA_ROOT_NAME = "data"
RAW_DATA_DIR_NAME = "raw"
PROCESSED_DATA_DIR_NAME = "processed"
STATE_DIR_NAME = "state"
FIGURES_DIR_NAME = "figures"
REPORTS_DIR_NAME = "reports"
CACHE_DIR_NAME = "cache"

def get_data_root() -> Path:
    """Get the root data directory path."""
    return get_project_root() / DATA_ROOT_NAME

def get_raw_data_path() -> Path:
    """Get the path to the raw data directory."""
    return get_data_root() / RAW_DATA_DIR_NAME

def get_processed_data_path() -> Path:
    """Get the path to the processed data directory."""
    return get_data_root() / PROCESSED_DATA_DIR_NAME

def get_state_path() -> Path:
    """Get the path to the state directory."""
    return get_data_root() / STATE_DIR_NAME

def get_figures_path() -> Path:
    """Get the path to the figures directory."""
    return get_data_root() / FIGURES_DIR_NAME

def get_reports_path() -> Path:
    """Get the path to the reports directory."""
    return get_data_root() / REPORTS_DIR_NAME

def get_cache_path() -> Path:
    """Get the path to the cache directory."""
    return get_data_root() / CACHE_DIR_NAME

def ensure_directories() -> Dict[str, Path]:
    """
    Ensure all required data subdirectories exist.
    
    Returns:
        Dict mapping directory name to Path object.
    """
    data_dirs = {
        "raw": get_raw_data_path(),
        "processed": get_processed_data_path(),
        "state": get_state_path(),
        "figures": get_figures_path(),
        "reports": get_reports_path(),
        "cache": get_cache_path(),
    }
    
    for name, path in data_dirs.items():
        path.mkdir(parents=True, exist_ok=True)
        
    return data_dirs

def is_data_directory_ready() -> bool:
    """
    Check if all required data directories exist and are writable.
    
    Returns:
        True if all directories are ready, False otherwise.
    """
    try:
        dirs = ensure_directories()
        # Verify we can write a temp file to each directory
        for name, path in dirs.items():
            test_file = path / ".write_test"
            try:
                test_file.touch()
                test_file.unlink()
            except (OSError, PermissionError):
                return False
        return True
    except Exception:
        return False

def get_data_directories() -> Dict[str, Path]:
    """
    Get a dictionary of all data directories without creating them.
    
    Returns:
        Dict mapping directory name to Path object.
    """
    return {
        "raw": get_raw_data_path(),
        "processed": get_processed_data_path(),
        "state": get_state_path(),
        "figures": get_figures_path(),
        "reports": get_reports_path(),
        "cache": get_cache_path(),
    }

def get_data_summary() -> Dict[str, Any]:
    """
    Get a summary of the data directory structure.
    
    Returns:
        Dict with directory paths and existence status.
    """
    dirs = get_data_directories()
    summary = {}
    for name, path in dirs.items():
        summary[name] = {
            "path": str(path),
            "exists": path.exists(),
            "is_dir": path.is_dir(),
        }
    return summary
