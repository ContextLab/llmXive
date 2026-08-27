"""
Setup and configuration management for the single-cell trajectory pipeline.

This module handles:
- Loading configuration from config.yaml
- Setting random seeds for reproducibility
- Validating path existence
- Managing environment variables
"""

import os
import random
import sys
from pathlib import Path
from typing import Any, Dict, Optional

import yaml

# Try to import numpy, but make it optional for seed setting
try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False

# Try to import R via reticulate (optional)
try:
    import rpy2.robjects as ro
    R_AVAILABLE = True
except (ImportError, OSError):
    R_AVAILABLE = False


def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load configuration from a YAML file.
    
    Args:
        config_path: Path to config.yaml. If None, looks in code/ directory.
        
    Returns:
        Dictionary containing configuration values.
        
    Raises:
        FileNotFoundError: If config file doesn't exist.
        yaml.YAMLError: If config file is malformed.
    """
    if config_path is None:
        # Default to code/config.yaml relative to project root
        config_path = Path(__file__).parent / "config.yaml"
    
    config_path = Path(config_path)
    
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    return config


def set_random_seeds(config: Dict[str, Any]) -> None:
    """
    Set random seeds for reproducibility across all libraries.
    
    Args:
        config: Configuration dictionary with 'random_seeds' section.
    """
    seeds = config.get('random_seeds', {})
    
    # Python random
    if 'python' in seeds:
        random.seed(seeds['python'])
    
    # NumPy
    if NUMPY_AVAILABLE and 'numpy' in seeds:
        np.random.seed(seeds['numpy'])
    
    # TensorFlow (if available)
    try:
        import tensorflow as tf
        if 'tensorflow' in seeds and seeds['tensorflow'] is not None:
            tf.random.set_seed(seeds['tensorflow'])
    except ImportError:
        pass
    
    # PyTorch (if available)
    try:
        import torch
        if 'pytorch' in seeds and seeds['pytorch'] is not None:
            torch.manual_seed(seeds['pytorch'])
            if torch.cuda.is_available():
                torch.cuda.manual_seed_all(seeds['pytorch'])
    except ImportError:
        pass
    
    # R (if available via rpy2)
    if R_AVAILABLE and 'r' in seeds:
        ro.r.set_seed(seeds['r'])


def ensure_paths_exist(config: Dict[str, Any]) -> None:
    """
    Ensure all required directories exist based on configuration.
    
    Args:
        config: Configuration dictionary with 'paths' section.
    """
    paths = config.get('paths', {})
    
    # Get project root (parent of code/ directory)
    project_root = Path(__file__).parent.parent
    
    required_dirs = [
        paths.get('data_root', 'data'),
        paths.get('raw_data', 'data/raw'),
        paths.get('processed_data', 'data/processed'),
        paths.get('results', 'data/results'),
        paths.get('figures', 'figures'),
        paths.get('logs', 'logs'),
    ]
    
    for dir_name in required_dirs:
        dir_path = project_root / dir_name
        dir_path.mkdir(parents=True, exist_ok=True)


def get_dataset_paths(config: Dict[str, Any], dataset_id: str) -> Dict[str, Path]:
    """
    Get file paths for a specific dataset.
    
    Args:
        config: Configuration dictionary.
        dataset_id: Dataset identifier (e.g., 'gse136103').
        
    Returns:
        Dictionary with 'raw', 'processed', and 'results' paths.
    """
    paths = config.get('paths', {})
    project_root = Path(__file__).parent.parent
    
    raw_dir = project_root / paths.get('raw_data', 'data/raw')
    processed_dir = project_root / paths.get('processed_data', 'data/processed')
    results_dir = project_root / paths.get('results', 'data/results')
    
    return {
        'raw': raw_dir,
        'processed': processed_dir,
        'results': results_dir,
    }


def validate_config(config: Dict[str, Any]) -> None:
    """
    Validate that required configuration sections exist.
    
    Args:
        config: Configuration dictionary.
        
    Raises:
        ValueError: If required sections are missing.
    """
    required_sections = [
        'random_seeds',
        'paths',
        'datasets',
    ]
    
    for section in required_sections:
        if section not in config:
            raise ValueError(f"Missing required configuration section: {section}")


def main() -> None:
    """
    Main function to demonstrate configuration loading and setup.
    """
    print("Loading configuration...")
    config = load_config()
    
    print("Validating configuration...")
    validate_config(config)
    
    print("Setting random seeds...")
    set_random_seeds(config)
    
    print("Ensuring paths exist...")
    ensure_paths_exist(config)
    
    print("Configuration loaded successfully!")
    print(f"  - Python seed: {config['random_seeds']['python']}")
    print(f"  - NumPy seed: {config['random_seeds']['numpy']}")
    print(f"  - R seed: {config['random_seeds']['r']}")
    print(f"  - Data root: {config['paths']['data_root']}")
    print(f"  - Discovery datasets: {config['datasets']['discovery']}")
    print(f"  - Validation datasets: {config['datasets']['validation']}")

if __name__ == "__main__":
    main()
