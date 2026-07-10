"""
Project Configuration Module.
"""
import os
from pathlib import Path
from typing import Optional, Dict, Any

# Project Root
_PROJECT_ROOT = Path(__file__).parent.parent

# Data Directories
_DATA_DIR = _PROJECT_ROOT / "data"
_RAW_DIR = _DATA_DIR / "raw"
_PROCESSED_DIR = _DATA_DIR / "processed"
_VALIDATION_DIR = _DATA_DIR / "validation"

# Configuration
_CONFIG = {
    "seed": 42,
    "dataset_url": "materialsproject/mp-dft-electrolytes",
    "fallback_path": str(_RAW_DIR / "mock_electrolytes.csv"),
    "debug_mode": False
}

def get_project_root() -> Path:
    return _PROJECT_ROOT

def get_data_dir() -> Path:
    return _DATA_DIR

def get_output_dir() -> Path:
    return _DATA_DIR

def get_seed() -> int:
    return _CONFIG["seed"]

def get_dataset_url() -> str:
    return _CONFIG["dataset_url"]

def get_fallback_path() -> str:
    return _CONFIG["fallback_path"]

def is_debug_mode() -> bool:
    return _CONFIG["debug_mode"]

def get_config_summary() -> Dict[str, Any]:
    return {
        "project_root": str(_PROJECT_ROOT),
        "data_dir": str(_DATA_DIR),
        "seed": _CONFIG["seed"],
        "dataset_url": _CONFIG["dataset_url"]
    }

class Config:
    """Configuration class for type hints and static access."""
    project_root = _PROJECT_ROOT
    data_dir = _DATA_DIR
    seed = _CONFIG["seed"]
    dataset_url = _CONFIG["dataset_url"]
    fallback_path = _CONFIG["fallback_path"]
