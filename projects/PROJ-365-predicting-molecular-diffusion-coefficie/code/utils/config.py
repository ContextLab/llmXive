import os
from pathlib import Path

_cached_root: Path | None = None
_cached_log_path: Path | None = None

def get_project_root() -> Path:
    """
    Returns the project root directory.
    Assumes the project root is the parent of the 'code' directory.
    """
    global _cached_root
    if _cached_root is not None:
        return _cached_root

    current_file = Path(__file__)
    # code/utils/config.py -> code/utils -> code -> project_root
    _cached_root = current_file.parent.parent.parent.resolve()
    return _cached_root

def get_log_path() -> Path:
    """
    Returns the path to the ingestion log file.
    """
    global _cached_log_path
    if _cached_log_path is not None:
        return _cached_log_path

    project_root = get_project_root()
    _cached_log_path = project_root / "data" / "logs" / "ingestion.log"
    return _cached_log_path
