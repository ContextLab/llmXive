import logging
import os
from pathlib import Path
from typing import Optional

# Project Root
PROJECT_ROOT = Path(__file__).parent.parent

# Directory Paths
DATA_DIR = PROJECT_ROOT / "data"
DATA_RAW_DIR = DATA_DIR / "raw"
DATA_PROCESSED_DIR = DATA_DIR / "processed"
RESULTS_DIR = PROJECT_ROOT / "results"
SPEC_DIR = PROJECT_ROOT / "specs"
CONTRACTS_DIR = PROJECT_ROOT / "contracts"

# Constants
RANDOM_SEED = 42
BATCH_SIZE = 10  # LLM batch size constraint

# Logging Configuration
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
LOG_LEVEL = logging.INFO
LOG_FILE = RESULTS_DIR / "pipeline.log"

def setup_logging():
    """Configure logging for the project."""
    log_file = LOG_FILE
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    logging.basicConfig(
        level=LOG_LEVEL,
        format=LOG_FORMAT,
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )

def get_path(base_dir: Path, sub_path: str = "") -> Path:
    """Construct a full path from base directory and sub-path."""
    return base_dir / sub_path if sub_path else base_dir

def get_data_path(sub_path: str = "") -> Path:
    """Get path relative to data directory."""
    return get_path(DATA_DIR, sub_path)

def get_processed_path(sub_path: str = "") -> Path:
    """Get path relative to processed data directory."""
    return get_path(DATA_PROCESSED_DIR, sub_path)

def get_results_path(sub_path: str = "") -> Path:
    """Get path relative to results directory."""
    return get_path(RESULTS_DIR, sub_path)
