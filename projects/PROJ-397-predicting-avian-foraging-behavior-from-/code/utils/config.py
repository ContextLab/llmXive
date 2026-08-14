import os
from pathlib import Path
from typing import Dict, Any, Optional, List
import numpy as np
import random

# Project root directory
_PROJECT_ROOT = Path(__file__).resolve().parent.parent

def get_project_root() -> Path:
    """Returns the project root directory."""
    return _PROJECT_ROOT

def get_data_dir() -> Path:
    """Returns the data directory."""
    return _PROJECT_ROOT / "data"

def get_raw_data_dir() -> Path:
    """Returns the raw data directory."""
    return get_data_dir() / "raw"

def get_processed_dir() -> Path:
    """Returns the processed data directory."""
    return get_data_dir() / "processed"

def get_models_dir() -> Path:
    """Returns the models directory."""
    return get_data_dir() / "models"

def get_viz_dir() -> Path:
    """Returns the visualization directory."""
    return get_data_dir() / "viz"

def get_figures_dir() -> Path:
    """Returns the figures directory."""
    return get_data_dir() / "figures"

def get_reports_dir() -> Path:
    """Returns the reports directory."""
    return get_data_dir() / "reports"

# Random seed for reproducibility
_SEED = 42

def get_seed() -> int:
    """Returns the random seed."""
    return _SEED

def set_seed(seed: int) -> None:
    """Sets the random seed."""
    global _SEED
    _SEED = seed
    np.random.seed(seed)
    random.seed(seed)

# Model parameters
_MODEL_PARAMS = {
    "n_estimators": 100,
    "max_depth": 10,
    "random_state": _SEED
}

def get_model_params() -> Dict[str, Any]:
    """Returns model parameters."""
    return _MODEL_PARAMS

# Cross-validation parameters
_CV_PARAMS = {
    "n_splits": 5,
    "shuffle": True,
    "random_state": _SEED
}

def get_cv_params() -> Dict[str, Any]:
    """Returns cross-validation parameters."""
    return _CV_PARAMS

# Permutation test parameters
_PERMUTATION_PARAMS = {
    "n_iterations": 1000,
    "random_state": _SEED
}

def get_permutation_params() -> Dict[str, Any]:
    """Returns permutation test parameters."""
    return _PERMUTATION_PARAMS

# Data thresholds
_DATA_THRESHOLDS = {
    "min_observations_per_species": 50,
    "max_species_count": 25
}

def get_data_thresholds() -> Dict[str, int]:
    """Returns data thresholds."""
    return _DATA_THRESHOLDS

# File paths
_FILE_PATHS = {
    "ebd_raw": "raw/ebd_train.parquet",
    "nlcd_raw": "raw/nlcd_2019.zip",
    "guild_mapping": "processed/guild_mapping.csv",
    "top_species": "processed/top_25_species_ids.json",
    "merged_observations": "processed/merged_observations.csv",
    "species_profiles": "processed/species_profiles.csv",
    "model": "models/random_forest.pkl",
    "evaluation_metrics": "models/evaluation_metrics.json"
}

def get_file_paths() -> Dict[str, str]:
    """Returns file paths relative to data directory."""
    return _FILE_PATHS

def ensure_directories() -> None:
    """Ensures all necessary directories exist."""
    dirs = [
        get_raw_data_dir(),
        get_processed_dir(),
        get_models_dir(),
        get_viz_dir(),
        get_figures_dir(),
        get_reports_dir()
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
