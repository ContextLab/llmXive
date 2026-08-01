import os
from pathlib import Path
from typing import Dict, Any, Optional

# Project Configuration
PROJECT_NAME = "PROJ-899-llmxive-follow-up-extending-evalverse-pi"
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_ROOT = PROJECT_ROOT / "data"
STATE_ROOT = PROJECT_ROOT / "state"
REPORTS_ROOT = PROJECT_ROOT / "reports"
FIGURES_ROOT = PROJECT_ROOT / "figures"
CACHE_DIR = DATA_ROOT / "cache"
RAW_DATA_DIR = DATA_ROOT / "raw"
PROCESSED_DATA_DIR = DATA_ROOT / "processed"
RESULTS_DIR = DATA_ROOT / "results"

# Dataset Configuration (referenced by T009b)
DATASET_DOI = "10.5281/zenodo.1234567"  # Placeholder DOI
DATASET_URL = "https://zenodo.org/record/1234567/files/evalverse.tar.gz"  # Placeholder URL

# Random Seeds
RANDOM_SEED = 42
NUMPY_SEED = 42

# Thresholds
CORRELATION_THRESHOLD = 0.85
VLM_REQUIRED_LOWER_CI = 0.70
ERROR_RATE_THRESHOLD = 0.05

def get_project_root() -> Path:
    return PROJECT_ROOT

def get_data_root() -> Path:
    return DATA_ROOT

def get_state_root() -> Path:
    return STATE_ROOT

def get_reports_root() -> Path:
    return REPORTS_ROOT

def get_figures_root() -> Path:
    return FIGURES_ROOT

def get_cache_dir() -> Path:
    return CACHE_DIR

def get_raw_data_dir() -> Path:
    return RAW_DATA_DIR

def get_processed_data_dir() -> Path:
    return PROCESSED_DATA_DIR

def ensure_environment():
    """Ensure all required directories exist."""
    dirs = [
        DATA_ROOT, STATE_ROOT, REPORTS_ROOT, FIGURES_ROOT, CACHE_DIR,
        RAW_DATA_DIR, PROCESSED_DATA_DIR, RESULTS_DIR
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

def get_config_summary() -> Dict[str, Any]:
    return {
        "project_root": str(PROJECT_ROOT),
        "data_root": str(DATA_ROOT),
        "state_root": str(STATE_ROOT),
        "reports_root": str(REPORTS_ROOT),
        "figures_root": str(FIGURES_ROOT),
        "dataset_doi": DATASET_DOI,
        "random_seed": RANDOM_SEED
    }
