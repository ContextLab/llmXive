import os
from pathlib import Path
from typing import Dict, Any, Optional
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
        'min_continuous_vars': 20
    }
    
    if config_path and os.path.exists(config_path):
        with open(config_path, 'r') as f:
            loaded = yaml.safe_load(f)
            # Deep merge not strictly necessary for this simple structure, 
            # but we'll update top-level keys
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
