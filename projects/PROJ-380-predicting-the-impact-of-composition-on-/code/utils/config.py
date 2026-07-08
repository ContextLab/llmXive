"""
Configuration module for the BMG Shear Modulus prediction pipeline.

This module provides:
- Random seed management for reproducibility
- Path constants for the project directory structure
- Hyperparameter defaults and other configuration values
"""
import os
import random
from pathlib import Path
from typing import Dict, Any, Optional
import numpy as np

# Project root is assumed to be the parent of the 'code' directory
# If running as a script, we try to resolve relative to __file__
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# === Path Constants ===
# Data directories
DATA_DIR = _PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
ARTIFACTS_DIR = DATA_DIR / "artifacts"
FIGURES_DIR = DATA_DIR / "figures"

# Code directories
CODE_DIR = _PROJECT_ROOT / "code"
DATA_MODULE_DIR = CODE_DIR / "data"
MODELS_MODULE_DIR = CODE_DIR / "models"
VIZ_MODULE_DIR = CODE_DIR / "viz"
UTILS_MODULE_DIR = CODE_DIR / "utils"

# Specs and Contracts
SPECS_DIR = _PROJECT_ROOT / "specs"
CONTRACTS_DIR = _PROJECT_ROOT / "contracts"

# State and Provenance
STATE_DIR = _PROJECT_ROOT / "state"
PROJECTS_STATE_DIR = STATE_DIR / "projects"

# Output defaults
DEFAULT_OUTPUT_CSV = PROCESSED_DATA_DIR / "bmg_processed.csv"
DEFAULT_MODEL_REPORT = ARTIFACTS_DIR / "model_report.json"
DEFAULT_IMPORTANCE_REPORT = ARTIFACTS_DIR / "importance_report.json"

# === Random Seed Management ===
# Default seed for reproducibility across experiments
DEFAULT_SEED = 42

def set_random_seed(seed: Optional[int] = None) -> None:
    """
    Set random seeds for reproducibility across Python, NumPy, and random modules.
    
    Args:
        seed: The random seed to use. Defaults to DEFAULT_SEED if None.
    """
    if seed is None:
        seed = DEFAULT_SEED
    
    random.seed(seed)
    np.random.seed(seed)
    
    # Optional: If torch/tensorflow are used later, they can be seeded here
    # try:
    #     import torch
    #     torch.manual_seed(seed)
    #     if torch.cuda.is_available():
    #         torch.cuda.manual_seed_all(seed)
    # except ImportError:
    #     pass

def get_paths() -> Dict[str, Path]:
    """
    Return a dictionary of all major path constants for convenience.
    
    Returns:
        Dict mapping logical names to Path objects.
    """
    return {
        "project_root": _PROJECT_ROOT,
        "data": DATA_DIR,
        "raw": RAW_DATA_DIR,
        "processed": PROCESSED_DATA_DIR,
        "artifacts": ARTIFACTS_DIR,
        "figures": FIGURES_DIR,
        "code": CODE_DIR,
        "specs": SPECS_DIR,
        "contracts": CONTRACTS_DIR,
        "state": STATE_DIR,
        "projects_state": PROJECTS_STATE_DIR,
    }

def ensure_directories() -> None:
    """
    Create all required data directories if they do not exist.
    
    This should be called once at the start of the pipeline to ensure
    the file system structure is ready for reading/writing.
    """
    for path in get_paths().values():
        if path != _PROJECT_ROOT:
            path.mkdir(parents=True, exist_ok=True)

# === Hyperparameter Defaults ===
MODEL_CONFIG = {
    "linear_regression": {
        "fit_intercept": True,
        "normalize": False,
    },
    "random_forest": {
        "n_estimators": 100,
        "max_depth": None,
        "min_samples_split": 2,
        "min_samples_leaf": 1,
        "random_state": DEFAULT_SEED,
    },
    "gradient_boosting": {
        "n_estimators": 100,
        "learning_rate": 0.1,
        "max_depth": 3,
        "random_state": DEFAULT_SEED,
    }
}

GRID_SEARCH_CONFIG = {
    "max_combinations": 50,
    "cv_folds": 5,
    "scoring": "r2",
}

FEATURE_CONFIG = {
    "vif_threshold": 5.0,
    "descriptors": ["delta", "delta_hmix", "vec", "delta_chi"],
}

SPLIT_CONFIG = {
    "test_size": 0.2,
    "random_state": DEFAULT_SEED,
    "stratify_by": "alloy_family",
}

STATISTICAL_TEST_CONFIG = {
    "primary_method": "corrected_resampled_t_test",
    "fallback_method": "wilcoxon_signed_rank",
    "bayes_factor_fallback": True,
    "confidence_level": 0.95,
}

# === Initialization ===
# Ensure directories exist when the module is imported (optional but convenient)
# Uncomment if automatic directory creation is desired on import
# ensure_directories()