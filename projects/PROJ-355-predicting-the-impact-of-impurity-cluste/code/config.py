import os
from pathlib import Path
from typing import List, Dict, Any, Optional

# Constants
PROJECT_ROOT = Path(__file__).resolve().parent.parent
RANDOM_SEED = 42
N_FOLDS = 5
VIF_THRESHOLD = 10.0
MAX_RETRIES = 3
PERTURBATION_MAGNITUDE = 0.01  # Angstroms

# Whitelist for data sources (MP/OQMD)
# Renamed to match task requirement: VALIDATED_SOURCE_WHITELIST
VALIDATED_SOURCE_WHITELIST = [
    'https://materialsproject.org',
    'https://oqmd.org'
]

def get_project_root() -> Path:
    return PROJECT_ROOT

def get_data_paths() -> Dict[str, Path]:
    root = get_project_root()
    return {
        'raw': root / 'data' / 'raw',
        'processed': root / 'data' / 'processed',
        'results': root / 'results',
        'processed_descriptors': root / 'data' / 'processed' / 'descriptors.csv',
        'processed_energies': root / 'data' / 'processed' / 'segregation_energies.csv',
        'metadata': root / 'data' / 'metadata.yaml'
    }

def get_config_summary() -> Dict[str, Any]:
    return {
        'random_seed': RANDOM_SEED,
        'n_folds': N_FOLDS,
        'vif_threshold': VIF_THRESHOLD,
        'max_retries': MAX_RETRIES,
        'perturbation_magnitude': PERTURBATION_MAGNITUDE,
        'whitelist': VALIDATED_SOURCE_WHITELIST
    }
