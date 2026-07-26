"""
Configuration management for the project.
Handles random seeds, device settings, and directory paths.
"""
import os
import random
import logging
from typing import Optional, Dict, Any
import numpy as np

logger = logging.getLogger("config")

class Config:
    """Configuration class for project settings."""
    def __init__(self):
        # Random seeds
        self.random_seed = 42
        self.np_seed = 42
        
        # Device settings
        self.device = 'cpu'  # Default to CPU as per constraints
        
        # Directory paths (relative to project root)
        self.project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.data_dir = os.path.join(self.project_root, 'data')
        self.data_raw_dir = os.path.join(self.data_dir, 'raw')
        self.data_processed_dir = os.path.join(self.data_dir, 'processed')
        self.data_assets_dir = os.path.join(self.data_dir, 'assets')
        self.code_dir = os.path.join(self.project_root, 'code')
        self.artifacts_dir = os.path.join(self.project_root, 'artifacts')
        self.tests_dir = os.path.join(self.project_root, 'tests')
        
        # Ensure directories exist on initialization if needed
        # Note: T001a/T001b are marked as completed in tasks.md, but we ensure here too.
        # However, per T001a rejection, we must ensure they exist.
        ensure_directories([self.data_raw_dir, self.data_processed_dir, self.data_assets_dir,
                            self.code_dir, self.artifacts_dir, self.tests_dir])

def get_config() -> Dict[str, Any]:
    """
    Returns the configuration dictionary.
    
    Returns:
        Dictionary containing all configuration settings.
    """
    cfg = Config()
    return {
        "random_seed": cfg.random_seed,
        "np_seed": cfg.np_seed,
        "device": cfg.device,
        "data_dir": cfg.data_dir,
        "data_raw_dir": cfg.data_raw_dir,
        "data_processed_dir": cfg.data_processed_dir,
        "data_assets_dir": cfg.data_assets_dir,
        "code_dir": cfg.code_dir,
        "artifacts_dir": cfg.artifacts_dir,
        "tests_dir": cfg.tests_dir,
        "project_root": cfg.project_root
    }

def ensure_directories(dirs: list) -> None:
    """
    Ensures that the specified directories exist.
    
    Args:
        dirs: List of directory paths to create.
    """
    for dir_path in dirs:
        if not os.path.exists(dir_path):
            os.makedirs(dir_path, exist_ok=True)
            logger.info(f"Created directory: {dir_path}")
        else:
            logger.debug(f"Directory already exists: {dir_path}")

if __name__ == "__main__":
    cfg = get_config()
    print(f"Configuration loaded. Project root: {cfg['project_root']}")
    print(f"Data raw dir: {cfg['data_raw_dir']}")
    print(f"Artifacts dir: {cfg['artifacts_dir']}")
