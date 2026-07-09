"""
Configuration loader for the Statistical Analysis of Publicly Available Movie Review Sentiment and Box Office Revenue project.

This module provides a centralized configuration management system that loads
settings from environment variables and YAML configuration files. It supports
multiple environments (development, testing, production) and provides type-safe
access to configuration values.

Key responsibilities:
- Load and validate configuration from config.yaml
- Provide environment-specific overrides via environment variables
- Cache configuration to avoid redundant file I/O
- Validate required configuration keys at startup
"""

import os
import sys
import logging
from pathlib import Path
from typing import Any, Dict, Optional, List
import yaml

# Configure logging for the config module
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Project root directory
PROJECT_ROOT = Path(__file__).parent.parent.resolve()
CONFIG_DIR = PROJECT_ROOT / "specs" / "001-sentiment-revenue-lag-analysis"
CONFIG_FILE = CONFIG_DIR / "config.yaml"

# Default configuration values
DEFAULTS = {
    "paths": {
        "data_dir": "data",
        "results_dir": "results",
        "logs_dir": "data/logs",
        "figures_dir": "results",
        "processed_dir": "data/processed"
    },
    "datasets": {
        "tmdb_5000_url": "",
        "imdb_reviews_url": "",
        "min_movies": 500,
        "min_review_history_months": 3
    },
    "analysis": {
        "sentiment_window_weeks": 12,
        "correlation_method": "pearson",
        "bootstrap_iterations": 1000,
        "confidence_level": 0.95,
        "min_correlation_threshold": 0.1
    },
    "logging": {
        "level": "INFO",
        "file": "data/logs/ingestion_log.txt",
        "max_file_size_mb": 10,
        "backup_count": 5
    }
}

_config_cache: Optional[Dict[str, Any]] = None

def load_config(config_path: Optional[Path] = None, env: str = "default") -> Dict[str, Any]:
    """
    Load configuration from YAML file with environment-specific overrides.

    Args:
        config_path: Optional path to config file. Defaults to PROJECT_ROOT/config.yaml
        env: Environment name for overrides (default, development, testing, production)

    Returns:
        Merged configuration dictionary with environment overrides applied

    Raises:
        FileNotFoundError: If config file doesn't exist and no defaults provided
        yaml.YAMLError: If config file has invalid YAML syntax
        ValueError: If required configuration keys are missing
    """
    global _config_cache

    # Return cached config if available
    if _config_cache is not None:
        return _config_cache

    path = config_path or CONFIG_FILE

    # Start with defaults
    config = _deep_copy_dict(DEFAULTS)

    # Load from file if it exists
    if path.exists():
        logger.info(f"Loading configuration from {path}")
        with open(path, 'r', encoding='utf-8') as f:
            file_config = yaml.safe_load(f) or {}
            config = _merge_dicts(config, file_config)
    else:
        logger.warning(f"Config file not found at {path}, using defaults")

    # Apply environment-specific overrides from environment variables
    env_prefix = f"MOVIE_ANALYSIS_{env.upper()}_"
    for key, value in os.environ.items():
        if key.startswith(env_prefix):
            env_key = key[len(env_prefix):].lower()
            _set_nested_value(config, env_key, _parse_env_value(value))
            logger.info(f"Applied environment override: {env_key}")

    # Validate required keys
    _validate_required_keys(config)

    # Cache the result
    _config_cache = config

    return config

def get_config(key: Optional[str] = None, default: Any = None) -> Any:
    """
    Get a specific configuration value or the entire config dictionary.

    Args:
        key: Dot-separated path to config value (e.g., 'paths.data_dir')
        default: Default value if key not found

    Returns:
        Configuration value or entire config dict if key is None
    """
    config = load_config()

    if key is None:
        return config

    value = _get_nested_value(config, key, default)
    return value

def reset_config_cache() -> None:
    """Clear the configuration cache. Useful for testing."""
    global _config_cache
    _config_cache = None

def _deep_copy_dict(d: Dict) -> Dict:
    """Create a deep copy of a dictionary."""
    result = {}
    for key, value in d.items():
        if isinstance(value, dict):
            result[key] = _deep_copy_dict(value)
        elif isinstance(value, list):
            result[key] = [
                _deep_copy_dict(item) if isinstance(item, dict) else item
                for item in value
            ]
        else:
            result[key] = value
    return result

