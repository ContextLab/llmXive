"""
Configuration constants and utilities for the llmXive project.
"""
import os
from pathlib import Path
from typing import Dict, Any, Optional

# Project Root
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Directories
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
STATE_DIR = DATA_DIR / "state"
FIGURES_DIR = DATA_DIR / "figures"
REPORTS_DIR = DATA_DIR / "reports"

CODE_DIR = PROJECT_ROOT / "src"
TESTS_DIR = PROJECT_ROOT / "tests"
SPECS_DIR = PROJECT_ROOT / "specs"

# Random Seeds
RANDOM_SEED = 42
NP_SEED = 42
TORCH_SEED = 42  # If PyTorch is used later

# Thresholds
CORRELATION_THRESHOLD_FEATURE_SUFFICIENT = 0.85
CORRELATION_THRESHOLD_VLM_REQUIRED = 0.70
ERROR_RATE_THRESHOLD = 0.05

# Performance Constraints
MAX_MEMORY_GB = 7.0
MAX_TOTAL_HOURS = 6.0

# Dataset Specifics
EVALVERSE_ZENODO_ID = "10066666"

def ensure_environment() -> bool:
    """
    Ensure all required environment variables and directories are set up.
    Returns True if successful, raises an error otherwise.
    """
    import sys
    from src.utils import ensure_directories, get_logger
    
    logger = get_logger(__name__)
    
    # Ensure directories
    dirs = [RAW_DATA_DIR, PROCESSED_DATA_DIR, STATE_DIR, FIGURES_DIR, REPORTS_DIR]
    ensure_directories(dirs)
    
    # Check for critical environment variables if any
    # e.g., API keys for external services
    # os.environ.get('SOME_API_KEY')
    
    logger.info("Environment setup verified.")
    return True

def get_config_summary() -> Dict[str, Any]:
    """Return a summary of the current configuration."""
    return {
        "project_root": str(PROJECT_ROOT),
        "data_dir": str(DATA_DIR),
        "random_seed": RANDOM_SEED,
        "correlation_thresholds": {
            "feature_sufficient": CORRELATION_THRESHOLD_FEATURE_SUFFICIENT,
            "vlm_required": CORRELATION_THRESHOLD_VLM_REQUIRED
        },
        "performance_constraints": {
            "max_memory_gb": MAX_MEMORY_GB,
            "max_total_hours": MAX_TOTAL_HOURS
        }
    }
