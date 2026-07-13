"""
Configuration module for the sleep quality prediction pipeline.
Defines paths, seeds, and hyperparameters.
"""
import os
from pathlib import Path
from typing import Dict, Any

# Project root
PROJECT_ROOT = Path(__file__).parent.parent

# Seeds
SEED = 42

def get_paths() -> Dict[str, Union[Path, str]]:
    """
    Get all required paths for the project.
    
    Returns:
        Dictionary of paths
    """
    base = PROJECT_ROOT
    paths = {
        'root': base,
        'code_dir': base / 'code',
        'data_dir': base / 'data',
        'raw_dir': base / 'data' / 'raw' / 'behavioral',
        'processed_dir': base / 'data' / 'processed',
        'results_dir': base / 'data' / 'results',
        'figures_dir': base / 'data' / 'results',
        'behavioral_file': base / 'data' / 'raw' / 'behavioral' / 'hcp1200_behavioral_data.csv',
        'log_file': base / 'data' / 'logs' / 'pipeline_run.json',
        'subject_ids_file': base / 'data' / 'processed' / 'valid_subjects.json'
    }
    return paths

def ensure_dirs() -> None:
    """Create all required directories if they don't exist."""
    paths = get_paths()
    for path in paths.values():
        if isinstance(path, Path):
            path.mkdir(parents=True, exist_ok=True)

def get_hyperparameter(key: str) -> Any:
    """
    Get a specific hyperparameter.
    
    Args:
        key: Name of the hyperparameter
        
    Returns:
        Value of the hyperparameter
    """
    hyperparameters = {
        'variance_threshold': 0.01,
        'pca_retention': 0.95,
        'subset_size': 100,
        'n_permutations': 1000,
        'n_bootstrap': 1000,
        'time_budget_hours': 3
    }
    return hyperparameters.get(key, None)
