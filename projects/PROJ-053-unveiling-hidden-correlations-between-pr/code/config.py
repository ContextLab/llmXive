import os
import logging
from pathlib import Path
from typing import Optional

# Project Root
# Assuming the script is run from the project root or we infer it
# For safety, we define the root relative to this file if not set
def get_project_root() -> str:
    """Returns the absolute path to the project root."""
    # If run as a module, __file__ is code/config.py
    current_file = Path(__file__).resolve()
    return str(current_file.parent.parent)

PROJECT_ROOT = get_project_root()

# Directories
DATA_DIR = os.path.join(PROJECT_ROOT, "data")
RAW_DATA_DIR = os.path.join(DATA_DIR, "raw")
PROCESSED_DATA_DIR = os.path.join(DATA_DIR, "processed")
RESULTS_DIR = os.path.join(PROJECT_ROOT, "results")
MODELS_DIR = os.path.join(RESULTS_DIR, "models")
FIGURES_DIR = os.path.join(RESULTS_DIR, "figures")
DOCS_DIR = os.path.join(PROJECT_ROOT, "docs")
STATE_DIR = os.path.join(PROJECT_ROOT, "state")
LOGS_DIR = os.path.join(RESULTS_DIR, "logs")

# Random Seed
RANDOM_SEED = 42

def get_data_dir() -> str:
    return DATA_DIR

def get_raw_data_dir() -> str:
    return RAW_DATA_DIR

def get_processed_data_dir() -> str:
    return PROCESSED_DATA_DIR

def get_results_dir() -> str:
    return RESULTS_DIR

def get_models_dir() -> str:
    return MODELS_DIR

def get_figures_dir() -> str:
    return FIGURES_DIR

def get_docs_dir() -> str:
    return DOCS_DIR

def get_state_dir() -> str:
    return STATE_DIR

def get_logs_dir() -> str:
    return LOGS_DIR

def get_random_seed() -> int:
    return RANDOM_SEED

def ensure_directories(dirs: Optional[list] = None):
    """Ensure all required directories exist."""
    if dirs is None:
        dirs = [DATA_DIR, RAW_DATA_DIR, PROCESSED_DATA_DIR, RESULTS_DIR, 
                MODELS_DIR, FIGURES_DIR, DOCS_DIR, STATE_DIR, LOGS_DIR]
    
    for d in dirs:
        os.makedirs(d, exist_ok=True)

# Logger Setup
def get_logger(name: str = __name__) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger
