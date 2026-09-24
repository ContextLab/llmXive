import os
from pathlib import Path
from typing import List, Dict, Any, Optional
import json

# Constants
PROJECT_ROOT = Path(__file__).resolve().parent.parent
RANDOM_SEED = 42
N_FOLDS = 5
VIF_THRESHOLD = 10.0
MAX_RETRIES = 3
PERTURBATION_MAGNITUDE = 0.01  # Angstroms

# Whitelist for data sources (MP/OQMD)
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
        'metadata': root / 'data' / 'metadata.yaml',
        'collinearity_report': root / 'data' / 'processed' / 'collinearity_report.md',
        'preprocessing_report': root / 'data' / 'processed' / 'preprocessing_report.json',
        'alloy_systems': root / 'data' / 'processed' / 'alloy_systems.json',
        'metrics': root / 'results' / 'metrics.json',
        'confidence_intervals': root / 'results' / 'confidence_intervals.json',
        'sensitivity_report': root / 'results' / 'sensitivity_report.json',
        'per_system_results': root / 'results' / 'per_system_results.json',
        'feature_importance': root / 'results' / 'feature_importance.json',
        'null_results_report': root / 'results' / 'null_results_report.json',
        'permutation_test': root / 'results' / 'permutation_test.json'
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

def save_config_snapshot(output_path: Optional[Path] = None) -> Path:
    """
    Saves the current configuration state to a JSON file for provenance.
    If output_path is not provided, saves to results/config_snapshot.json.
    """
    root = get_project_root()
    if output_path is None:
        output_path = root / 'results' / 'config_snapshot.json'
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    config_data = get_config_summary()
    config_data['project_root'] = str(PROJECT_ROOT)
    config_data['paths'] = {k: str(v) for k, v in get_data_paths().items()}
    
    with open(output_path, 'w') as f:
        json.dump(config_data, f, indent=2)
    
    return output_path