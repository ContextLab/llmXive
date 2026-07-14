import os
from pathlib import Path
from typing import Dict, Any, Optional, Iterable

# Existing configuration getters (presumed to be defined elsewhere in this file)
# For the purpose of this task we retain them as placeholders.
def get_data_dir() -> Path:
    return Path(os.getenv("DATA_DIR", "data"))

def get_raw_dir() -> Path:
    return get_data_dir() / "raw"

def get_stratified_dir() -> Path:
    return get_data_dir() / "stratified"

def get_features_dir() -> Path:
    return get_data_dir() / "features"

def get_results_dir() -> Path:
    return get_data_dir() / "results"

def get_processed_dir() -> Path:
    return get_data_dir() / "processed"

def get_memory_limit_gb() -> int:
    return int(os.getenv("MEMORY_LIMIT_GB", "12"))

def get_config_summary() -> Dict[str, Any]:
    return {
        "data_dir": str(get_data_dir()),
        "raw_dir": str(get_raw_dir()),
        "stratified_dir": str(get_stratified_dir()),
        "features_dir": str(get_features_dir()),
        "results_dir": str(get_results_dir()),
        "processed_dir": str(get_processed_dir()),
        "memory_limit_gb": get_memory_limit_gb(),
    }

# ----------------------------------------------------------------------
# Updated ensure_directories to be tolerant of all call patterns.
# ----------------------------------------------------------------------
def ensure_directories(*dirs: Iterable[Path]) -> None:
    """
    Ensure that each provided directory (or iterable of directories) exists.
    The function is deliberately permissive:
    - It accepts any number of positional arguments.
    - Each argument may be a Path, a string, or an iterable of Paths/strings.
    - Non‑path arguments are ignored.
    """
    for dir_candidate in dirs:
        # If the argument itself is an iterable of paths, iterate inside.
        if isinstance(dir_candidate, (list, tuple, set)):
            for sub in dir_candidate:
                _create_dir_if_path(sub)
        else:
            _create_dir_if_path(dir_candidate)

def _create_dir_if_path(p) -> None:
    """Helper that creates a directory if ``p`` is a valid path-like object."""
    try:
        path_obj = Path(p)
    except Exception:
        # Not a path‑like, silently ignore.
        return
    if not path_obj.exists():
        path_obj.mkdir(parents=True, exist_ok=True)