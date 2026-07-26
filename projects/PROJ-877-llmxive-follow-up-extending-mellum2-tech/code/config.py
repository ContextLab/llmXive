"""
Configuration management for llmXive follow-up project.
Handles paths, random seeds, and hyperparameter defaults.
"""
import os
import random
from pathlib import Path
from typing import Any, Dict

# Project Root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
CODE_DIR = PROJECT_ROOT / "code"
DATA_DIR = PROJECT_ROOT / "data"
TESTS_DIR = PROJECT_ROOT / "tests"
SPECS_DIR = PROJECT_ROOT / "specs"

# Data Subdirectories
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
RESULTS_DIR = DATA_DIR / "results"

# Random Seeds
DEFAULT_SEED = 42

# Hyperparameter Defaults
HYPERPARAMS: Dict[str, Any] = {
    "ngram_order": 5,
    "max_chunk_tokens": 512,
    "timeout_seconds": 300,
    "max_retries": 3,
    "backoff_factor": 2,
    "batch_size": 8,
    "num_workers": 4,
}

# Statistical Power Defaults
STAT_POWER_DEFAULTS: Dict[str, Any] = {
    "alpha": 0.05,
    "power": 0.80,
    "effect_size_guess": 0.3,  # Medium effect size
}

def set_seed(seed: int = DEFAULT_SEED) -> None:
    """Set global random seeds for reproducibility."""
    random.seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)
    # Note: torch/numpy seeds set in specific modules where needed

def ensure_dirs() -> None:
    """Create all required project directories if they don't exist."""
    dirs = [
        CODE_DIR,
        DATA_DIR,
        TESTS_DIR,
        SPECS_DIR,
        RAW_DIR,
        PROCESSED_DIR,
        RESULTS_DIR,
        PROJECT_ROOT / "figures",
        PROJECT_ROOT / "docs",
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

def get_config() -> Dict[str, Any]:
    """Return a complete configuration dictionary."""
    return {
        "paths": {
            "root": str(PROJECT_ROOT),
            "code": str(CODE_DIR),
            "data": str(DATA_DIR),
            "raw": str(RAW_DIR),
            "processed": str(PROCESSED_DIR),
            "results": str(RESULTS_DIR),
            "tests": str(TESTS_DIR),
        },
        "seed": DEFAULT_SEED,
        "hyperparams": HYPERPARAMS,
        "stat_power": STAT_POWER_DEFAULTS,
    }
