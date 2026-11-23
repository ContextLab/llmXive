"""
Configuration loading utilities.
"""
import yaml
import os
from pathlib import Path

def load_config(config_path: str = "config.yaml") -> dict:
    """
    Load configuration from a YAML file.
    
    Args:
        config_path: Path to the config file.
        
    Returns:
        Configuration dictionary.
    """
    path = Path(config_path)
    if not path.exists():
        # Return default config if file doesn't exist
        return {
            "seeds": {"random": 42},
            "thresholds": {"r": 0.8, "t": 100, "min_files": 10},
            "paths": {
                "raw_data": "data/raw",
                "processed": "data/processed",
                "results": "results",
                "state": "state",
                "logs": "logs"
            }
        }
        
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def get_paths(config: dict) -> dict:
    """
    Get path objects from configuration.
    
    Args:
        config: Configuration dictionary.
        
    Returns:
        Dictionary of Path objects.
    """
    path_config = config.get('paths', {})
    return {
        'raw_data': Path(path_config.get('raw_data', 'data/raw')),
        'processed': Path(path_config.get('processed', 'data/processed')),
        'results': Path(path_config.get('results', 'results')),
        'state': Path(path_config.get('state', 'state')),
        'logs': Path(path_config.get('logs', 'logs'))
    }
