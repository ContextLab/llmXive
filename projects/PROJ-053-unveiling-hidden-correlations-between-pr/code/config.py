import os
import logging
from pathlib import Path
from typing import Optional

# Project Root
_PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Directories
_DATA_DIR = _PROJECT_ROOT / "data"
_RAW_DATA_DIR = _DATA_DIR / "raw"
_PROCESSED_DATA_DIR = _DATA_DIR / "processed"
_RESULTS_DIR = _PROJECT_ROOT / "results"
_MODELS_DIR = _RESULTS_DIR / "models"
_FIGURES_DIR = _RESULTS_DIR / "figures"
_DOCS_DIR = _PROJECT_ROOT / "docs"
_STATE_DIR = _PROJECT_ROOT / "state"
_LOGS_DIR = _PROJECT_ROOT / "logs"
_CONTRACTS_DIR = _PROJECT_ROOT / "contracts"

# Configuration Keys
TIME_LIMIT_SECONDS = 21600  # 6 hours
RANDOM_SEED = 42

# Manual Data Paths
MANUAL_DATA_PATHS = {
    "am_data_csv": _RAW_DATA_DIR / "am_data.csv"
}

# Hardcoded Baseline for Literature Fallback (T031)
LITERATURE_BASELINE_RANKING = {
    'laser_power': 1,
    'scan_speed': 2,
    'layer_thickness': 3
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
    return RANDOM_SEED

def get_time_limit_seconds() -> int:
    return TIME_LIMIT_SECONDS

def ensure_directories():
    """Create all necessary directories if they do not exist."""
    dirs = [
        _DATA_DIR, _RAW_DATA_DIR, _PROCESSED_DATA_DIR,
        _RESULTS_DIR, _MODELS_DIR, _FIGURES_DIR,
        _DOCS_DIR, _STATE_DIR, _LOGS_DIR, _CONTRACTS_DIR
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

def get_logger(name: str = "llmXive") -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger

# Helper to load hardcoded baseline directly from config if needed elsewhere
def get_hardcoded_baseline_ranking() -> dict:
    return LITERATURE_BASELINE_RANKING
