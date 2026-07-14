"""Configuration management for the project."""
import os
import random
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

class Config:
    def __init__(self, config_dict: Dict[str, Any]):
        self.config_dict = config_dict
        self.paths = config_dict.get('paths', {})

    def get_data_path(self, key: str) -> Path:
        """Get a data path by key from the config."""
        path_str = self.paths.get(key)
        if not path_str:
            raise KeyError(f"Path key '{key}' not found in config.")
        return Path(path_str)

_config: Optional[Config] = None

def get_config() -> Config:
    """Load or return the global configuration."""
    global _config
    if _config is None:
        # Default config if no file found
        default_paths = {
            'project_root': Path.cwd(),
            'data_raw': 'data/raw',
            'data_processed': 'data/processed',
            'results_dir': 'results',
            'cleaned_data': 'data/processed/cleaned_data.csv',
            'engineered_data': 'data/processed/engineered_data.csv',
            'metadata': 'data/metadata.yaml',
            'modeling_log': 'modeling_log.yaml'
        }
        
        config_file = Path('code/config.yaml')
        if config_file.exists():
            with open(config_file, 'r') as f:
                cfg = yaml.safe_load(f)
                default_paths.update(cfg.get('paths', {}))
        
        _config = Config({'paths': default_paths})
    return _config

def set_random_seed(seed: int = 42) -> None:
    """Set random seed for reproducibility."""
    random.seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)
    # Note: numpy and torch seeds set in specific scripts if needed

def get_data_path(key: str) -> Path:
    """Convenience function to get a data path."""
    return get_config().get_data_path(key)
