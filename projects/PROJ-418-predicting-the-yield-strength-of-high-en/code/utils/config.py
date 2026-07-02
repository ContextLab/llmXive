"""
Environment configuration management for verified dataset URLs.
"""
import os
import json
from typing import Dict, Any, Optional

# Default configuration
DEFAULT_CONFIG = {
    'paths': {
        'raw_data': 'data/raw',
        'processed_data': 'data/processed',
        'output': 'output',
        'figures': 'output/plots'
    },
    'research': {
        'verified_datasets': {
            'hea_compositions': 'https://raw.githubusercontent.com/llmXive/hea-datasets/main/hea_yield_strength.csv'
        }
    },
    'random_seed': 42,
    'logging': {
        'level': 'INFO',
        'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    }
}

def get_config() -> Dict[str, Any]:
    """
    Load configuration from environment or return defaults.
    
    Returns:
        Configuration dictionary.
    """
    config = DEFAULT_CONFIG.copy()
    
    # Check for environment variable override
    config_path = os.environ.get('LLMXIVE_CONFIG_PATH')
    if config_path and os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                env_config = json.load(f)
                # Deep merge not implemented for simplicity
                config.update(env_config)
        except Exception as e:
            print(f"Warning: Could not load config from {config_path}: {e}")
    
    return config

def get_verified_dataset_url(dataset_name: str) -> Optional[str]:
    """
    Retrieve the verified URL for a dataset.
    
    Args:
        dataset_name: Name of the dataset (e.g., 'hea_compositions')
    
    Returns:
        URL string or None if not found.
    """
    config = get_config()
    datasets = config.get('research', {}).get('verified_datasets', {})
    return datasets.get(dataset_name)

def ensure_dataset_url_exists(dataset_name: str) -> str:
    """
    Ensure a dataset URL exists, raising an error if not.
    
    Args:
        dataset_name: Name of the dataset.
    
    Returns:
        The verified URL.
    
    Raises:
        RuntimeError: If no verified URL is found.
    """
    url = get_verified_dataset_url(dataset_name)
    if not url:
        raise RuntimeError(
            f"DATA_SOURCE_MISSING: No verified URL found for dataset '{dataset_name}'. "
            f"Please add it to the verified_datasets configuration."
        )
    return url
