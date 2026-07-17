"""
Configuration utilities for random seeds, paths, and constants.
"""
import os
import random
from pathlib import Path
from typing import Dict, Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

def get_project_root() -> Path:
    return PROJECT_ROOT

def set_seed(seed: int = 42) -> None:
    random.seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)

def get_config_summary() -> Dict[str, Any]:
    return {
        "project_root": str(PROJECT_ROOT),
        "seed": 42
    }
