import os
from pathlib import Path
from typing import Dict, Any, Optional
import yaml

def get_config(config_path: str = 'code/config.yaml') -> Dict[str, Any]:
    """Load configuration from YAML file."""
    default_config = {
        'random_seed': 42,
        'threshold': 0.3,
        'permutations': 2000,
        'alpha': 0.05,
        'synthetic_n': 500,
        'synthetic_v': 20,
        'sweep_thresholds': [0.3, 0.4, 0.5],
        'paths': {
            'data_raw': 'data/raw',
            'data_processed': 'data/processed',
            'output_results': 'output/results',
            'output_plots': 'output/plots',
            'output_reports': 'output/reports'
        }
    }
    
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            user_config = yaml.safe_load(f)
            # Deep merge
            for key in user_config:
                if isinstance(user_config[key], dict) and key in default_config and isinstance(default_config[key], dict):
                    default_config[key].update(user_config[key])
                else:
                    default_config[key] = user_config[key]
    
    return default_config

def ensure_dirs(config: Dict[str, Any]):
    """Ensure all required directories exist."""
    paths = config['paths']
    for path_name, path_str in paths.items():
        os.makedirs(path_str, exist_ok=True)
