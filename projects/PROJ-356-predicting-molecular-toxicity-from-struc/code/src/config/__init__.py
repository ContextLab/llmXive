"""
Configuration module for the molecular toxicity prediction pipeline.

This module provides environment variable management and path resolution
for the project's data, models, and results directories.
"""

import os
from pathlib import Path
from typing import Optional

# Project root relative to this file (code/src/config -> project root)
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
_CODE_DIR = _PROJECT_ROOT / "code"

# Core directories
DATA_DIR = _CODE_DIR / "data"
RESULTS_DIR = _CODE_DIR / "results"
MODELS_DIR = _CODE_DIR / "models"
CONFIG_DIR = _CODE_DIR / "config"
SRC_DIR = _CODE_DIR / "src"
TESTS_DIR = _CODE_DIR / "tests"

# Default paths for key artifacts
DEFAULT_ALERTS_CONFIG = CONFIG_DIR / "structural_alerts.json"
DEFAULT_DATA_FILE = DATA_DIR / "toxcast_raw.csv"
DEFAULT_PREPROCESSED_FILE = DATA_DIR / "toxcast_processed.csv"
DEFAULT_RULE_MODEL_PATH = MODELS_DIR / "rule_based_model.json"
DEFAULT_LOGISTIC_MODEL_PATH = MODELS_DIR / "logistic_model.joblib"
DEFAULT_METRICS_FILE = RESULTS_DIR / "metrics_baseline.json"
DEFAULT_OOF_FILE = RESULTS_DIR / "oof_predictions_final.json"

def get_env_path(key: str, default: Optional[Path] = None) -> Path:
    """
    Resolve a path from an environment variable or return the default.
    
    Args:
        key: Environment variable name (e.g., 'PROJECT_DATA_DIR')
        default: Fallback Path if env var is not set
    
    Returns:
        Resolved Path object
    
    Raises:
        ValueError: If env var is set but not a valid path
    """
    val = os.getenv(key)
    if val:
        path = Path(val).resolve()
        if not path.exists():
            raise ValueError(f"Environment path {key}={path} does not exist")
        return path
    if default:
        return default.resolve()
    raise ValueError(f"Environment variable {key} is not set and no default provided")

def ensure_dirs() -> None:
    """Create all core directories if they do not exist."""
    for dir_path in [DATA_DIR, RESULTS_DIR, MODELS_DIR, CONFIG_DIR]:
        dir_path.mkdir(parents=True, exist_ok=True)

__all__ = [
    "DATA_DIR",
    "RESULTS_DIR",
    "MODELS_DIR",
    "CONFIG_DIR",
    "SRC_DIR",
    "TESTS_DIR",
    "DEFAULT_ALERTS_CONFIG",
    "DEFAULT_DATA_FILE",
    "DEFAULT_PREPROCESSED_FILE",
    "DEFAULT_RULE_MODEL_PATH",
    "DEFAULT_LOGISTIC_MODEL_PATH",
    "DEFAULT_METRICS_FILE",
    "DEFAULT_OOF_FILE",
    "get_env_path",
    "ensure_dirs",
]