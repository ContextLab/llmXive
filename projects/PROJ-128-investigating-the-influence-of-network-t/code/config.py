import os
from pathlib import Path
from typing import Dict, Any, Optional

# Default configuration
CONFIG = {
    'seed': 42,
    'paths': {
        'root': str(Path(__file__).parent.parent),
        'raw': str(Path(__file__).parent.parent / 'data' / 'raw'),
        'processed': str(Path(__file__).parent.parent / 'data' / 'processed'),
        'logs': str(Path(__file__).parent.parent / 'data' / 'logs'),
        'figures': str(Path(__file__).parent.parent / 'figures'),
    },
    'window_params': {
        'size': 30,  # 30 TR window
        'step': 1    # 1 TR step
    },
    'kmeans': {
        'k': 5
    },
    'thresholds': {
        'density': 0.1,      # Keep top 10% edges
        'max_sparsity': 0.90 # Exclude if sparsity > 90%
    },
    'subjects': [] # To be populated or loaded from a manifest
}

def ensure_directories(config):
    """Create necessary directories if they don't exist."""
    for path in config['paths'].values():
        if path:
            os.makedirs(path, exist_ok=True)

def get_config_dict():
    """Return the configuration dictionary."""
    return CONFIG

if __name__ == '__main__':
    print("Config loaded.")
    print(get_config_dict())
