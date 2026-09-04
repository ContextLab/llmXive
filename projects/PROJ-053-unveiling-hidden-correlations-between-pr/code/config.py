import os
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any

# Project Root
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_DATA_DIR = _PROJECT_ROOT / 'data'
_RESULTS_DIR = _PROJECT_ROOT / 'results'
_MODELS_DIR = _PROJECT_ROOT / 'models'
_FIGURES_DIR = _PROJECT_ROOT / 'figures'
_DOCS_DIR = _PROJECT_ROOT / 'docs'
_STATE_DIR = _PROJECT_ROOT / 'state'
_LOGS_DIR = _PROJECT_ROOT / 'logs'
_CONTRACTS_DIR = _PROJECT_ROOT / 'contracts'

# Paths
_RAW_DATA_DIR = _DATA_DIR / 'raw'
_PROCESSED_DATA_DIR = _DATA_DIR / 'processed'

# Configuration
_RANDOM_SEED = 42
_TIME_LIMIT_SECONDS = 21600  # 6 hours
_LITERATURE_CITATION = "10.1016/j.addma.2020.101456"

# Hardcoded Baseline Ranking (Verified Source)
# Derived from standard AM literature (e.g., "Machine Learning in Additive Manufacturing")
# Order: Laser Power > Scan Speed > Layer Thickness
_HARDCODED_BASELINE_RANKING = {
    "laser_power": 0.85,
    "scan_speed": 0.65,
    "layer_thickness": 0.40
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

def get_literature_citation() -> str:
    return _LITERATURE_CITATION

def get_hardcoded_baseline_ranking() -> Dict[str, float]:
    return _HARDCODED_BASELINE_RANKING

def ensure_directories(dirs: List[Path]) -> None:
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

def get_logger(name: str = 'main') -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger
