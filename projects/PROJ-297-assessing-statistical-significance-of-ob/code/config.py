import os
from pathlib import Path
from typing import Dict, Any, Optional, List
import yaml

def get_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load configuration from a YAML file or return defaults.
    """
    defaults = {
        'paths': {
            'data_raw': 'data/raw',
            'data_processed': 'data/processed',
            'output_results': 'output/results',
            'output_plots': 'output/plots',
            'output_reports': 'output/reports',
            'output_exploratory': 'output/exploratory'
        },
        'random_seed': 42,
        'thresholds': [0.3, 0.5, 0.7],
        'permutations': 2000,
        'min_continuous_vars': 20,
        # Registry of the six required UCI datasets with verified URLs and handling hints
        'datasets': [
            {
                'name': 'Wine',
                'url': 'https://archive.ics.uci.edu/ml/machine-learning-databases/wine/wine.data',
                'format': 'csv',
                'delimiter': ',',
                'has_header': False,
                'description': 'Wine recognition dataset; 13 continuous attributes.'
            },
            {
                'name': 'Abalone',
                'url': 'https://archive.ics.uci.edu/ml/machine-learning-databases/abalone/abalone.data',
                'format': 'csv',
                'delimiter': ',',
                'has_header': False,
                'description': 'Predict age of abalone; includes several numeric features.'
            },
            {
                'name': 'Breast Cancer Wisconsin',
                'url': 'https://archive.ics.uci.edu/ml/machine-learning-databases/breast-cancer-wisconsin/wdbc.data',
                'format': 'csv',
                'delimiter': ',',
                'has_header': False,
                'description': 'Diagnostic breast cancer dataset with 30 continuous attributes.'
            },
            {
                'name': 'Student Performance',
                'url': 'https://archive.ics.uci.edu/ml/machine-learning-databases/00320/student.zip',
                'format': 'zip',
                'files': ['student-mat.csv', 'student-por.csv'],
                'merge': True,
                'delimiter': ',',
                'has_header': True,
                'description': 'Two CSV files (Math and Portuguese) that should be merged row‑wise.'
            },
            {
                'name': 'Air Quality',
                'url': 'https://archive.ics.uci.edu/ml/machine-learning-databases/00360/AirQualityUCI.zip',
                'format': 'zip',
                'files': ['AirQualityUCI.csv'],
                'delimiter': ';',
                'has_header': True,
                'description': 'Air quality measurements; CSV inside a zip archive.'
            },
            {
                'name': 'Concrete Compressive Strength',
                'url': 'https://archive.ics.uci.edu/ml/machine-learning-databases/concrete/compressive/Concrete_Data.xls',
                'format': 'excel',
                'description': 'Concrete compressive strength dataset in Excel format.'
            }
        ]
    }

    if config_path and os.path.exists(config_path):
        with open(config_path, 'r') as f:
            loaded = yaml.safe_load(f)
            # Deep merge not strictly necessary for this simple structure,
            # but we update top‑level keys to allow overrides.
            defaults.update(loaded)

    return defaults

def ensure_dirs(config: Dict[str, Any]):
    """Create directories defined in the config if they don't exist."""
    paths = config.get('paths', {})
    for key, path in paths.items():
        os.makedirs(path, exist_ok=True)

def save_config(config: Dict[str, Any], config_path: str):
    """Save configuration to a YAML file."""
    with open(config_path, 'w') as f:
        yaml.dump(config, f, default_flow_style=False)

def load_config(config_path: str) -> Dict[str, Any]:
    """Load configuration from a YAML file."""
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def get_dataset_registry() -> List[Dict[str, Any]]:
    """
    Return the list of dataset specifications defined in the configuration.
    This helper is convenient for loader modules that need to iterate over the
    six required UCI datasets and apply the appropriate handling logic.
    """
    cfg = get_config()
    return cfg.get('datasets', [])