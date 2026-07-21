import os
import yaml
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Union

from config import get_project_root

# Configure logger
logger = logging.getLogger(__name__)

# Default configuration values
DEFAULT_CONFIG = {
    "filter_bands": {
        "low_cut": 0.5,
        "high_cut": 45.0,
        "order": 4
    },
    "ica_settings": {
        "n_components": 20,
        "method": "fastica",
        "random_state": 42
    },
    "pseudocount": 0.5,
    "epoch_duration": 120,  # 2 minutes in seconds
    "min_valid_epochs_pct": 80
}

def load_preprocess_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load preprocessing configuration from a YAML file.
    
    Args:
        config_path: Path to the YAML configuration file. If None, defaults to
                     'data/processed/preprocess.yaml' in the project root.
                     
    Returns:
        Dictionary containing the loaded configuration with defaults applied
        for any missing keys.
        
    Raises:
        FileNotFoundError: If the specified config file does not exist.
        yaml.YAMLError: If the file contains invalid YAML syntax.
    """
    if config_path is None:
        project_root = get_project_root()
        config_path = os.path.join(project_root, "data", "processed", "preprocess.yaml")
    
    config_path = Path(config_path)
    
    if not config_path.exists():
        # If file doesn't exist, return defaults but log a warning
        logger.warning(f"Config file not found at {config_path}. Using defaults.")
        return DEFAULT_CONFIG.copy()
    
    with open(config_path, 'r') as f:
        loaded_config = yaml.safe_load(f)
    
    # Deep merge with defaults to ensure all required keys exist
    def deep_merge(base: Dict, override: Dict) -> Dict:
        result = base.copy()
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = deep_merge(result[key], value)
            else:
                result[key] = value
        return result
    
    return deep_merge(DEFAULT_CONFIG, loaded_config or {})

def get_filter_bands(config: Dict[str, Any]) -> Dict[str, float]:
    """
    Extract filter band settings from the configuration.
    
    Args:
        config: The loaded configuration dictionary.
        
    Returns:
        Dictionary with 'low_cut', 'high_cut', and 'order' keys.
    """
    return config.get("filter_bands", DEFAULT_CONFIG["filter_bands"]).copy()

def get_ica_settings(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract ICA settings from the configuration.
    
    Args:
        config: The loaded configuration dictionary.
        
    Returns:
        Dictionary with 'n_components', 'method', and 'random_state' keys.
    """
    return config.get("ica_settings", DEFAULT_CONFIG["ica_settings"]).copy()

def get_pseudocount(config: Dict[str, Any]) -> float:
    """
    Extract the pseudocount value from the configuration.
    
    Args:
        config: The loaded configuration dictionary.
        
    Returns:
        The pseudocount value as a float.
    """
    return float(config.get("pseudocount", DEFAULT_CONFIG["pseudocount"]))

def validate_config(config: Dict[str, Any]) -> List[str]:
    """
    Validate the configuration for logical consistency and required ranges.
    
    Args:
        config: The loaded configuration dictionary.
        
    Returns:
        A list of validation error messages. Empty if the config is valid.
    """
    errors = []
    
    # Validate filter bands
    fb = config.get("filter_bands", {})
    if fb.get("low_cut", 0) >= fb.get("high_cut", 100):
        errors.append("Filter low_cut must be less than high_cut.")
    if fb.get("order", 0) < 1:
        errors.append("Filter order must be at least 1.")
        
    # Validate ICA settings
    ica = config.get("ica_settings", {})
    if ica.get("n_components", 0) < 1:
        errors.append("ICA n_components must be at least 1.")
    if ica.get("method") not in ["fastica", "infomax", "picard"]:
        errors.append(f"Unsupported ICA method: {ica.get('method')}")
        
    # Validate pseudocount
    pc = config.get("pseudocount", 0)
    if pc < 0:
        errors.append("Pseudocount must be non-negative.")
        
    return errors

def main():
    """
    CLI entry point to load and print the configuration.
    Useful for debugging and verification.
    """
    import argparse
    import json
    
    parser = argparse.ArgumentParser(description="Load and display preprocessing configuration")
    parser.add_argument("--config", type=str, default=None,
                      help="Path to config file (default: data/processed/preprocess.yaml)")
    parser.add_argument("--validate", action="store_true",
                      help="Validate the configuration and exit with error if invalid")
    args = parser.parse_args()
    
    config = load_preprocess_config(args.config)
    
    if args.validate:
        errors = validate_config(config)
        if errors:
            for err in errors:
                logger.error(err)
            exit(1)
        else:
            logger.info("Configuration is valid.")
    
    print(json.dumps(config, indent=2))

if __name__ == "__main__":
    main()
