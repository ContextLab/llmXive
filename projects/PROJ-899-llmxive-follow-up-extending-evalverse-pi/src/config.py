"""
Project configuration and path management.
"""
import os
from pathlib import Path
from typing import Dict, Any, Optional

# Constants
PROJECT_NAME = "llmXive-feature-distillation"
RANDOM_SEED = 42

# Paths
_PROJECT_ROOT = Path(__file__).resolve().parent.parent

def get_project_root() -> Path:
    return _PROJECT_ROOT

def get_data_root() -> Path:
    return _PROJECT_ROOT / "data"

def get_state_root() -> Path:
    return _PROJECT_ROOT / "state"

def get_reports_root() -> Path:
    return _PROJECT_ROOT / "reports"

def get_figures_root() -> Path:
    return _PROJECT_ROOT / "figures"

def get_cache_dir() -> Path:
    return get_data_root() / "cache"

def get_raw_data_dir() -> Path:
    return get_data_root() / "raw"

def get_processed_data_dir() -> Path:
    return get_data_root() / "processed"

def ensure_environment() -> None:
    """Ensure all required directories exist."""
    from src.data.config import ensure_directories
    ensure_directories()

def get_config_summary() -> Dict[str, Any]:
    """Return a summary of the current configuration."""
    return {
        "project_root": str(get_project_root()),
        "data_root": str(get_data_root()),
        "state_root": str(get_state_root()),
        "reports_root": str(get_reports_root()),
        "figures_root": str(get_figures_root()),
        "random_seed": RANDOM_SEED,
    }
