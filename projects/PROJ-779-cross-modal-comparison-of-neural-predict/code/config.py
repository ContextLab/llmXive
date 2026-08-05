import os
from pathlib import Path
from typing import Dict, Any, Tuple

# ==============================================================================
# REAL DATA POLICY
# ==============================================================================
# This project STRICTLY requires real data from OpenNeuro datasets.
# - Auditory: ds000246
# - Visual: ds000117 (via Hugging Face)
#
# SYNTHETIC DATA GENERATION IS PROHIBITED.
# If real data cannot be fetched or validated, the pipeline MUST fail loudly.
# No fallback to mock/synthetic data is permitted.
# ==============================================================================

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
        base / 'code' / 'utils',
        base / 'docs'
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
            'figures': str(base / 'figures'),
            'docs': str(base / 'docs')
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
        },
        'data_sources': {
            'auditory': {
                'source': 'OpenNeuro',
                'dataset_id': 'ds000246',
                'description': 'Auditory oddball paradigm (OpenNeuro)'
            },
            'visual': {
                'source': 'HuggingFace/OpenNeuro',
                'dataset_id': 'ds000117',
                'description': 'Visual oddball paradigm (OpenNeuro mirror)'
            }
        },
        'policies': {
            'real_data_only': True,
            'synthetic_data_permitted': False,
            'fail_on_fetch_error': True,
            'description': 'All data must originate from OpenNeuro. Synthetic data is strictly prohibited.'
        }
    }