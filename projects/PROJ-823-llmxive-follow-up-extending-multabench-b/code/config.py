"""
Global configuration and paths for the llmXive pipeline.
"""
import os
import random
from pathlib import Path
from typing import List

# Project Root
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Directory Definitions
DATA_DIR = PROJECT_ROOT / "data"
CODE_DIR = PROJECT_ROOT / "code"
TESTS_DIR = PROJECT_ROOT / "tests"
ARTIFACTS_DIR = DATA_DIR / "artifacts"
PROCESSED_DIR = DATA_DIR / "processed"
RAW_DIR = DATA_DIR / "raw"
FIGURES_DIR = DATA_DIR / "figures"
LOGS_DIR = DATA_DIR / "logs"
STATE_DIR = PROJECT_ROOT / "state" / "projects"

# Configuration Dictionary
CONFIG = {
    "random_seed": 42,
    "sensitivity_seeds": [42, 123, 456, 789, 101112],
    "device": "cpu",
    "batch_size": 8,
    "max_workers": 4,
}

# Random Seeds for Reproducibility
RANDOM_SEED = 42
# Explicitly pinned set of sensitivity seeds to assess initialization variability
SENSITIVITY_SEEDS: List[int] = [42, 123, 456, 789, 101112]

def ensure_directories():
    """Ensure all required directories exist."""
    for d in [DATA_DIR, CODE_DIR, TESTS_DIR, ARTIFACTS_DIR, PROCESSED_DIR, RAW_DIR, FIGURES_DIR, LOGS_DIR, STATE_DIR]:
        d.mkdir(parents=True, exist_ok=True)

def get_data_path(filename: str) -> Path:
    """Get full path for a file in data/raw."""
    return RAW_DIR / filename

def get_processed_path(filename: str) -> Path:
    """Get full path for a file in data/processed."""
    return PROCESSED_DIR / filename

def get_artifact_path(filename: str) -> Path:
    """Get full path for a file in data/artifacts."""
    return ARTIFACTS_DIR / filename

def set_seed(seed: int = RANDOM_SEED):
    """Set random seeds for reproducibility."""
    random.seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)
    try:
        import numpy as np
        np.random.seed(seed)
    except ImportError:
        pass
    try:
        import torch
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed(seed)
            torch.cuda.manual_seed_all(seed)
    except ImportError:
        pass