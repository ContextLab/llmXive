import os
from pathlib import Path
from typing import Any, Dict, Union

def get_paths():
    """Return all project paths."""
    base_dir = Path(__file__).parent.parent
    paths = {
        'base': base_dir,
        'data_raw': base_dir / 'data' / 'raw',
        'data_processed': base_dir / 'data' / 'processed',
        'data_results': base_dir / 'data' / 'results',
        'hcp_data_dir': base_dir / 'data' / 'raw' / 'hcp',
        'behavioral_data': base_dir / 'data' / 'raw' / 'behavioral' / 'hcp1200_behavioral_data.csv',
        'filtered_subjects': base_dir / 'data' / 'raw' / 'behavioral' / 'filtered_subjects.csv',
        'preprocessed_data': base_dir / 'data' / 'processed' / 'time_series',
        'processed_features': base_dir / 'data' / 'processed' / 'features',
        'log_file': base_dir / 'data' / 'logs' / 'pipeline_run.json',
    }
    return paths

def ensure_dirs():
    """Ensure all required directories exist."""
    paths = get_paths()
    for path in paths.values():
        if isinstance(path, Path):
            path.mkdir(parents=True, exist_ok=True)

def get_config():
    """Return configuration parameters."""
    return {
        'variance_threshold': 0.01,
        'pca_retention': 0.95,
        'subset_size': 100,
        'random_seed': 42,
    }
