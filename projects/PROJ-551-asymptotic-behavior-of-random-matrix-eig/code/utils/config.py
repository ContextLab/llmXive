import logging
from pathlib import Path
from typing import Dict

def get_project_paths() -> Dict[str, Path]:
    """Returns the standard project directory structure."""
    root = Path(__file__).resolve().parent.parent
    return {
        "root": root,
        "raw": root / "data" / "raw",
        "processed": root / "data" / "processed",
        "logs": root / "data" / "logs",
        "figures": root / "data" / "figures",
    }

def get_outlier_tolerance() -> float:
    """Returns the numerical tolerance for outlier detection."""
    return 1e-10

def ensure_directories(root_path: Path = None):
    """Creates necessary project directories if they don't exist."""
    if root_path is None:
        root_path = Path(__file__).resolve().parent.parent
    
    paths = get_project_paths()
    for path in paths.values():
        path.mkdir(parents=True, exist_ok=True)
