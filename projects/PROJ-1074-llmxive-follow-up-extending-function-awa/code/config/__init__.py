"""Configuration module for llmXive pipeline."""
from pathlib import Path
import yaml
from utils.common import ConfigurationError, read_yaml, get_logger

logger = get_logger(__name__)

CONFIG_PATH = Path(__file__).parent / "settings.yaml"

def load_settings() -> dict:
    """Load and validate the base configuration settings.
    
    Returns:
        dict: The configuration dictionary with dataset_paths and model_hyperparameters.
    
    Raises:
        ConfigurationError: If the config file is missing or invalid.
    """
    if not CONFIG_PATH.exists():
        raise ConfigurationError(f"Configuration file not found: {CONFIG_PATH}")
    
    try:
        config = read_yaml(CONFIG_PATH)
    except Exception as e:
        raise ConfigurationError(f"Failed to parse configuration file: {e}") from e
    
    # Basic validation of required keys
    required_keys = ["dataset_paths", "model_hyperparameters"]
    for key in required_keys:
        if key not in config:
            raise ConfigurationError(f"Missing required configuration key: {key}")
    
    ds_keys = ["gsm8k", "logiqa"]
    for key in ds_keys:
        if key not in config["dataset_paths"]:
            raise ConfigurationError(f"Missing required dataset path key: {key}")
    
    model_keys = ["model_name", "batch_size", "max_length"]
    for key in model_keys:
        if key not in config["model_hyperparameters"]:
            raise ConfigurationError(f"Missing required model hyperparameter key: {key}")
    
    logger.info(f"Configuration loaded successfully from {CONFIG_PATH}")
    return config

__all__ = ["load_settings", "CONFIG_PATH"]
