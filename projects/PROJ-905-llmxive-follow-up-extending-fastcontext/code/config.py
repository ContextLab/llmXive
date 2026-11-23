import os
from pathlib import Path
from typing import Any, Dict, Optional

# Project root is assumed to be the parent of the 'code' directory
# This allows the script to run from 'code' or from the project root
def _get_project_root() -> Path:
    current_file = Path(__file__).resolve()
    return current_file.parent.parent

PROJECT_ROOT = _get_project_root()

def get_path(*subdirs: str) -> Path:
    """Construct a path relative to the project root."""
    path = PROJECT_ROOT
    for subdir in subdirs:
        path = path / subdir
    return path

def ensure_directories(paths: list) -> None:
    """Create directories if they don't exist."""
    for p in paths:
        if isinstance(p, str):
            p = Path(p)
        p.mkdir(parents=True, exist_ok=True)

def get_config_dict() -> Dict[str, Any]:
    """Return configuration dictionary including paths and weights."""
    return {
        'project_root': str(PROJECT_ROOT),
        'weights': {
            'w1': 0.5,
            'w2': 0.5
        },
        'thresholds': {
            'regularity_threshold': 0.5,
            'precision_threshold': 0.9
        }
    }
