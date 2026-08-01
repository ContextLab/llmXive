"""
Configuration management for the project.
Provides settings for random seeds, device, and directory paths.
"""
import os
import random
import logging
from typing import Optional, Dict, Any
import numpy as np

class Config:
    """Central configuration class for project settings."""
    
    def __init__(self):
        # Random seed for reproducibility
        self.seed: int = 42
        
        # Device for computation (default to CPU as per plan)
        self.device: str = 'cpu'
        
        # Project root directory (assumes current working directory is project root)
        self.project_root: str = os.getcwd()
        
        # Directory paths
        self.data_raw: str = os.path.join(self.project_root, "data", "raw")
        self.data_processed: str = os.path.join(self.project_root, "data", "processed")
        self.data_assets: str = os.path.join(self.project_root, "data", "assets")
        self.code_dir: str = os.path.join(self.project_root, "code")
        self.artifacts_dir: str = os.path.join(self.project_root, "artifacts")
        self.tests_dir: str = os.path.join(self.project_root, "tests")
        self.docs_dir: str = os.path.join(self.project_root, "docs")
        self.specs_dir: str = os.path.join(self.project_root, "specs")
        
        # Logging settings
        self.log_level: int = logging.INFO
        self.log_dir: str = os.path.join(self.artifacts_dir, "logs")
        
        # Memory limits (in GB)
        self.memory_limit_gb: float = 4.0
        
        # Batch size defaults
        self.batch_size: int = 64
        
        # Training settings
        self.epochs: int = 100
        self.patience: int = 5
        self.target_loss_threshold: float = 0.01
        
        # Statistical test settings
        self.statistical_test_primary: str = 'wilcoxon'
        self.statistical_test_sensitivity: str = 't-test'
        
        # Alignment threshold for US3
        self.alignment_threshold: float = 0.7

# Global config instance
_config: Optional[Config] = None

def get_config() -> Config:
    """Get the global configuration instance."""
    global _config
    if _config is None:
        _config = Config()
    return _config

def ensure_directories():
    """Ensure all required directories exist."""
    config = get_config()
    dirs = [
        config.data_raw,
        config.data_processed,
        config.data_assets,
        config.code_dir,
        config.artifacts_dir,
        config.tests_dir,
        config.docs_dir,
        config.specs_dir,
        config.log_dir
    ]
    for dir_path in dirs:
        os.makedirs(dir_path, exist_ok=True)

def set_seed(seed: int):
    """Set random seeds for reproducibility."""
    random.seed(seed)
    np.random.seed(seed)
    # If torch is available, set its seed too
    try:
        import torch
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
    except ImportError:
        pass