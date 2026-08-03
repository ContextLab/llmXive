import os
import random
import logging
from typing import Optional, Dict, Any
import numpy as np

class Config:
    """Global configuration container."""
    def __init__(self):
        self.seed = 42
        self.device = 'cpu'
        self.project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.data_dir = os.path.join(self.project_root, "data")
        self.code_dir = os.path.join(self.project_root, "code")
        self.tests_dir = os.path.join(self.project_root, "tests")
        self.artifacts_dir = os.path.join(self.project_root, "artifacts")
        self.specs_dir = os.path.join(self.project_root, "specs")
        
        # Training hyperparameters (defaults)
        self.batch_size = 32
        self.epochs = 100
        self.learning_rate = 1e-3
        self.weight_decay = 1e-5
        self.patience = 5  # Early stopping patience
        
        # Data processing parameters
        self.max_memory_gb = 4.0
        self.min_batch_size = 16
        
        # Logging settings
        self.log_level = logging.INFO

_config = Config()

def get_config() -> Config:
    """Return the global configuration instance."""
    return _config

def set_seed(seed: Optional[int] = None) -> None:
    """Set random seeds for reproducibility."""
    if seed is None:
        seed = _config.seed
    random.seed(seed)
    np.random.seed(seed)
    # Note: torch is not imported here to avoid circular dependency or forced import
    # If torch is available, it should be seeded in the module that uses it.
    try:
        import torch
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
    except ImportError:
        pass
    
    logging.info(f"Random seed set to {seed}")

def ensure_directories(dirs: list) -> None:
    """
    Create a list of directories if they do not exist.
    Raises an error if creation fails.
    """
    for dir_path in dirs:
        # Construct absolute path relative to project root if relative
        if not os.path.isabs(dir_path):
            full_path = os.path.join(_config.project_root, dir_path)
        else:
            full_path = dir_path

        if not os.path.exists(full_path):
            try:
                os.makedirs(full_path, exist_ok=True)
                logging.debug(f"Created directory: {full_path}")
            except OSError as e:
                logging.error(f"Failed to create directory {full_path}: {e}")
                raise e