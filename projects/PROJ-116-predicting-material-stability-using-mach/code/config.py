import os
import random
from pathlib import Path
from typing import Optional, Dict, Any
import logging

# Project Root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
CODE_DIR = PROJECT_ROOT / "code"
DATA_DIR = PROJECT_ROOT / "data"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"
SPECS_DIR = PROJECT_ROOT / "specs"
TESTS_DIR = PROJECT_ROOT / "tests"

# Data Paths
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
MODELS_DIR = DATA_DIR / "models"

# Output Paths
OUTPUTS_LOGS_DIR = OUTPUTS_DIR / "logs"
OUTPUTS_METRICS_DIR = OUTPUTS_DIR / "metrics"
OUTPUTS_FIGURES_DIR = OUTPUTS_DIR / "figures"

# Configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FILE = os.getenv("LOG_FILE", "pipeline.log")
RANDOM_SEED = int(os.getenv("RANDOM_SEED", "42"))

def set_seed(seed: Optional[int] = None) -> None:
    """Set random seeds for reproducibility."""
    if seed is None:
        seed = RANDOM_SEED
    random.seed(seed)
    np.random.seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)
    logging.info(f"Random seed set to {seed}")

def get_seed() -> int:
    """Get the current random seed."""
    return RANDOM_SEED
