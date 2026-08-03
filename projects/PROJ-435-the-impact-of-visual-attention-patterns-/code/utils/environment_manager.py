"""
Environment management and reproducibility utilities.
Handles configuration loading, random seed setting, and path resolution.
"""
import os
import random
import logging
from pathlib import Path
from typing import Any, Dict, Optional
import yaml
import numpy as np

# Global configuration cache
_config_cache: Optional[Dict[str, Any]] = None
_paths_cache: Optional[Dict[str, Path]] = None

def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load configuration from a YAML file.
    
    Args:
        config_path: Path to the config file. Defaults to 'code/config.yaml'.
        
    Returns:
        Dictionary containing configuration parameters.
    """
    global _config_cache
    if _config_cache is not None:
        return _config_cache
        
    if config_path is None:
        config_path = "code/config.yaml"
        
    config_file = Path(config_path)
    if not config_file.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
    with open(config_file, 'r') as f:
        _config_cache = yaml.safe_load(f)
        
    return _config_cache

def deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """
    Recursively merge two dictionaries.
    
    Args:
        base: Base dictionary.
        override: Dictionary with values to override.
        
    Returns:
        Merged dictionary.
    """
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result

def setup_reproducibility(seed: Optional[int] = None) -> int:
    """
    Set random seeds for Python, NumPy, and optionally other libraries.
    
    Args:
        seed: Random seed to use. If None, reads from config.
        
    Returns:
        The seed value that was set.
    """
    if seed is None:
        config = load_config()
        seed = config.get('random_seed', 42)
        
    # Set Python random seed
    random.seed(seed)
    
    # Set NumPy random seed
    np.random.seed(seed)
    
    # Log the seed for reproducibility
    logger = logging.getLogger(__name__)
    logger.info(f"Reproducibility: Random seed set to {seed}")
    
    return seed

def get_paths() -> Dict[str, Path]:
    """
    Get standardized paths for project directories.
    
    Returns:
        Dictionary mapping directory names to Path objects.
    """
    global _paths_cache
    if _paths_cache is not None:
        return _paths_cache
        
    config = load_config()
    paths_config = config.get('paths', {})
    
    base_dir = Path(__file__).parent.parent.parent
    
    _paths_cache = {
        'raw_data': base_dir / paths_config.get('raw_data_dir', 'data/raw'),
        'derived_data': base_dir / paths_config.get('derived_data_dir', 'data/derived'),
        'processed_data': base_dir / paths_config.get('processed_data_dir', 'data/processed'),
        'state': base_dir / paths_config.get('state_dir', 'state'),
        'figures': base_dir / paths_config.get('figures_dir', 'figures'),
        'code': base_dir / 'code',
        'tests': base_dir / 'tests'
    }
    
    # Ensure directories exist
    for path in _paths_cache.values():
        path.mkdir(parents=True, exist_ok=True)
        
    return _paths_cache

def get_config_value(key: str, default: Any = None) -> Any:
    """
    Get a specific value from the configuration.
    
    Args:
        key: Dot-separated key path (e.g., 'fixation_detection.ivt_duration_threshold').
        default: Default value if key not found.
        
    Returns:
        Configuration value or default.
    """
    config = load_config()
    keys = key.split('.')
    value = config
    for k in keys:
        if isinstance(value, dict) and k in value:
            value = value[k]
        else:
            return default
    return value

def setup_logging(log_level: Optional[str] = None, log_file: Optional[str] = None) -> logging.Logger:
    """
    Configure logging for the project.
    
    Args:
        log_level: Logging level (e.g., 'INFO', 'DEBUG').
        log_file: Path to log file.
        
    Returns:
        Configured logger.
    """
    config = load_config()
    
    if log_level is None:
        log_level = config.get('logging', {}).get('level', 'INFO')
        
    if log_file is None:
        log_file = config.get('logging', {}).get('file', 'state/pipeline.log')
        
    # Ensure state directory exists
    Path(log_file).parent.mkdir(parents=True, exist_ok=True)
    
    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, log_level.upper(), logging.INFO),
        format=config.get('logging', {}).get('format', '%(asctime)s - %(name)s - %(levelname)s - %(message)s'),
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    
    return logging.getLogger(__name__)

def main():
    """
    Main function to demonstrate environment setup.
    """
    # Setup logging
    logger = setup_logging()
    
    # Setup reproducibility
    seed = setup_reproducibility()
    logger.info(f"Environment initialized with seed: {seed}")
    
    # Get paths
    paths = get_paths()
    logger.info(f"Data directories initialized:")
    for name, path in paths.items():
        logger.info(f"  {name}: {path}")
        
    # Get a config value
    duration_threshold = get_config_value('fixation_detection.ivt_duration_threshold')
    logger.info(f"IVT duration threshold: {duration_threshold} ms")
    
    logger.info("Environment setup complete.")

if __name__ == "__main__":
    main()
