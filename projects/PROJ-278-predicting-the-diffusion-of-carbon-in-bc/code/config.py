"""
Configuration management for the llmXive diffusion prediction pipeline.

This module provides centralized management of:
- Random seeds (for reproducibility)
- File paths (project structure)
- Environment variables
- Hyperparameters

Usage:
    from config import load_config, set_global_seed, Config
    cfg = load_config()
    set_global_seed(cfg.random_seed)
"""
import os
import json
import random
import numpy as np
from pathlib import Path
from typing import Any, Dict, Optional, Union
import logging

# Configure module logger
logger = logging.getLogger(__name__)

class Config:
    """
    Centralized configuration container for the project.
    
    Attributes:
        project_root (Path): Root directory of the project.
        data_raw (Path): Path to raw data directory.
        data_processed (Path): Path to processed data directory.
        data_outputs (Path): Path to model outputs directory.
        contracts (Path): Path to contracts directory.
        random_seed (int): Global random seed for reproducibility.
        log_level (str): Logging level (DEBUG, INFO, WARNING, ERROR).
        max_memory_gb (float): Maximum allowed memory in GB.
        permutation_iterations (int): Number of iterations for permutation tests.
        cv_folds (int): Number of folds for cross-validation.
    """
    
    def __init__(self, project_root: Optional[Union[str, Path]] = None):
        """
        Initialize configuration with default paths and values.
        
        Args:
            project_root: Optional override for project root path.
        """
        # Determine project root
        if project_root:
            self.project_root = Path(project_root).resolve()
        else:
            # Default: assume code/ is at project_root/code/
            self.project_root = Path(__file__).resolve().parent.parent
        
        # Define directory structure
        self.data_raw = self.project_root / "data" / "raw"
        self.data_processed = self.project_root / "data" / "processed"
        self.data_outputs = self.project_root / "data" / "outputs"
        self.contracts = self.project_root / "contracts"
        self.figures = self.project_root / "figures"
        
        # Default values
        self.random_seed = 42
        self.log_level = "INFO"
        self.max_memory_gb = 6.0
        self.permutation_iterations = 10000
        self.cv_folds = 5
        self.test_split_ratio = 0.2
        self.min_samples_loocv = 30
        
        # Model hyperparameters (defaults)
        self.model_params = {
            "random_forest": {
                "n_estimators": 100,
                "max_depth": 10,
                "min_samples_split": 2,
                "random_state": 42
            },
            "xgboost": {
                "n_estimators": 100,
                "max_depth": 6,
                "learning_rate": 0.1,
                "random_state": 42
            },
            "elastic_net": {
                "alpha": 0.1,
                "l1_ratio": 0.5,
                "random_state": 42
            }
        }
        
        # Ensure directories exist
        self._ensure_directories()
    
    def _ensure_directories(self) -> None:
        """Create necessary directories if they don't exist."""
        directories = [
            self.data_raw,
            self.data_processed,
            self.data_outputs,
            self.contracts,
            self.figures
        ]
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Ensured directory exists: {directory}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            "project_root": str(self.project_root),
            "data_raw": str(self.data_raw),
            "data_processed": str(self.data_processed),
            "data_outputs": str(self.data_outputs),
            "contracts": str(self.contracts),
            "figures": str(self.figures),
            "random_seed": self.random_seed,
            "log_level": self.log_level,
            "max_memory_gb": self.max_memory_gb,
            "permutation_iterations": self.permutation_iterations,
            "cv_folds": self.cv_folds,
            "test_split_ratio": self.test_split_ratio,
            "min_samples_loocv": self.min_samples_loocv,
            "model_params": self.model_params
        }
    
    def save(self, path: Optional[Union[str, Path]] = None) -> None:
        """
        Save configuration to a JSON file.
        
        Args:
            path: Optional path to save config. Defaults to project_root/config.json
        """
        if path is None:
            path = self.project_root / "config.json"
        else:
            path = Path(path)
        
        with open(path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)
        logger.info(f"Configuration saved to {path}")
    
    @classmethod
    def load(cls, path: Optional[Union[str, Path]] = None) -> 'Config':
        """
        Load configuration from a JSON file.
        
        Args:
            path: Optional path to load config from. Defaults to project_root/config.json
        
        Returns:
            Config instance with loaded values
        """
        if path is None:
            path = Path(__file__).resolve().parent.parent / "config.json"
        else:
            path = Path(path)
        
        if not path.exists():
            logger.warning(f"Config file not found at {path}, using defaults")
            return cls()
        
        with open(path, 'r') as f:
            data = json.load(f)
        
        cfg = cls()
        # Update with loaded values
        if "random_seed" in data:
            cfg.random_seed = data["random_seed"]
        if "log_level" in data:
            cfg.log_level = data["log_level"]
        if "max_memory_gb" in data:
            cfg.max_memory_gb = data["max_memory_gb"]
        if "permutation_iterations" in data:
            cfg.permutation_iterations = data["permutation_iterations"]
        if "cv_folds" in data:
            cfg.cv_folds = data["cv_folds"]
        if "test_split_ratio" in data:
            cfg.test_split_ratio = data["test_split_ratio"]
        if "min_samples_loocv" in data:
            cfg.min_samples_loocv = data["min_samples_loocv"]
        if "model_params" in data:
            cfg.model_params = data["model_params"]
        
        # Paths are derived from project_root if not explicitly overridden
        if "project_root" in data:
            cfg.project_root = Path(data["project_root"]).resolve()
            cfg._ensure_directories()
        
        logger.info(f"Configuration loaded from {path}")
        return cfg


def set_global_seed(seed: int) -> None:
    """
    Set random seeds for all major libraries to ensure reproducibility.
    
    Args:
        seed: Integer seed value
    """
    random.seed(seed)
    np.random.seed(seed)
    
    # Try to set torch seed if available (optional)
    try:
        import torch
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
    except ImportError:
        logger.debug("PyTorch not available, skipping torch seed setting")
    
    # Set environment variable for some libraries
    os.environ["PYTHONHASHSEED"] = str(seed)
    
    logger.info(f"Global random seed set to {seed}")


def load_config(path: Optional[Union[str, Path]] = None) -> Config:
    """
    Convenience function to load configuration.
    
    Args:
        path: Optional path to config file
    
    Returns:
        Config instance
    """
    return Config.load(path)


def get_path(name: str) -> Path:
    """
    Get a specific path from the default configuration.
    
    Args:
        name: One of 'raw', 'processed', 'outputs', 'contracts', 'figures'
    
    Returns:
        Path object
    
    Raises:
        ValueError: If name is not recognized
    """
    cfg = Config()
    path_map = {
        "raw": cfg.data_raw,
        "processed": cfg.data_processed,
        "outputs": cfg.data_outputs,
        "contracts": cfg.contracts,
        "figures": cfg.figures
    }
    
    if name not in path_map:
        raise ValueError(f"Unknown path name: {name}. Valid options: {list(path_map.keys())}")
    
    return path_map[name]


# Initialize default config on module import if needed
# This allows scripts to access paths without explicit loading
_default_config: Optional[Config] = None

def get_config() -> Config:
    """
    Get or create the default configuration instance.
    
    Returns:
        Config instance
    """
    global _default_config
    if _default_config is None:
        _default_config = Config()
    return _default_config