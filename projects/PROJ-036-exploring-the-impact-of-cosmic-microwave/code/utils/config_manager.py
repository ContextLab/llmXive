"""
Configuration management module for loading and combining cosmology parameters.

This module handles loading of standard Lambda-CDM and anomaly-specific
configuration files, providing a unified interface for simulation parameters.
"""
import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Project root directory (assumed to be two levels up from this file)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CONFIG_DIR = PROJECT_ROOT / "config"

def load_yaml_config(config_path: Path) -> Dict[str, Any]:
    """
    Load a YAML configuration file.
    
    Args:
        config_path: Path to the YAML configuration file.
        
    Returns:
        Dictionary containing the configuration data.
        
    Raises:
        FileNotFoundError: If the configuration file does not exist.
        yaml.YAMLError: If the file contains invalid YAML syntax.
    """
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    logger.info(f"Loaded configuration from {config_path}")
    return config

def load_lambdacdm_config() -> Dict[str, Any]:
    """
    Load the standard Lambda-CDM cosmology configuration.
    
    Returns:
        Dictionary containing Lambda-CDM parameters.
        
    Raises:
        FileNotFoundError: If lambdacdm.yaml is not found in the config directory.
    """
    config_path = CONFIG_DIR / "lambdacdm.yaml"
    return load_yaml_config(config_path)

def load_anomaly_config() -> Dict[str, Any]:
    """
    Load the anomaly-specific configuration.
    
    Returns:
        Dictionary containing anomaly parameters.
        
    Raises:
        FileNotFoundError: If anomaly.yaml is not found in the config directory.
    """
    config_path = CONFIG_DIR / "anomaly.yaml"
    return load_yaml_config(config_path)

def get_combined_config() -> Dict[str, Any]:
    """
    Combine standard Lambda-CDM and anomaly configurations.
    
    The anomaly configuration takes precedence for overlapping keys.
    
    Returns:
        Dictionary containing combined parameters.
    """
    lambdacdm = load_lambdacdm_config()
    anomaly = load_anomaly_config()
    
    # Deep merge: anomaly config overrides lambdacdm
    combined = lambdacdm.copy()
    for key, value in anomaly.items():
        if isinstance(value, dict) and key in combined and isinstance(combined[key], dict):
            combined[key].update(value)
        else:
            combined[key] = value
    
    logger.info("Combined Lambda-CDM and anomaly configurations")
    return combined

def ensure_config_exists() -> bool:
    """
    Verify that required configuration files exist.
    
    Returns:
        True if all required config files exist, False otherwise.
    """
    required_files = [
        CONFIG_DIR / "lambdacdm.yaml",
        CONFIG_DIR / "anomaly.yaml"
    ]
    
    all_exist = True
    for config_file in required_files:
        if not config_file.exists():
            logger.error(f"Missing required configuration file: {config_file}")
            all_exist = False
        else:
            logger.info(f"Found configuration file: {config_file}")
    
    return all_exist

def main():
    """
    Main function to demonstrate configuration loading.
    """
    print("Testing configuration management...")
    
    # Check if configs exist
    if not ensure_config_exists():
        print("ERROR: Required configuration files are missing.")
        return 1
    
    try:
        # Load individual configs
        lambdacdm = load_lambdacdm_config()
        print(f"\nLambda-CDM config loaded. Keys: {list(lambdacdm.keys())}")
        
        anomaly = load_anomaly_config()
        print(f"Anomaly config loaded. Keys: {list(anomaly.keys())}")
        
        # Load combined config
        combined = get_combined_config()
        print(f"\nCombined config loaded. Keys: {list(combined.keys())}")
        
        # Display some key parameters
        if 'cosmology' in combined:
            print(f"\nHubble parameter (h): {combined['cosmology']['h']}")
            print(f"Omega_m: {combined['cosmology']['omega_m']}")
        
        if 'anomaly_type' in combined:
            print(f"Anomaly type: {combined['anomaly_type']}")
        
        print("\nConfiguration loading successful!")
        return 0
        
    except Exception as e:
        logger.error(f"Error loading configuration: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
