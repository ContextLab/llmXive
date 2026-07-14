import os
from pathlib import Path
from typing import Dict, Any, Optional

# Project Root
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Data Directories
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
STRATIFIED_DIR = DATA_DIR / "stratified"
FEATURES_DIR = DATA_DIR / "features"
RESULTS_DIR = DATA_DIR / "results"

# Configuration
MEMORY_LIMIT_GB = 8.0
BATCH_MEMORY_THRESHOLD_GB = 6.0
RANDOM_SEED = 42

def get_data_dir() -> Path:
    return DATA_DIR

def get_raw_dir() -> Path:
    return RAW_DIR

def get_stratified_dir() -> Path:
    return STRATIFIED_DIR

def get_features_dir() -> Path:
    return FEATURES_DIR

def get_results_dir() -> Path:
    return RESULTS_DIR

def get_processed_dir() -> Path:
    return PROCESSED_DIR

def get_memory_limit_gb() -> float:
    return MEMORY_LIMIT_GB

def ensure_directories() -> None:
    """Create all necessary data directories if they don't exist."""
    for dir_path in [DATA_DIR, RAW_DIR, PROCESSED_DIR, STRATIFIED_DIR, FEATURES_DIR, RESULTS_DIR]:
        dir_path.mkdir(parents=True, exist_ok=True)

def get_config_summary() -> Dict[str, Any]:
    return {
        "data_dir": str(DATA_DIR),
        "memory_limit_gb": MEMORY_LIMIT_GB,
        "batch_threshold_gb": BATCH_MEMORY_THRESHOLD_GB,
        "random_seed": RANDOM_SEED,
    }