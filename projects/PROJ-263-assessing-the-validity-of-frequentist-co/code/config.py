"""
Configuration management for the Monte Carlo simulation pipeline.

This module handles:
- Loading configuration from YAML/JSON files
- Random seed management (deterministic execution per Principle I)
- Directory path resolution
- Logging setup
"""
import os
import json
import random
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
import numpy as np

# Global configuration state
_config: Dict[str, Any] = {}
_random_seed: Optional[int] = None
_np_random_generator: Optional[np.random.Generator] = None
_python_random_state_initialized: bool = False

# Default paths relative to project root
DEFAULT_CONFIG_PATH = "config/simulation_config.yaml"
PROJECT_ROOT = Path(__file__).parent.parent

def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load configuration from a YAML or JSON file.
    
    Args:
        config_path: Path to config file. Defaults to DEFAULT_CONFIG_PATH.
        
    Returns:
        Dictionary containing configuration values.
    """
    global _config
    
    if config_path is None:
        config_path = DEFAULT_CONFIG_PATH
    
    config_file = PROJECT_ROOT / config_path
    
    if not config_file.exists():
        logging.warning(f"Config file not found: {config_file}. Using defaults.")
        _config = _get_default_config()
        return _config
    
    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            if config_file.suffix in ['.yaml', '.yml']:
                # Try to load YAML if pyyaml is available, otherwise JSON
                try:
                    import yaml
                    _config = yaml.safe_load(f)
                except ImportError:
                    logging.warning("PyYAML not installed. Attempting JSON load.")
                    f.seek(0)
                    _config = json.load(f)
            elif config_file.suffix == '.json':
                _config = json.load(f)
            else:
                raise ValueError(f"Unsupported config file format: {config_file.suffix}")
    except Exception as e:
        logging.error(f"Failed to load config from {config_file}: {e}")
        _config = _get_default_config()
    
    return _config

def save_config(config: Dict[str, Any], config_path: Optional[str] = None) -> None:
    """
    Save configuration to a YAML or JSON file.
    
    Args:
        config: Configuration dictionary to save.
        config_path: Path to save to. Defaults to DEFAULT_CONFIG_PATH.
    """
    if config_path is None:
        config_path = DEFAULT_CONFIG_PATH
    
    config_file = PROJECT_ROOT / config_path
    config_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(config_file, 'w', encoding='utf-8') as f:
        if config_path.endswith(('.yaml', '.yml')):
            try:
                import yaml
                yaml.dump(config, f, default_flow_style=False)
            except ImportError:
                json.dump(config, f, indent=2)
        else:
            json.dump(config, f, indent=2)

def _get_default_config() -> Dict[str, Any]:
    """Return default configuration values."""
    return {
        "random_seed": 42,
        "simulation": {
            "n_replications": 10000,
            "confidence_levels": [0.90, 0.95, 0.99],
            "sample_sizes": [10, 20, 30],
            "bootstrap_resamples": 1000
        },
        "datasets": [
            "Wine",
            "Wine Quality Red",
            "Wine Quality White",
            "Ionosphere",
            "Heart Disease (Cleveland)"
        ],
        "paths": {
            "raw_data": "data/raw",
            "processed_data": "data/processed",
            "figures": "figures",
            "outputs": "outputs"
        },
        "logging": {
            "level": "INFO",
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        }
    }

def get_random_seed() -> int:
    """
    Get the current random seed.
    
    Returns:
        The configured random seed integer.
    """
    global _random_seed
    if _random_seed is None:
        # Load config if not already loaded
        config = load_config()
        _random_seed = config.get("random_seed", 42)
    return _random_seed

def set_random_seed(seed: int) -> None:
    """
    Set the random seed for reproducibility.
    
    This updates the global seed and re-initializes random number generators.
    
    Args:
        seed: Integer seed value.
    """
    global _random_seed, _np_random_generator, _python_random_state_initialized
    _random_seed = seed
    initialize_random_state()

def initialize_random_state() -> None:
    """
    Initialize all random number generators with the current seed.
    
    This ensures deterministic behavior across:
    - Python's built-in random module
    - NumPy's random number generator
    """
    global _np_random_generator, _python_random_state_initialized
    
    seed = get_random_seed()
    
    # Initialize Python's random module
    random.seed(seed)
    _python_random_state_initialized = True
    
    # Initialize NumPy's random generator
    _np_random_generator = np.random.default_rng(seed)
    
    logging.info(f"Random state initialized with seed: {seed}")

def get_random_generator() -> np.random.Generator:
    """
    Get the global NumPy random generator.
    
    Returns:
        The initialized np.random.Generator instance.
        
    Raises:
        RuntimeError: If random state has not been initialized.
    """
    global _np_random_generator
    if _np_random_generator is None:
        initialize_random_state()
    return _np_random_generator

def get_np_random_generator() -> np.random.Generator:
    """
    Alias for get_random_generator().
    
    Returns:
        The initialized np.random.Generator instance.
    """
    return get_random_generator()

def get_data_dir() -> Path:
    """Get the base data directory."""
    config = load_config()
    return PROJECT_ROOT / config.get("paths", {}).get("data", "data")

def get_raw_data_dir() -> Path:
    """Get the raw data directory path."""
    config = load_config()
    base = config.get("paths", {}).get("raw_data", "data/raw")
    path = PROJECT_ROOT / base
    path.mkdir(parents=True, exist_ok=True)
    return path

def get_processed_data_dir() -> Path:
    """Get the processed data directory path."""
    config = load_config()
    base = config.get("paths", {}).get("processed_data", "data/processed")
    path = PROJECT_ROOT / base
    path.mkdir(parents=True, exist_ok=True)
    return path

def get_figures_dir() -> Path:
    """Get the figures directory path."""
    config = load_config()
    base = config.get("paths", {}).get("figures", "figures")
    path = PROJECT_ROOT / base
    path.mkdir(parents=True, exist_ok=True)
    return path

def get_output_dir() -> Path:
    """Get the outputs directory path."""
    config = load_config()
    base = config.get("paths", {}).get("outputs", "outputs")
    path = PROJECT_ROOT / base
    path.mkdir(parents=True, exist_ok=True)
    return path

def get_log_level() -> int:
    """Get the logging level from config."""
    config = load_config()
    level_str = config.get("logging", {}).get("level", "INFO")
    return getattr(logging, level_str.upper(), logging.INFO)

def get_simulation_config() -> Dict[str, Any]:
    """Get simulation-specific configuration."""
    config = load_config()
    return config.get("simulation", {})

def setup_logging() -> None:
    """Configure logging based on configuration."""
    level = get_log_level()
    config = load_config()
    log_format = config.get("logging", {}).get("format", "%(asctime)s - %(levelname)s - %(message)s")
    
    logging.basicConfig(
        level=level,
        format=log_format,
        handlers=[
            logging.StreamHandler()
        ]
    )

def main():
    """Entry point for testing configuration."""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("Testing configuration module...")
    
    # Test seed management
    seed = get_random_seed()
    logger.info(f"Current seed: {seed}")
    
    set_random_seed(12345)
    new_seed = get_random_seed()
    logger.info(f"New seed: {new_seed}")
    
    # Test random generators
    rng = get_random_generator()
    sample = rng.random(5)
    logger.info(f"Sample from numpy RNG: {sample}")
    
    sample_py = [random.random() for _ in range(5)]
    logger.info(f"Sample from python RNG: {sample_py}")
    
    # Test paths
    logger.info(f"Raw data dir: {get_raw_data_dir()}")
    logger.info(f"Processed data dir: {get_processed_data_dir()}")
    logger.info(f"Output dir: {get_output_dir()}")
    
    logger.info("Configuration test complete.")

if __name__ == "__main__":
    main()