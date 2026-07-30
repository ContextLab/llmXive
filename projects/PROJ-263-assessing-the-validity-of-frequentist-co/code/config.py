"""
Configuration management for the Monte Carlo simulation pipeline.

This module handles loading configuration from YAML files, managing random seeds
for reproducibility (Principle I), and providing access to project directories.
"""
import os
import json
import random
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
import yaml

# Global configuration state
_config: Dict[str, Any] = {}
_random_seed: Optional[int] = None
_logger = logging.getLogger(__name__)

# Default paths relative to project root
DEFAULT_CONFIG_PATH = "config/simulation_config.yaml"
DEFAULT_DATA_DIR = "data"
DEFAULT_OUTPUT_DIR = "outputs"
DEFAULT_LOG_LEVEL = "INFO"

# Default random seed if not specified
DEFAULT_SEED = 42

def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load configuration from a YAML file.
    
    Args:
        config_path: Path to the configuration file. If None, uses default.
        
    Returns:
        Dictionary containing configuration values.
        
    Raises:
        FileNotFoundError: If the config file doesn't exist.
        yaml.YAMLError: If the config file is malformed.
    """
    global _config
    path = Path(config_path) if config_path else Path(DEFAULT_CONFIG_PATH)
    
    if not path.exists():
        # Create a default config file if it doesn't exist
        _create_default_config(path)
    
    with open(path, 'r') as f:
        _config = yaml.safe_load(f) or {}
    
    _logger.info(f"Configuration loaded from {path}")
    return _config

def _create_default_config(path: Path) -> None:
    """Create a default configuration file if one doesn't exist."""
    path.parent.mkdir(parents=True, exist_ok=True)
    
    default_config = {
        "simulation": {
            "random_seed": DEFAULT_SEED,
            "confidence_levels": [0.90, 0.95, 0.99],
            "sample_sizes": [10, 20, 30],
            "n_replications": 1000,
            "bootstrap_resamples": 1000
        },
        "datasets": {
            "source_urls": {
                "wine": "https://archive.ics.uci.edu/ml/machine-learning-databases/wine/wine.data",
                "wine_quality_red": "https://archive.ics.uci.edu/ml/machine-learning-databases/wine-quality/winequality-red.csv",
                "wine_quality_white": "https://archive.ics.uci.edu/ml/machine-learning-databases/wine-quality/winequality-white.csv",
                "ionosphere": "https://archive.ics.uci.edu/ml/machine-learning-databases/ionosphere/ionosphere.data",
                "heart_cleveland": "https://archive.ics.uci.edu/ml/machine-learning-databases/heart-disease/processed.cleveland.data"
            },
            "variable_names": {
                "wine": "class,alcohol,mallic_acid,ash,alcalinity_of_ash,magnesium,total_phenols,flavanoids,nonflavanoid_phenols,proanthocyanins,color_intensity,hue,OD280/OD315_of_diluted_wines,proline",
                "wine_quality_red": "fixed acidity,volatile acidity,citric acid,residual sugar,chlorides,free sulfur dioxide,total sulfur dioxide,density,pH,sulphates,alcohol,quality",
                "wine_quality_white": "fixed acidity,volatile acidity,citric acid,residual sugar,chlorides,free sulfur dioxide,total sulfur dioxide,density,pH,sulphates,alcohol,quality",
                "ionosphere": "radar_returns",
                "heart_cleveland": "age,sex,cp,trestbps,chol,fbs,restecg,thalach,exang,oldpeak,slope,ca,thal"
            }
        },
        "paths": {
            "data_dir": DEFAULT_DATA_DIR,
            "output_dir": DEFAULT_OUTPUT_DIR,
            "raw_data_dir": "data/raw",
            "processed_data_dir": "data/processed",
            "figures_dir": "figures"
        },
        "logging": {
            "level": DEFAULT_LOG_LEVEL,
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        }
    }
    
    with open(path, 'w') as f:
        yaml.dump(default_config, f, default_flow_style=False)
    _logger.info(f"Created default configuration at {path}")

def save_config(config: Dict[str, Any], config_path: Optional[str] = None) -> None:
    """
    Save configuration to a YAML file.
    
    Args:
        config: Configuration dictionary to save.
        config_path: Path to save the configuration file. If None, uses default.
    """
    path = Path(config_path) if config_path else Path(DEFAULT_CONFIG_PATH)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, 'w') as f:
        yaml.dump(config, f, default_flow_style=False)
    _logger.info(f"Configuration saved to {path}")

