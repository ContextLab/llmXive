import os
import random
from pathlib import Path
from typing import Dict, Any, Optional, List
import numpy as np

# Project root directory
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if not _PROJECT_ROOT.exists():
    # Fallback for different execution contexts if necessary
    _PROJECT_ROOT = Path.cwd()

# Constants
RANDOM_SEED = 42
BUFFER_SIZE = 100  # meters
N_PERMUTATIONS = 1000
EBD_URL = "s3://ebird-data/ebd_release/"
NLCD_URL = "https://www.usgs.gov/landsat-missions/landsat-collection2-land-cover-data"

def get_project_root() -> Path:
    return _PROJECT_ROOT

def get_code_root() -> Path:
    return _PROJECT_ROOT / "code"

def get_data_dir() -> Path:
    return _PROJECT_ROOT / "data"

def get_raw_data_dir() -> Path:
    return get_data_dir() / "raw"

def get_processed_dir() -> Path:
    return get_data_dir() / "processed"

def get_models_dir() -> Path:
    return _PROJECT_ROOT / "models"

def get_viz_dir() -> Path:
    return _PROJECT_ROOT / "viz"

def get_figures_dir() -> Path:
    return get_viz_dir() / "figures"

def get_reports_dir() -> Path:
    return _PROJECT_ROOT / "docs" / "results"

def get_metadata_file() -> Path:
    return get_data_dir() / "metadata.yaml"

def get_seed() -> int:
    return RANDOM_SEED

def set_seed(seed: int):
    """Set random seeds for reproducibility."""
    random.seed(seed)
    np.random.seed(seed)
    if 'torch' in sys.modules:
        import torch
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)

def get_model_params() -> Dict[str, Any]:
    return {
        'n_estimators': 100,
        'max_depth': None,
        'random_state': RANDOM_SEED
    }

def get_cv_params() -> Dict[str, Any]:
    return {
        'n_splits': 5,
        'shuffle': True,
        'random_state': RANDOM_SEED
    }

def get_permutation_params() -> Dict[str, Any]:
    return {
        'n_permutations': N_PERMUTATIONS,
        'random_state': RANDOM_SEED
    }

def get_data_thresholds() -> Dict[str, Any]:
    return {
        'min_observations_per_species': 50
    }

def get_file_path(name: str, category: str = 'processed') -> Path:
    """Helper to get file paths."""
    if category == 'raw':
        return get_raw_data_dir() / name
    elif category == 'processed':
        return get_processed_dir() / name
    elif category == 'models':
        return get_models_dir() / name
    else:
        raise ValueError(f"Unknown category: {category}")

def get_file_paths() -> Dict[str, Path]:
    return {
        'ebd_train': get_raw_data_dir() / 'ebd_train.parquet',
        'nlcd_zip': get_raw_data_dir() / 'nlcd_2019.zip',
        'guild_source': get_raw_data_dir() / 'guild_source.csv',
        'guild_mapping': get_processed_dir() / 'guild_mapping.csv',
        'species_counts': get_processed_dir() / 'species_counts.json',
        'top_species': get_processed_dir() / 'top_species_ids.json',
        'filtered_ebd': get_processed_dir() / 'filtered_ebd.csv',
        'merged_observations': get_processed_dir() / 'merged_observations.csv',
        'species_profiles': get_processed_dir() / 'species_profiles.csv',
        'model': get_models_dir() / 'random_forest.pkl',
        'metrics': get_models_dir() / 'training_metrics.json',
        'cv_predictions': get_models_dir() / 'cv_predictions.json',
        'null_distribution': get_models_dir() / 'null_distribution.npy',
        'evaluation_results': get_models_dir() / 'evaluation_results.json'
    }

def ensure_directories():
    """Ensure all required directories exist."""
    dirs = [
        get_raw_data_dir(),
        get_processed_dir(),
        get_models_dir(),
        get_figures_dir(),
        get_reports_dir()
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

def get_logger(name: str = __name__):
    import logging
    return logging.getLogger(name)

# Import sys for torch check if needed, but keep it minimal
import sys
