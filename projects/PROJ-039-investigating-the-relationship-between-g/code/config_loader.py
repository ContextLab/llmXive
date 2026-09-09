import os
import yaml
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Union

from config import get_project_root

logger = logging.getLogger(__name__)

# Default configuration values matching the project's preprocessing requirements
DEFAULT_CONFIG = {
    "filter_bands": {
        "low_pass": 45.0,
        "high_pass": 1.0,
        "notch": 50.0
    },
    "ica_settings": {
        "n_components": 20,
        "method": "fastica",
        "random_state": 42
    },
    "pseudocount": 0.5,
    "alpha_band": {
        "low": 8.0,
        "high": 13.0
    },
    "epoch_config": {
        "tmin": -0.2,
        "tmax": 0.8,
        "baseline": (None, None),
        "min_valid_epochs_ratio": 0.8
    },
    "matching_config": {
        "strata_min_size": 5,
        "imputation_method": "median"
    }
}

def load_preprocess_config(config_path: Optional[Union[str, Path]] = None) -> Dict[str, Any]:
    """
    Load the preprocessing configuration from artifacts/preprocess.yaml.
    
    If the file does not exist, creates it with default values.
    
    Args:
        config_path: Optional path to the config file. Defaults to 
                     artifacts/preprocess.yaml relative to project root.
                     
    Returns:
        Dict containing the configuration parameters.
    """
    if config_path is None:
        project_root = get_project_root()
        config_path = project_root / "artifacts" / "preprocess.yaml"
    else:
        config_path = Path(config_path)

    # Ensure the directory exists
    config_path.parent.mkdir(parents=True, exist_ok=True)

    if config_path.exists():
        logger.info(f"Loading existing config from {config_path}")
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            # Validate and merge with defaults if keys are missing
            if not isinstance(config, dict):
                logger.warning("Config file is not a dictionary, using defaults")
                config = DEFAULT_CONFIG.copy()
            else:
                # Deep merge with defaults to ensure all required keys exist
                for key, value in DEFAULT_CONFIG.items():
                    if key not in config:
                        config[key] = value
                    elif isinstance(value, dict) and isinstance(config[key], dict):
                        config[key].update(value)
        
        except yaml.YAMLError as e:
            logger.error(f"Error parsing YAML file: {e}")
            logger.warning("Regenerating config with defaults")
            config = DEFAULT_CONFIG.copy()
    else:
        logger.info(f"Config file not found at {config_path}. Creating with defaults.")
        config = DEFAULT_CONFIG.copy()
        save_preprocess_config(config, config_path)

    return config

def save_preprocess_config(config: Dict[str, Any], config_path: Optional[Union[str, Path]] = None) -> None:
    """
    Save the preprocessing configuration to artifacts/preprocess.yaml.
    
    Args:
        config: The configuration dictionary to save.
        config_path: Optional path to the config file. Defaults to 
                     artifacts/preprocess.yaml relative to project root.
    """
    if config_path is None:
        project_root = get_project_root()
        config_path = project_root / "artifacts" / "preprocess.yaml"
    else:
        config_path = Path(config_path)

    config_path.parent.mkdir(parents=True, exist_ok=True)

    with open(config_path, 'w', encoding='utf-8') as f:
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)

    logger.info(f"Saved configuration to {config_path}")

def get_filter_bands(config: Dict[str, Any]) -> Dict[str, float]:
    """Extract filter band settings from config."""
    return config.get("filter_bands", DEFAULT_CONFIG["filter_bands"])

def get_ica_settings(config: Dict[str, Any]) -> Dict[str, Any]:
    """Extract ICA settings from config."""
    return config.get("ica_settings", DEFAULT_CONFIG["ica_settings"])

def get_pseudocount(config: Dict[str, Any]) -> float:
    """Extract pseudocount value from config."""
    return config.get("pseudocount", DEFAULT_CONFIG["pseudocount"])

def get_alpha_band(config: Dict[str, Any]) -> Dict[str, float]:
    """Extract alpha band settings from config."""
    return config.get("alpha_band", DEFAULT_CONFIG["alpha_band"])

def get_epoch_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """Extract epoch configuration from config."""
    return config.get("epoch_config", DEFAULT_CONFIG["epoch_config"])

def get_matching_config(config: Dict[str, Any]) -> Dict[str, Any]:
    """Extract matching/stratification configuration from config."""
    return config.get("matching_config", DEFAULT_CONFIG["matching_config"])

def validate_config(config: Dict[str, Any]) -> bool:
    """
    Validate that the configuration contains all required fields.
    
    Returns:
        True if valid, False otherwise.
    """
    required_keys = ["filter_bands", "ica_settings", "pseudocount", "alpha_band", "epoch_config"]
    for key in required_keys:
        if key not in config:
            logger.error(f"Missing required config key: {key}")
            return False
    
    # Validate filter_bands structure
    fb = config.get("filter_bands", {})
    if not all(k in fb for k in ["low_pass", "high_pass", "notch"]):
        logger.error("filter_bands missing required fields")
        return False

    # Validate ICA settings
    ica = config.get("ica_settings", {})
    if "n_components" not in ica or "method" not in ica:
        logger.error("ica_settings missing required fields")
        return False

    return True

def main():
    """Main entry point for creating/initializing the preprocess config."""
    logging.basicConfig(level=logging.INFO)
    
    config = load_preprocess_config()
    
    if validate_config(config):
        logger.info("Configuration is valid.")
        logger.info(f"Pseudocount: {get_pseudocount(config)}")
        logger.info(f"Filter bands: {get_filter_bands(config)}")
        logger.info(f"ICA settings: {get_ica_settings(config)}")
    else:
        logger.error("Configuration validation failed.")
        exit(1)

if __name__ == "__main__":
    main()
