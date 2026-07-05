import os
import random
from pathlib import Path
from typing import Any, Dict, Optional

# Project root is assumed to be the directory containing this file's parent
# Adjust based on actual project structure
PROJECT_ROOT = Path(__file__).resolve().parent.parent

def get_path(relative_path: str) -> Path:
    """Get absolute path relative to project root."""
    return PROJECT_ROOT / relative_path

def set_seed(seed: int = 42) -> None:
    """Set random seed for reproducibility."""
    random.seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)

def ensure_directories() -> None:
    """Create necessary directory structure."""
    dirs = [
        "data/raw",
        "data/processed",
        "data/primes",
        "data/targets",
        "code",
        "tests",
        "state/projects/PROJ-345"
    ]
    for d in dirs:
        get_path(d).mkdir(parents=True, exist_ok=True)
