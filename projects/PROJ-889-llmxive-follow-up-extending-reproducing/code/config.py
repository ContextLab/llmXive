"""
Configuration module for the llmXive project.
"""
import os
from pathlib import Path
from typing import Optional

def get_project_root() -> Path:
    """
    Returns the root directory of the project.
    Assumes the project root is the parent of the 'code' directory.
    """
    current_file = Path(__file__).resolve()
    code_dir = current_file.parent
    return code_dir.parent

def ensure_paths_exist():
    """
    Ensures that required directory structures exist.
    Creates data/raw, data/processed, tests, etc. if missing.
    """
    root = get_project_root()
    dirs = [
        root / "data" / "raw",
        root / "data" / "processed",
        root / "tests" / "unit",
        root / "tests" / "integration",
        root / "contracts",
        root / "figures"
    ]
    
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

# Hyperparameters and thresholds
WINDOW_SIZE: int = 20
MIN_SAMPLES_ZSCORE: int = 5
DYNAMIC_THRESHOLD_MULTIPLIER: float = 3.0
CORRELATION_THRESHOLD: float = 0.8
