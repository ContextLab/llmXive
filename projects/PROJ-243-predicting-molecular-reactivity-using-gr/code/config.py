import os
import random
import logging
from typing import Optional, Dict, Any
import numpy as np

class Config:
    """Central configuration for the project."""
    def __init__(self):
        self.project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        self.data_raw_dir = os.path.join(self.project_root, 'data', 'raw')
        self.data_processed_dir = os.path.join(self.project_root, 'data', 'processed')
        self.data_assets_dir = os.path.join(self.project_root, 'data', 'assets')
        self.code_dir = os.path.join(self.project_root, 'code')
        self.artifacts_dir = os.path.join(self.project_root, 'artifacts')
        self.tests_dir = os.path.join(self.project_root, 'tests')
        self.artifacts_logs_dir = os.path.join(self.artifacts_dir, 'logs')
        self.artifacts_weights_dir = os.path.join(self.artifacts_dir, 'weights')
        self.artifacts_figures_dir = os.path.join(self.artifacts_dir, 'figures')
        
        # Device configuration
        self.device = 'cpu'
        
        # Random seed
        self.seed = 42

def get_config() -> Config:
    """Retrieve the global configuration instance."""
    return Config()

def set_seed(seed: Optional[int] = None) -> None:
    """Set random seeds for reproducibility."""
    if seed is None:
        seed = get_config().seed
    random.seed(seed)
    np.random.seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)

def ensure_directories() -> None:
    """
    Create all required project directories if they do not exist.
    This ensures the directory structure is ready for data ingestion and artifact storage.
    """
    config = get_config()
    directories = [
        config.data_raw_dir,
        config.data_processed_dir,
        config.data_assets_dir,
        config.code_dir,
        config.artifacts_dir,
        config.tests_dir,
        config.artifacts_logs_dir,
        config.artifacts_weights_dir,
        config.artifacts_figures_dir
    ]
    
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            logging.getLogger(__name__).info(f"Created directory: {directory}")

def get_default_config() -> Dict[str, Any]:
    """Return a dictionary of default configuration values."""
    config = get_config()
    return {
        'device': config.device,
        'seed': config.seed,
        'data_raw_dir': config.data_raw_dir,
        'data_processed_dir': config.data_processed_dir,
        'data_assets_dir': config.data_assets_dir,
        'artifacts_dir': config.artifacts_dir,
        'artifacts_logs_dir': config.artifacts_logs_dir
    }
