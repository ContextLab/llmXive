"""
Environment configuration module for pipeline settings.

This module provides centralized configuration management for dataset URLs,
random seeds, and other environment-specific settings.
"""
import os
import random
from pathlib import Path
from typing import Dict, Any, Optional
import numpy as np
import yaml

class EnvironmentConfig:
    """Container for environment configuration settings."""
    
    def __init__(
        self,
        dataset_name: Optional[str] = None,
        dataset_url: Optional[str] = None,
        raw_data_dir: Optional[str] = None,
        processed_data_dir: Optional[str] = None,
        random_seed: int = 42,
        project_root: Optional[str] = None
    ):
        self.dataset_name = dataset_name
        self.dataset_url = dataset_url
        self.raw_data_dir = raw_data_dir
        self.processed_data_dir = processed_data_dir
        self.random_seed = random_seed
        self.project_root = Path(project_root) if project_root else Path(__file__).parent.parent.parent

_config: Optional[EnvironmentConfig] = None

def get_environment_config() -> EnvironmentConfig:
    """
    Gets the singleton environment configuration instance.
    
    Returns:
        EnvironmentConfig instance with current settings.
    """
    global _config
    if _config is None:
        # Default configuration
        project_root = Path(__file__).parent.parent.parent
        _config = EnvironmentConfig(
            dataset_name="ml4matscience/gfa-experimental",
            dataset_url="https://huggingface.co/datasets/ml4matscience/gfa-experimental",
            raw_data_dir=str(project_root / "data" / "raw"),
            processed_data_dir=str(project_root / "data" / "processed"),
            random_seed=42,
            project_root=str(project_root)
        )
        
        # Override with environment variables if set
        if os.getenv("GFA_DATASET_NAME"):
            _config.dataset_name = os.getenv("GFA_DATASET_NAME")
        if os.getenv("GFA_RAW_DATA_DIR"):
            _config.raw_data_dir = os.getenv("GFA_RAW_DATA_DIR")
        if os.getenv("GFA_PROCESSED_DATA_DIR"):
            _config.processed_data_dir = os.getenv("GFA_PROCESSED_DATA_DIR")
        if os.getenv("RANDOM_SEED"):
            _config.random_seed = int(os.getenv("RANDOM_SEED"))
    
    return _config

def initialize_random_seeds(seed: Optional[int] = None) -> None:
    """
    Initializes random seeds for reproducibility.
    
    Args:
        seed: Optional seed value. If None, uses the configured random_seed.
    """
    if seed is None:
        seed = get_environment_config().random_seed
    
    random.seed(seed)
    np.random.seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)

def main():
    """Main entry point for standalone execution (for testing)."""
    config = get_environment_config()
    print(f"Project Root: {config.project_root}")
    print(f"Dataset Name: {config.dataset_name}")
    print(f"Dataset URL: {config.dataset_url}")
    print(f"Raw Data Dir: {config.raw_data_dir}")
    print(f"Processed Data Dir: {config.processed_data_dir}")
    print(f"Random Seed: {config.random_seed}")

if __name__ == "__main__":
    main()