def get_random_seed() -> int:
    """
    Get the current random seed for reproducibility.
    
    Returns:
        The current random seed value.
    """
    global _random_seed
    if _random_seed is None:
        # Try to load from config first
        if _config and 'simulation' in _config:
            _random_seed = _config['simulation'].get('random_seed', DEFAULT_SEED)
        else:
            _random_seed = DEFAULT_SEED
    return _random_seed

def set_random_seed(seed: int) -> None:
    """
    Set the random seed for all random number generators.
    
    This ensures deterministic behavior across all modules that use
    random number generation (numpy, random, etc.).
    
    Args:
        seed: The seed value to use.
    """
    global _random_seed
    _random_seed = seed
    
    # Set seed for Python's random module
    random.seed(seed)
    
    # Set seed for numpy (if available)
    try:
        import numpy as np
        np.random.seed(seed)
    except ImportError:
        pass
    
    _logger.info(f"Random seed set to {seed}")

def initialize_random_state(seed: Optional[int] = None) -> int:
    """
    Initialize the random state for the entire pipeline.
    
    This function should be called at the start of any script that
    requires deterministic random behavior.
    
    Args:
        seed: Optional seed value. If None, uses config or default.
        
    Returns:
        The seed value that was used.
    """
    if seed is not None:
        set_random_seed(seed)
    else:
        set_random_seed(get_random_seed())
    
    return get_random_seed()

def get_data_dir() -> Path:
    """
    Get the path to the data directory.
    
    Returns:
        Path object pointing to the data directory.
    """
    if _config and 'paths' in _config:
        data_dir = _config['paths'].get('data_dir', DEFAULT_DATA_DIR)
    else:
        data_dir = DEFAULT_DATA_DIR
    return Path(data_dir)

def get_output_dir() -> Path:
    """
    Get the path to the output directory.
    
    Returns:
        Path object pointing to the output directory.
    """
    if _config and 'paths' in _config:
        output_dir = _config['paths'].get('output_dir', DEFAULT_OUTPUT_DIR)
    else:
        output_dir = DEFAULT_OUTPUT_DIR
    return Path(output_dir)

def get_raw_data_dir() -> Path:
    """
    Get the path to the raw data directory.
    
    Returns:
        Path object pointing to the raw data directory.
    """
    if _config and 'paths' in _config:
        raw_dir = _config['paths'].get('raw_data_dir', "data/raw")
    else:
        raw_dir = "data/raw"
    return Path(raw_dir)

def get_processed_data_dir() -> Path:
    """
    Get the path to the processed data directory.
    
    Returns:
        Path object pointing to the processed data directory.
    """
    if _config and 'paths' in _config:
        processed_dir = _config['paths'].get('processed_data_dir', "data/processed")
    else:
        processed_dir = "data/processed"
    return Path(processed_dir)

def get_figures_dir() -> Path:
    """
    Get the path to the figures directory.
    
    Returns:
        Path object pointing to the figures directory.
    """
    if _config and 'paths' in _config:
        figures_dir = _config['paths'].get('figures_dir', "figures")
    else:
        figures_dir = "figures"
    return Path(figures_dir)

def get_log_level() -> str:
    """
    Get the logging level from configuration.
    
    Returns:
        The logging level string (e.g., "INFO", "DEBUG").
    """
    if _config and 'logging' in _config:
        return _config['logging'].get('level', DEFAULT_LOG_LEVEL)
    return DEFAULT_LOG_LEVEL

def get_simulation_config() -> Dict[str, Any]:
    """
    Get the simulation-specific configuration.
    
    Returns:
        Dictionary containing simulation parameters.
    """
    if _config and 'simulation' in _config:
        return _config['simulation']
    return {
        "random_seed": DEFAULT_SEED,
        "confidence_levels": [0.90, 0.95, 0.99],
        "sample_sizes": [10, 20, 30],
        "n_replications": 1000,
        "bootstrap_resamples": 1000
    }

def main():
    """
    Command-line interface for configuration management.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Configuration management for simulation pipeline")
    parser.add_argument("--config", type=str, help="Path to configuration file")
    parser.add_argument("--seed", type=int, help="Set random seed")
    parser.add_argument("--show", action="store_true", help="Show current configuration")
    
    args = parser.parse_args()
    
    # Load configuration
    config = load_config(args.config)
    
    if args.seed is not None:
        set_random_seed(args.seed)
    
    if args.show:
        print("Current Configuration:")
        print(json.dumps(config, indent=2))
        print(f"\nRandom Seed: {get_random_seed()}")
        print(f"Data Directory: {get_data_dir()}")
        print(f"Output Directory: {get_output_dir()}")
        print(f"Raw Data Directory: {get_raw_data_dir()}")
        print(f"Processed Data Directory: {get_processed_data_dir()}")
        print(f"Log Level: {get_log_level()}")

if __name__ == "__main__":
    main()
