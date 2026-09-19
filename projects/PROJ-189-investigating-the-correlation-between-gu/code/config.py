"""
Environment configuration management for dataset paths and random seeds.

This module provides a centralized way to manage:
- Dataset paths (raw, processed, models)
- Random seeds for reproducibility
- Resource limits (memory, time)
- Logging levels and output directories

Usage:
    from config import Config
    cfg = Config()
    print(cfg.data_raw_path)
    print(cfg.random_seed)
"""

import os
import yaml
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, field

from utils.logging import get_logger

# Default configuration values
DEFAULT_CONFIG = {
    "paths": {
        "data_raw": "data/raw",
        "data_processed": "data/processed",
        "data_models": "data/models",
        "figures": "figures",
        "logs": "logs",
    },
    "seeds": {
        "random": 42,
        "numpy": 42,
        "tensorflow": None,  # Only used if TensorFlow is available
        "pytorch": None,  # Only used if PyTorch is available
    },
    "resources": {
        "max_memory_mb": 7000,
        "max_time_hours": 6,
        "cpu_only": True,
    },
    "analysis": {
        "rarefaction_depth": None,  # Auto-detect if None
        "min_samples": 500,
        "alpha_fdr": 0.05,
        "min_genera": 5,
        "min_cognitive_cols": 1,
    },
    "logging": {
        "level": "INFO",
        "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    },
}

@dataclass
class Config:
    """
    Centralized configuration manager for the project.

    Loads configuration from a YAML file if available, otherwise uses defaults.
    Provides typed access to all configuration values.
    """

    _config: Dict[str, Any] = field(default_factory=lambda: DEFAULT_CONFIG.copy())
    _project_root: Path = field(default_factory=lambda: Path(__file__).parent.parent)

    def __post_init__(self):
        """Initialize configuration from YAML file if available."""
        self._load_config_file()
        self._setup_directories()

    def _load_config_file(self) -> None:
        """Load configuration from config.yaml if it exists."""
        config_path = self._project_root / "config.yaml"
        if config_path.exists():
            logger = get_logger(__name__)
            logger.info(f"Loading configuration from {config_path}")
            try:
                with open(config_path, "r") as f:
                    user_config = yaml.safe_load(f)
                    if user_config:
                        self._merge_config(user_config)
            except yaml.YAMLError as e:
                logger.warning(f"Failed to parse config.yaml: {e}. Using defaults.")
            except Exception as e:
                logger.warning(f"Error loading config.yaml: {e}. Using defaults.")

    def _merge_config(self, user_config: Dict[str, Any]) -> None:
        """Recursively merge user configuration with defaults."""
        for key, value in user_config.items():
            if key in self._config and isinstance(self._config[key], dict):
                if isinstance(value, dict):
                    self._merge_config_recursive(self._config[key], value)
                else:
                    self._config[key] = value
            else:
                self._config[key] = value

    def _merge_config_recursive(self, base: Dict, override: Dict) -> None:
        """Recursively merge nested dictionaries."""
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._merge_config_recursive(base[key], value)
            else:
                base[key] = value

    def _setup_directories(self) -> None:
        """Create all required directories if they don't exist."""
        paths = self._config.get("paths", {})
        for dir_name, dir_path in paths.items():
            full_path = self._project_root / dir_path
            if not full_path.exists():
                full_path.mkdir(parents=True, exist_ok=True)

    # Path properties
    @property
    def data_raw_path(self) -> Path:
        """Path to raw data directory."""
        return self._project_root / self._config["paths"]["data_raw"]

    @property
    def data_processed_path(self) -> Path:
        """Path to processed data directory."""
        return self._project_root / self._config["paths"]["data_processed"]

    @property
    def data_models_path(self) -> Path:
        """Path to model storage directory."""
        return self._project_root / self._config["paths"]["data_models"]

    @property
    def figures_path(self) -> Path:
        """Path to figures output directory."""
        return self._project_root / self._config["paths"]["figures"]

    @property
    def logs_path(self) -> Path:
        """Path to logs directory."""
        return self._project_root / self._config["paths"]["logs"]

    # Seed properties
    @property
    def random_seed(self) -> int:
        """Primary random seed for reproducibility."""
        return self._config["seeds"]["random"]

    @property
    def numpy_seed(self) -> int:
        """Seed for NumPy random operations."""
        return self._config["seeds"]["numpy"]

    @property
    def tensorflow_seed(self) -> Optional[int]:
        """Seed for TensorFlow (if available)."""
        return self._config["seeds"]["tensorflow"]

    @property
    def pytorch_seed(self) -> Optional[int]:
        """Seed for PyTorch (if available)."""
        return self._config["seeds"]["pytorch"]

    # Resource properties
    @property
    def max_memory_mb(self) -> int:
        """Maximum allowed memory usage in MB."""
        return self._config["resources"]["max_memory_mb"]

    @property
    def max_time_hours(self) -> int:
        """Maximum allowed execution time in hours."""
        return self._config["resources"]["max_time_hours"]

    @property
    def cpu_only(self) -> bool:
        """Whether to enforce CPU-only execution."""
        return self._config["resources"]["cpu_only"]

    # Analysis properties
    @property
    def rarefaction_depth(self) -> Optional[int]:
        """Rarefaction depth for normalization. None means auto-detect."""
        return self._config["analysis"]["rarefaction_depth"]

    @property
    def min_samples(self) -> int:
        """Minimum number of samples required."""
        return self._config["analysis"]["min_samples"]

    @property
    def alpha_fdr(self) -> float:
        """FDR correction alpha level."""
        return self._config["analysis"]["alpha_fdr"]

    @property
    def min_genera(self) -> int:
        """Minimum number of genera required per sample."""
        return self._config["analysis"]["min_genera"]

    @property
    def min_cognitive_cols(self) -> int:
        """Minimum number of cognitive score columns required."""
        return self._config["analysis"]["min_cognitive_cols"]

    # Logging properties
    @property
    def log_level(self) -> int:
        """Logging level."""
        level_str = self._config["logging"]["level"].upper()
        return getattr(logging, level_str, logging.INFO)

    @property
    def log_format(self) -> str:
        """Logging format string."""
        return self._config["logging"]["format"]

    def get_config_dict(self) -> Dict[str, Any]:
        """Return the full configuration as a dictionary."""
        return self._config.copy()

    def save_config(self, path: Optional[Path] = None) -> None:
        """Save current configuration to a YAML file."""
        if path is None:
            path = self._project_root / "config.yaml"
        
        with open(path, "w") as f:
            yaml.dump(self._config, f, default_flow_style=False, sort_keys=False)
        
        logger = get_logger(__name__)
        logger.info(f"Configuration saved to {path}")


# Global configuration instance
_config_instance: Optional[Config] = None

def get_config() -> Config:
    """
    Get the global configuration instance.
    
    Returns:
        Config: The global configuration object.
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = Config()
    return _config_instance


def set_random_seed() -> None:
    """
    Set random seeds for reproducibility across all libraries.
    
    This function sets seeds for:
    - Python's random module
    - NumPy
    - TensorFlow (if available)
    - PyTorch (if available)
    """
    import random
    import numpy as np
    
    config = get_config()
    seed = config.random_seed
    
    random.seed(seed)
    np.random.seed(seed)
    
    logger = get_logger(__name__)
    logger.info(f"Random seeds set to {seed}")
    
    # TensorFlow
    try:
        import tensorflow as tf
        if config.tensorflow_seed is not None:
            tf.random.set_seed(config.tensorflow_seed)
            logger.info(f"TensorFlow seed set to {config.tensorflow_seed}")
    except ImportError:
        pass
    
    # PyTorch
    try:
        import torch
        if config.pytorch_seed is not None:
            torch.manual_seed(config.pytorch_seed)
            if torch.cuda.is_available():
                torch.cuda.manual_seed(config.pytorch_seed)
                torch.cuda.manual_seed_all(config.pytorch_seed)
            logger.info(f"PyTorch seed set to {config.pytorch_seed}")
    except ImportError:
        pass


if __name__ == "__main__":
    # Example usage
    config = get_config()
    
    print("=== Project Configuration ===")
    print(f"Data Raw Path: {config.data_raw_path}")
    print(f"Data Processed Path: {config.data_processed_path}")
    print(f"Data Models Path: {config.data_models_path}")
    print(f"Figures Path: {config.figures_path}")
    print(f"Logs Path: {config.logs_path}")
    print()
    print("=== Random Seeds ===")
    print(f"Random Seed: {config.random_seed}")
    print(f"NumPy Seed: {config.numpy_seed}")
    print(f"TensorFlow Seed: {config.tensorflow_seed}")
    print(f"PyTorch Seed: {config.pytorch_seed}")
    print()
    print("=== Resource Limits ===")
    print(f"Max Memory (MB): {config.max_memory_mb}")
    print(f"Max Time (hours): {config.max_time_hours}")
    print(f"CPU Only: {config.cpu_only}")
    print()
    print("=== Analysis Settings ===")
    print(f"Rarefaction Depth: {config.rarefaction_depth}")
    print(f"Min Samples: {config.min_samples}")
    print(f"FDR Alpha: {config.alpha_fdr}")
    print(f"Min Genera: {config.min_genera}")
    print(f"Min Cognitive Cols: {config.min_cognitive_cols}")
    
    # Set seeds for reproducibility
    set_random_seed()
    print("\nRandom seeds have been set for reproducibility.")