def _merge_dicts(base: Dict, override: Dict) -> Dict:
    """Recursively merge two dictionaries, with override taking precedence."""
    result = _deep_copy_dict(base)
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _merge_dicts(result[key], value)
        else:
            result[key] = value
    return result

def _set_nested_value(d: Dict, key: str, value: Any) -> None:
    """Set a value in a nested dictionary using dot notation."""
    keys = key.split('.')
    current = d
    for k in keys[:-1]:
        if k not in current:
            current[k] = {}
        current = current[k]
    current[keys[-1]] = value

def _get_nested_value(d: Dict, key: str, default: Any = None) -> Any:
    """Get a value from a nested dictionary using dot notation."""
    keys = key.split('.')
    current = d
    for k in keys:
        if isinstance(current, dict) and k in current:
            current = current[k]
        else:
            return default
    return current

def _parse_env_value(value: str) -> Any:
    """Parse environment variable string into appropriate Python type."""
    # Try boolean
    if value.lower() in ('true', 'yes', '1'):
        return True
    if value.lower() in ('false', 'no', '0'):
        return False

    # Try integer
    try:
        return int(value)
    except ValueError:
        pass

    # Try float
    try:
        return float(value)
    except ValueError:
        pass

    # Return as string
    return value

def _validate_required_keys(config: Dict) -> None:
    """Validate that required configuration keys are present and valid."""
    required_paths = [
        'paths.data_dir',
        'paths.results_dir',
        'paths.logs_dir'
    ]

    for path in required_paths:
        if _get_nested_value(config, path) is None:
            raise ValueError(f"Missing required configuration key: {path}")

    # Validate paths exist or can be created
    for path_key in ['data_dir', 'results_dir', 'logs_dir', 'processed_dir']:
        full_key = f'paths.{path_key}'
        path_value = _get_nested_value(config, full_key)
        if path_value:
            full_path = PROJECT_ROOT / path_value
            if not full_path.exists():
                logger.info(f"Creating directory: {full_path}")
                full_path.mkdir(parents=True, exist_ok=True)

def get_dataset_urls() -> Dict[str, str]:
    """
    Get validated dataset URLs from configuration.

    Returns:
        Dictionary containing dataset URLs

    Raises:
        ValueError: If required dataset URLs are not configured
    """
    config = load_config()
    urls = {
        'tmdb_5000': config['datasets']['tmdb_5000_url'],
        'imdb_reviews': config['datasets']['imdb_reviews_url']
    }

    if not urls['tmdb_5000']:
        raise ValueError("TMDB 5000 dataset URL not configured")
    if not urls['imdb_reviews']:
        raise ValueError("IMDb Reviews dataset URL not configured")

    return urls

def get_analysis_params() -> Dict[str, Any]:
    """
    Get analysis parameters from configuration.

    Returns:
        Dictionary containing analysis parameters
    """
    config = load_config()
    return config['analysis']

def get_logging_config() -> Dict[str, Any]:
    """
    Get logging configuration.

    Returns:
        Dictionary containing logging settings
    """
    config = load_config()
    return config['logging']

def ensure_directories() -> None:
    """Ensure all required directories exist."""
    config = load_config()
    for path_key in ['data_dir', 'results_dir', 'logs_dir', 'processed_dir']:
        full_key = f'paths.{path_key}'
        path_value = _get_nested_value(config, full_key)
        if path_value:
            full_path = PROJECT_ROOT / path_value
            full_path.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Ensured directory exists: {full_path}")

if __name__ == "__main__":
    # Test configuration loading
    logger.setLevel(logging.DEBUG)
    config = load_config()
    print("Configuration loaded successfully:")
    print(f"Data directory: {config['paths']['data_dir']}")
    print(f"Results directory: {config['paths']['results_dir']}")
    print(f"Minimum movies: {config['datasets']['min_movies']}")
    print(f"Sentiment window: {config['analysis']['sentiment_window_weeks']} weeks")
