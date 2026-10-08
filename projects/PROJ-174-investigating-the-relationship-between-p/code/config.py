import os
import yaml
from pathlib import Path
from typing import Dict, Any

def load_config() -> Dict[str, Any]:
    """
    Load configuration from code/config.yaml.
    Returns a dictionary with configuration values.
    """
    config_path = Path('code/config.yaml')
    if not config_path.exists():
        # Fallback to root if not in code/
        config_path = Path('config.yaml')
    
    if not config_path.exists():
        # Create a default config if missing
        default_config = {
            'seeds': 42,
            'thresholds': [0.40, 0.50, 0.60],
            'paths': {
                'processed_features': 'data/processed/features.csv'
            },
            'aggregation': False
        }
        config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_path, 'w') as f:
            yaml.dump(default_config, f)
        return default_config
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    # Ensure defaults
    if 'thresholds' not in config:
        config['thresholds'] = [0.40, 0.50, 0.60]
    if 'aggregation' not in config:
        config['aggregation'] = False
    if 'paths' not in config:
        config['paths'] = {}
    if 'processed_features' not in config['paths']:
        config['paths']['processed_features'] = 'data/processed/features.csv'
        
    return config
