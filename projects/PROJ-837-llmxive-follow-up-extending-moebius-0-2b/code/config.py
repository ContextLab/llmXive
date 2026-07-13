"""
Configuration management for the Moebius project.
Defines seeds, paths, hyperparameters, and mode flags.
"""
import os
from pathlib import Path
from typing import Literal, Dict, Any

# Project Root
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
CODE_DIR = PROJECT_ROOT / "code"
TESTS_DIR = PROJECT_ROOT / "tests"
SPECS_DIR = PROJECT_ROOT / "specs"
FIGURES_DIR = DATA_DIR / "figures"
RESULTS_DIR = DATA_DIR / "results"
ANNOTATIONS_DIR = DATA_DIR / "annotations"
PROCESSED_DIR = DATA_DIR / "processed"
MASKED_IMAGES_DIR = PROCESSED_DIR / "masked_images"
RAW_DIR = DATA_DIR / "raw"

# Ensure directories exist
(PROCESSED_DIR / "masked_images").mkdir(parents=True, exist_ok=True)
ANNOTATIONS_DIR.mkdir(parents=True, exist_ok=True)
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
RAW_DIR.mkdir(parents=True, exist_ok=True)
FIGURES_DIR.mkdir(parents=True, exist_ok=True)

# Seeds
RANDOM_SEED = 42

# Modes
ModeType = Literal["CI", "Research"]
CURRENT_MODE: ModeType = os.getenv("MOEBIUS_MODE", "CI")  # Default to CI for safety

# Hyperparameters (Defaults)
HYPERPARAMS: Dict[str, Any] = {
    "batch_size": 32,
    "learning_rate": 1e-4,
    "num_epochs": 10,
    "max_rank": 5,
    "min_rank": 1,
    "mask_threshold": 0.5,
    "num_workers": 0,  # CPU-only, 0 workers for simplicity in CI
    "validation_split": 0.1,
    "proxy_threshold": 0.7,  # Pearson r threshold for US4 gate
    "power_threshold": 0.8,  # Statistical power threshold for US3
}

# Paths for specific datasets
DATASET_PATHS: Dict[str, str] = {
    "places365": "mit-places/Places365",
    "celebA": "celebA-HQ",
}

# Logging configuration
LOG_LEVEL = "INFO" if is_ci_mode() else "DEBUG"
LOG_FILE = RESULTS_DIR / "run.log"

def get_mode() -> ModeType:
    """Return the current execution mode."""
    return CURRENT_MODE

def is_ci_mode() -> bool:
    """Return True if running in CI mode (synthetic/decoupled data)."""
    return CURRENT_MODE == "CI"

def is_research_mode() -> bool:
    """Return True if running in Research mode (human-annotated data)."""
    return CURRENT_MODE == "Research"

def get_config_summary() -> Dict[str, Any]:
    """Return a summary of the current configuration for logging."""
    return {
        "mode": CURRENT_MODE,
        "seed": RANDOM_SEED,
        "hyperparams": HYPERPARAMS,
        "paths": {
            "root": str(PROJECT_ROOT),
            "data": str(DATA_DIR),
            "results": str(RESULTS_DIR),
        }
    }