import os
import logging
from pathlib import Path
from typing import Optional, List

# Project root
_PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Directories
_DATA_DIR = _PROJECT_ROOT / "data"
_RAW_DATA_DIR = _DATA_DIR / "raw"
_PROCESSED_DATA_DIR = _DATA_DIR / "processed"
_RESULTS_DIR = _PROJECT_ROOT / "results"
_MODELS_DIR = _PROJECT_ROOT / "models"
_FIGURES_DIR = _PROJECT_ROOT / "figures"
_DOCS_DIR = _PROJECT_ROOT / "docs"
_STATE_DIR = _PROJECT_ROOT / "state"
_LOGS_DIR = _PROJECT_ROOT / "logs"
_CONTRACTS_DIR = _PROJECT_ROOT / "contracts"

# Configuration
_RANDOM_SEED = 42
_TIME_LIMIT_SECONDS = 21600  # 6 hours
_HARDCODED_BASELINE_RANKING = ["laser_power", "scan_speed", "layer_thickness"]

# Manual data paths
MANUAL_DATA_PATHS = {
    "raw": _RAW_DATA_DIR / "am_data.csv"
}

def get_project_root() -> Path:
    return _PROJECT_ROOT

def get_data_dir() -> Path:
    return _DATA_DIR

def get_raw_data_dir() -> Path:
    return _RAW_DATA_DIR

def get_processed_data_dir() -> Path:
    return _PROCESSED_DATA_DIR

def get_results_dir() -> Path:
    return _RESULTS_DIR

def get_models_dir() -> Path:
    return _MODELS_DIR

def get_figures_dir() -> Path:
    return _FIGURES_DIR

def get_docs_dir() -> Path:
    return _DOCS_DIR

def get_state_dir() -> Path:
    return _STATE_DIR

def get_logs_dir() -> Path:
    return _LOGS_DIR

def get_contracts_dir() -> Path:
    return _CONTRACTS_DIR

def get_random_seed() -> int:
    return _RANDOM_SEED

def get_time_limit_seconds() -> int:
    return _TIME_LIMIT_SECONDS

def get_hardcoded_baseline_ranking() -> List[str]:
    return _HARDCODED_BASELINE_RANKING

def ensure_directories() -> None:
    """Create all required directories if they don't exist."""
    dirs = [
        _DATA_DIR, _RAW_DATA_DIR, _PROCESSED_DATA_DIR, _RESULTS_DIR,
        _MODELS_DIR, _FIGURES_DIR, _DOCS_DIR, _STATE_DIR, _LOGS_DIR,
        _CONTRACTS_DIR
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

def get_logger(name: str, log_file: Optional[str] = None) -> logging.Logger:
    """Get a logger instance."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        if log_file:
            fh = logging.FileHandler(log_file)
            fh.setLevel(logging.INFO)
            logger.addHandler(fh)
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        logger.addHandler(ch)
    return logger
