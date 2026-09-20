import os
import random
from pathlib import Path
from typing import Dict, Any, Optional, List
import numpy as np

# Project Root Configuration
# In a real deployment, this might be set via environment variable
# For this pipeline, we assume the project root is the parent of the 'code' directory
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# Constants
RANDOM_SEED = 42

def get_project_root() -> Path:
    """Return the project root directory."""
    return _PROJECT_ROOT

def get_code_root() -> Path:
    """Return the code directory."""
    return _PROJECT_ROOT / "code"

def get_data_dir() -> Path:
    """Return the data directory."""
    return _PROJECT_ROOT / "data"

def get_raw_data_dir() -> Path:
    """Return the raw data directory."""
    return get_data_dir() / "raw"

def get_processed_dir() -> Path:
    """Return the processed data directory."""
    return get_data_dir() / "processed"

def get_models_dir() -> Path:
    """Return the models directory."""
    return _PROJECT_ROOT / "models"

def get_viz_dir() -> Path:
    """Return the visualization directory."""
    return _PROJECT_ROOT / "viz"

def get_figures_dir() -> Path:
    """Return the figures directory."""
    return get_viz_dir() / "figures"

def get_reports_dir() -> Path:
    """Return the reports directory."""
    return _PROJECT_ROOT / "docs" / "results"

def get_metadata_file() -> Path:
    """Return the path to the metadata.yaml file."""
    return get_data_dir() / "metadata.yaml"

def get_seed() -> int:
    """Return the random seed."""
    return RANDOM_SEED

def set_seed(seed: Optional[int] = None):
    """Set random seeds for reproducibility."""
    if seed is None:
        seed = RANDOM_SEED
    random.seed(seed)
    np.random.seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)

def get_model_params() -> Dict[str, Any]:
    """Return default model parameters."""
    return {
        "n_estimators": 100,
        "max_depth": None,
        "random_state": RANDOM_SEED
    }

def get_cv_params() -> Dict[str, Any]:
    """Return cross-validation parameters."""
    return {
        "n_splits": 5,
        "shuffle": True,
        "random_state": RANDOM_SEED
    }

def get_permutation_params() -> Dict[str, Any]:
    """Return permutation test parameters."""
    return {
        "n_permutations": 1000,
        "random_state": RANDOM_SEED
    }

def get_data_thresholds() -> Dict[str, Any]:
    """Return data filtering thresholds."""
    return {
        "min_observations_per_species": 50,
        "top_species_count": 25
    }

def get_file_path(relative_path: str) -> Path:
    """Get a full path from a relative path string."""
    return _PROJECT_ROOT / relative_path

def get_file_paths(relative_paths: List[str]) -> List[Path]:
    """Get full paths from a list of relative path strings."""
    return [_PROJECT_ROOT / p for p in relative_paths]

def ensure_directories():
    """Ensure all required directories exist."""
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
