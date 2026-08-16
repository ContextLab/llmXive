import os
import logging
from pathlib import Path
from typing import Optional, List

# Project Root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROJECT_NAME = "PROJ-053-unveiling-hidden-correlations-between-pr"

# Directory Paths
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
RESULTS_DIR = PROJECT_ROOT / "results"
MODELS_DIR = PROJECT_ROOT / "models"
FIGURES_DIR = PROJECT_ROOT / "figures"
DOCS_DIR = PROJECT_ROOT / "docs"
STATE_DIR = PROJECT_ROOT / "state"
LOGS_DIR = PROJECT_ROOT / "logs"
CONTRACTS_DIR = PROJECT_ROOT / "contracts"

# Configuration
RANDOM_SEED = 42
TIME_LIMIT_SECONDS = 21600

# Hardcoded Baseline for T031 (Literature Baseline)
# This is the fallback if no user-provided baseline exists.
HARDCODED_BASELINE_RANKING = {
    "rankings": {
        "laser_power": 1,
        "scan_speed": 2,
        "layer_thickness": 3
    }
}

def get_project_root() -> Path:
    return PROJECT_ROOT

def get_data_dir() -> Path:
    return DATA_DIR

def get_raw_data_dir() -> Path:
    return RAW_DATA_DIR

def get_processed_data_dir() -> Path:
    return PROCESSED_DATA_DIR

def get_results_dir() -> Path:
    return RESULTS_DIR

def get_models_dir() -> Path:
    return MODELS_DIR

def get_figures_dir() -> Path:
    return FIGURES_DIR

def get_docs_dir() -> Path:
    return DOCS_DIR

def get_state_dir() -> Path:
    return STATE_DIR

def get_logs_dir() -> Path:
    return LOGS_DIR

def get_contracts_dir() -> Path:
    return CONTRACTS_DIR

def get_random_seed() -> int:
    return RANDOM_SEED

def get_time_limit_seconds() -> int:
    return TIME_LIMIT_SECONDS

def get_hardcoded_baseline_ranking() -> dict:
    return HARDCODED_BASELINE_RANKING

def ensure_directories():
    """Create all required directories if they do not exist."""
    dirs = [
        DATA_DIR, RAW_DATA_DIR, PROCESSED_DATA_DIR, RESULTS_DIR,
        MODELS_DIR, FIGURES_DIR, DOCS_DIR, STATE_DIR, LOGS_DIR, CONTRACTS_DIR
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

def get_logger(name: str = "pipeline") -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger
