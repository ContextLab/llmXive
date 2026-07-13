import os
from pathlib import Path
from typing import Any, Dict, Union

def get_paths():
    """
    Returns a dictionary of paths used throughout the project.
    All paths are relative to the project root.
    """
    root = Path(__file__).parent.parent
    return {
        'root': root,
        'data_raw': root / 'data' / 'raw',
        'data_processed': root / 'data' / 'processed',
        'data_results': root / 'data' / 'results',
        'raw_behavioral': root / 'data' / 'raw' / 'behavioral' / 'hcp1200_behavioral_data.csv',
        'raw_fmri': root / 'data' / 'raw' / 'fmri',
        'processed_timeseries': root / 'data' / 'processed' / 'timeseries',
        'processed_features': root / 'data' / 'processed' / 'features',
        'results': root / 'data' / 'results',
        'logs': root / 'data' / 'logs'
    }

def ensure_dirs():
    """Create all necessary directories."""
    paths = get_paths()
    for path in paths.values():
        if isinstance(path, Path):
            path.mkdir(parents=True, exist_ok=True)
