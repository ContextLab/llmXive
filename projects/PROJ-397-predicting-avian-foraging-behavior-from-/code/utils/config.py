import os
import random
from pathlib import Path
from typing import Dict, Any, Optional, List
import numpy as np

# Project Root
# The project root is assumed to be the parent of the 'code' directory
# or explicitly set via environment variable.
_PROJECT_ROOT = Path(os.environ.get("PROJECT_ROOT", Path(__file__).parent.parent.parent))

def get_project_root() -> Path:
    """Returns the absolute path to the project root."""
    return _PROJECT_ROOT.resolve()

def get_data_dir() -> Path:
    """Returns the path to the data directory."""
    return get_project_root() / "data"

def get_raw_data_dir() -> Path:
    """Returns the path to the raw data directory."""
    return get_data_dir() / "raw"

def get_processed_dir() -> Path:
    """Returns the path to the processed data directory."""
    return get_data_dir() / "processed"

def get_models_dir() -> Path:
    """Returns the path to the models directory."""
    return get_project_root() / "models"

def get_viz_dir() -> Path:
    """Returns the path to the viz directory."""
    return get_project_root() / "viz"

def get_figures_dir() -> Path:
    """Returns the path to the figures directory."""
    return get_viz_dir() / "figures"

def get_reports_dir() -> Path:
    """Returns the path to the reports directory."""
    return get_viz_dir() / "reports"

def get_metadata_file() -> Path:
    """Returns the path to the metadata.yaml file."""
    return get_data_dir() / "metadata.yaml"

def ensure_directories():
    """Creates all required directories if they don't exist."""
    dirs = [
        get_data_dir(),
        get_raw_data_dir(),
        get_processed_dir(),
        get_models_dir(),
        get_viz_dir(),
        get_figures_dir(),
        get_reports_dir()
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

# Random Seeds
_SEED = 42

def get_seed() -> int:
    return _SEED

def set_seed(seed: int):
    global _SEED
    _SEED = seed
    random.seed(seed)
    np.random.seed(seed)

# Model Parameters
def get_model_params() -> Dict[str, Any]:
    return {
        "n_estimators": 100,
        "max_depth": None,
        "random_state": get_seed(),
        "n_jobs": -1
    }

def get_cv_params() -> Dict[str, Any]:
    return {
        "cv_folds": 5,
        "stratify": True
    }

def get_permutation_params() -> Dict[str, Any]:
    return {
        "n_permutations": 1000,
        "random_state": get_seed()
    }

# Data Thresholds
def get_data_thresholds() -> Dict[str, Any]:
    return {
        "min_observations_per_species": 50,
        "top_species_count": 25
    }

# File Paths
def get_file_paths() -> Dict[str, Path]:
    return {
        "ebd_train": get_raw_data_dir() / "ebd_train.csv",
        "nlcd_2019": get_raw_data_dir() / "nlcd_2019.zip",
        "guild_mapping": get_processed_dir() / "guild_mapping.csv",
        "top_species": get_processed_dir() / "top_25_species_ids.json",
        "merged_observations": get_processed_dir() / "merged_observations.csv",
        "species_profiles": get_processed_dir() / "species_profiles.csv",
        "model": get_models_dir() / "random_forest.pkl",
        "metrics": get_models_dir() / "training_metrics.json"
    }

def get_file_path(name: str) -> Path:
    paths = get_file_paths()
    if name not in paths:
        raise ValueError(f"Unknown file name: {name}")
    return paths[name]
