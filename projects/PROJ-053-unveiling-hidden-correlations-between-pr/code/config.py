import os
import logging
from pathlib import Path
from typing import Optional

# Project Root
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Directories
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
RESULTS_DIR = PROJECT_ROOT / "results"
MODELS_DIR = RESULTS_DIR / "models"
FIGURES_DIR = RESULTS_DIR / "figures"
DOCS_DIR = PROJECT_ROOT / "docs"
STATE_DIR = PROJECT_ROOT / "state"
LOGS_DIR = PROJECT_ROOT / "logs"

# Random Seed
RANDOM_SEED = 42

# Performance Thresholds
TIME_LIMIT_SECONDS = 21600  # 6 hours

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

def get_random_seed() -> int:
    return RANDOM_SEED

def get_time_limit_seconds() -> int:
    return TIME_LIMIT_SECONDS

def ensure_directories() -> None:
    """Ensure all required directories exist."""
    dirs = [
        DATA_DIR, RAW_DATA_DIR, PROCESSED_DATA_DIR,
        RESULTS_DIR, MODELS_DIR, FIGURES_DIR,
        DOCS_DIR, STATE_DIR, LOGS_DIR
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

def get_logger(name: str = "config") -> logging.Logger:
    return logging.getLogger(name)
