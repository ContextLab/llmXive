import os
import random
import logging
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
import yaml

class ConfigError(Exception):
    """Exception raised for configuration errors."""
    pass

def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load configuration from a YAML file.
    
    Args:
        config_path: Path to the config file. If None, looks for 'config.yaml' in project root.
        
    Returns:
        Dictionary containing configuration values.
        
    Raises:
        ConfigError: If config file is not found or invalid.
    """
    if config_path is None:
        # Default to project root config
        config_path = Path(__file__).parent.parent / 'config.yaml'
    else:
        config_path = Path(config_path)
    
    if not config_path.exists():
        # Create a default config if none exists
        default_config = {
            'dataset_url': 'https://raw.githubusercontent.com/pewresearch/social-media-data/main/survey_data.csv',
            'random_seed': 42,
            'paths': {
                'raw_data': 'data/raw',
                'processed_data': 'data/processed',
                'outputs': 'outputs'
            }
        }
        config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_path, 'w') as f:
            yaml.dump(default_config, f)
        logging.warning(f"Created default config at {config_path}")
        return default_config
    
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        return config
    except yaml.YAMLError as e:
        raise ConfigError(f"Invalid YAML in config file: {e}")
    except Exception as e:
        raise ConfigError(f"Error loading config file: {e}")

def set_seed(seed: int) -> None:
    """
    Set random seed for reproducibility.
    
    Args:
        seed: Integer seed value.
    """
    random.seed(seed)
    logging.info(f"Random seed set to: {seed}")

def verify_and_apply_seed(config: Dict[str, Any]) -> bool:
    """
    Verify if a random seed is configured, apply it if present, and log status.
    
    This function satisfies Constitution Principle I (Reproducibility) by ensuring
    that seeds are actively applied and logged at runtime. If no seed is set,
    it logs a warning.
    
    Args:
        config: Configuration dictionary.
        
    Returns:
        True if a seed was found and applied, False otherwise.
    """
    seed = config.get('random_seed')
    
    if seed is None:
        logging.warning(
            "Constitution Principle I (Reproducibility) Warning: "
            "No random seed configured in config. "
            "Results may not be reproducible across runs. "
            "Please set 'random_seed' in config.yaml."
        )
        return False
    
    try:
        seed_int = int(seed)
        set_seed(seed_int)
        logging.info(f"Seed verification successful: Applied seed {seed_int}")
        return True
    except (ValueError, TypeError):
        logging.warning(
            f"Invalid random seed value in config: {seed}. "
            "Seed must be an integer. Reproducibility not guaranteed."
        )
        return False

def get_dataset_url(config: Dict[str, Any]) -> str:
    """
    Get dataset URL from configuration.
    
    Args:
        config: Configuration dictionary.
        
    Returns:
        Dataset URL string.
        
    Raises:
        ConfigError: If URL is not found in config.
    """
    url = config.get('dataset_url')
    if not url:
        raise ConfigError("Dataset URL not found in configuration")
    return url

def ensure_directories(config: Dict[str, Any]) -> None:
    """
    Ensure all required directories exist based on configuration.
    
    Args:
        config: Configuration dictionary containing path settings.
    """
    paths = config.get('paths', {})
    for path_key, path_value in paths.items():
        path_obj = Path(path_value)
        path_obj.mkdir(parents=True, exist_ok=True)
        logging.debug(f"Ensured directory exists: {path_obj}")