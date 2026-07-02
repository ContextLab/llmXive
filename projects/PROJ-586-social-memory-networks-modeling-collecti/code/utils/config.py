"""
Configuration management for the Social Memory Networks project.
"""
from typing import Dict, Any
import os
from pathlib import Path

def get_config() -> Dict[str, Any]:
    """
    Load and return the experiment configuration.
    
    Returns:
        Configuration dictionary.
    """
    config = {
        'seed': 42,
        'device': 'cpu',
        'model_name': 'opt-125m',
        'context_limit': 512,
        'num_items': 10,
        'num_rounds': 5,
        'batch_size': 1,
        'log_level': 'INFO'
    }
    
    # Override with environment variables if present
    for key in config:
        env_key = f"SMN_{key.upper()}"
        if env_key in os.environ:
            value = os.environ[env_key]
            if key in ['seed', 'context_limit', 'num_items', 'num_rounds', 'batch_size']:
                config[key] = int(value)
            elif key == 'log_level':
                config[key] = value.upper()
            else:
                config[key] = value
    
    return config