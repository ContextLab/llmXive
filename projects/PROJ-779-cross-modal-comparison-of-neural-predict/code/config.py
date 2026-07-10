import os
from pathlib import Path
from typing import Dict, Any, Tuple

def ensure_directories():
    """Create necessary directories if they don't exist."""
    base = Path(__file__).parent.parent
    dirs = [
        base / 'data' / 'raw',
        base / 'data' / 'intermediate',
        base / 'data' / 'processed',
        base / 'data' / 'results',
        base / 'figures',
        base / 'code' / 'data',
        base / 'code' / 'analysis',
        base / 'code' / 'validation',
        base / 'code' / 'utils'
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

def get_config() -> Dict[str, Any]:
    """
    Get project configuration.
    
    Returns:
        Dictionary with configuration values.
    """
    base = Path(__file__).parent.parent
    
    return {
        'paths': {
            'base': str(base),
            'data': str(base / 'data'),
            'raw': str(base / 'data' / 'raw'),
            'intermediate': str(base / 'data' / 'intermediate'),
            'processed': str(base / 'data' / 'processed'),
            'results': str(base / 'data' / 'results'),
            'figures': str(base / 'figures')
        },
        'params': {
            'random_seed': 42,
            'min_sampling_rate': 500,  # Hz
            'min_oddball_trials': 100,
            'min_standard_trials': 300,
            'time_window_auditory': (-0.1, 0.5),  # seconds
            'time_window_visual': (-0.1, 0.5),    # seconds
            'filter_low': 1.0,  # Hz
            'filter_high': 40.0,  # Hz
            'ica_components': 20
        }
    }
