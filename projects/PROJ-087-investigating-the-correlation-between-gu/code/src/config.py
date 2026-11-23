"""
Configuration loader for the project.

Supports dynamic data source injection via environment variables.
"""
import os
from typing import Optional, Dict, Any
from pathlib import Path

def load_config() -> Dict[str, Any]:
    """
    Load configuration from environment variables and defaults.
    
    Returns:
        A dictionary containing configuration values.
    """
    config = {
        'DATA_URL': os.getenv('DATA_URL', 'american_gut_project'),
        'RANDOM_SEED': int(os.getenv('RANDOM_SEED', '42')),
        'LOG_LEVEL': os.getenv('LOG_LEVEL', 'INFO'),
        'DATA_DIR': os.getenv('DATA_DIR', 'data'),
        'OUTPUT_DIR': os.getenv('OUTPUT_DIR', 'data/processed'),
    }
    
    # Validate types
    try:
        config['RANDOM_SEED'] = int(config['RANDOM_SEED'])
    except ValueError:
        raise ValueError(f"Invalid RANDOM_SEED: {os.getenv('RANDOM_SEED')}")
        
    return config
