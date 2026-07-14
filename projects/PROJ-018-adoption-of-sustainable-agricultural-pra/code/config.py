"""
Configuration Management for Sustainable Agriculture Study.
Handles paths, seeds, and settings.
"""
import os
import random
from pathlib import Path
from typing import Any, Dict, Optional
import yaml

class Config:
    """Configuration container."""
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or 'code/config.yaml'
        self.data = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        if os.path.exists(self.config_path):
            with open(self.config_path, 'r') as f:
                return yaml.safe_load(f) or {}
        # Default configuration if file missing
        return {
            'paths': {
                'raw_data': 'data/raw',
                'processed_data': 'data/processed',
                'results': 'results',
                'figures': 'figures',
                'modeling_log': 'modeling_log.yaml',
                'cleaned_data': 'data/processed/cleaned_data.csv',
                'engineered_data': 'data/processed/engineered_data.csv'
            },
            'random_seed': 42
        }

    def __getitem__(self, key: str) -> Any:
        return self.data[key]

    def get(self, key: str, default: Any = None) -> Any:
        return self.data.get(key, default)

# Singleton instance
_config_instance = None

def get_config() -> Config:
    global _config_instance
    if _config_instance is None:
        _config_instance = Config()
    return _config_instance

def set_random_seed(seed: int):
    """Set random seed for reproducibility."""
    random.seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)
    # Note: numpy seed set in scripts that use numpy

def get_data_path(relative_path: str) -> Path:
    """Resolve a relative path to an absolute Path object."""
    project_root = Path(__file__).resolve().parent.parent
    # If relative_path is absolute, just return it
    if Path(relative_path).is_absolute():
        return Path(relative_path)
    return project_root / relative_path
