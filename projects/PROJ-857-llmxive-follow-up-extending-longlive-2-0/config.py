import os
import sys
from pathlib import Path
from typing import Final, List, Dict, Any

# Project Root
PROJECT_ROOT = Path(__file__).parent.parent

# Constants
SEED: Final[int] = 42
BIT_WIDTHS: Final[List[int]] = [2, 4, 8]
MAX_MEMORY_GB: Final[float] = 7.0
MAX_DISK_GB: Final[float] = 14.0

# Paths Configuration
PATHS: Final[Dict[str, str]] = {
    "data_dir": str(PROJECT_ROOT / "data"),
    "code_dir": str(PROJECT_ROOT / "code"),
    "results_dir": str(PROJECT_ROOT / "data" / "results"),
    "figures_dir": str(PROJECT_ROOT / "data" / "figures"),
    "cache_dir": str(PROJECT_ROOT / "data" / "cache"),
}

def get_path_str(key: str) -> str:
    """Retrieves a path string from the PATHS configuration."""
    if key not in PATHS:
        raise KeyError(f"Path key '{key}' not found in configuration.")
    return PATHS[key]

def ensure_dirs_exist(paths: List[Path]) -> None:
    """Ensures that the given directories exist, creating them if necessary."""
    for p in paths:
        os.makedirs(p, exist_ok=True)
