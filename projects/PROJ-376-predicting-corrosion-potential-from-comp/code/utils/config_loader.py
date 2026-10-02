"""
Configuration Loader for the Corrosion Potential Prediction Pipeline.

This module provides functionality to load and validate configuration files
for random seeds and file paths. It ensures that all required keys exist
and contain non-empty values before the pipeline proceeds.
"""

import os
import sys
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
import yaml

# Import existing logging utility
from utils.logging import get_logger
from utils.exceptions import DataInsufficientError, CorrosionPipelineError

logger = get_logger(__name__)

def load_yaml_config(config_path: str) -> Dict[str, Any]:
    """
    Load a YAML configuration file.
    
    Args:
        config_path: Path to the YAML file (relative to project root)
        
    Returns:
        Dictionary containing the configuration
        
    Raises:
        CorrosionPipelineError: If the file cannot be read or parsed
    """
    full_path = Path(config_path)
    
    if not full_path.exists():
        raise CorrosionPipelineError(f"Configuration file not found: {config_path}")
        
    try:
        with open(full_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
            
        if config is None:
            raise CorrosionPipelineError(f"Configuration file is empty: {config_path}")
            
        return config
        
    except yaml.YAMLError as e:
        raise CorrosionPipelineError(f"Failed to parse YAML config {config_path}: {e}")
    except IOError as e:
        raise CorrosionPipelineError(f"Failed to read config file {config_path}: {e}")

def validate_seeds_config(config: Dict[str, Any]) -> None:
    """
    Validate the seeds configuration.
    
    Ensures the 'seeds' key exists and contains non-empty integer values.
    
    Args:
        config: The loaded seeds configuration
        
    Raises:
        DataInsufficientError: If validation fails
    """
    if 'seeds' not in config:
        raise DataInsufficientError("Seeds configuration missing 'seeds' key")
        
    seeds = config['seeds']
    
    if not isinstance(seeds, dict):
        raise DataInsufficientError("Seeds configuration must be a dictionary")
        
    if len(seeds) == 0:
        raise DataInsufficientError("Seeds configuration is empty")
        
    required_keys = ['global_seed']
    for key in required_keys:
        if key not in seeds:
            raise DataInsufficientError(f"Required seed key '{key}' missing from seeds config")
            
    for key, value in seeds.items():
        if value is None:
            raise DataInsufficientError(f"Seed value for '{key}' is None")
        if not isinstance(value, int):
            raise DataInsufficientError(f"Seed value for '{key}' must be an integer, got {type(value)}")
            
    logger.info("Seeds configuration validated successfully")

def validate_paths_config(config: Dict[str, Any]) -> None:
    """
    Validate the paths configuration.
    
    Ensures the 'paths' key exists and contains non-empty string values.
    
    Args:
        config: The loaded paths configuration
        
    Raises:
        DataInsufficientError: If validation fails
    """
    if 'paths' not in config:
        raise DataInsufficientError("Paths configuration missing 'paths' key")
        
    paths = config['paths']
    
    if not isinstance(paths, dict):
        raise DataInsufficientError("Paths configuration must be a dictionary")
        
    if len(paths) == 0:
        raise DataInsufficientError("Paths configuration is empty")
        
    # Check for required keys
    required_keys = ['root', 'code_dir', 'data_dir', 'processed_data_dir', 'logs_dir']
    for key in required_keys:
        if key not in paths:
            raise DataInsufficientError(f"Required path key '{key}' missing from paths config")
            
    for key, value in paths.items():
        if value is None or value == "":
            raise DataInsufficientError(f"Path value for '{key}' is empty")
        if not isinstance(value, str):
            raise DataInsufficientError(f"Path value for '{key}' must be a string, got {type(value)}")
            
    logger.info("Paths configuration validated successfully")

def verify_all_keys_exist(config: Dict[str, Any], section: str) -> bool:
    """
    Verify that a section in the config is non-empty.
    
    Args:
        config: The configuration dictionary
        section: The section key to check
        
    Returns:
        True if the section exists and is non-empty
        
    Raises:
        DataInsufficientError: If the section is missing or empty
    """
    if section not in config:
        raise DataInsufficientError(f"Configuration section '{section}' is missing")
        
    section_data = config[section]
    
    if isinstance(section_data, dict):
        if len(section_data) == 0:
            raise DataInsufficientError(f"Configuration section '{section}' is empty")
    elif isinstance(section_data, list):
        if len(section_data) == 0:
            raise DataInsufficientError(f"Configuration section '{section}' is empty")
    else:
        if section_data is None:
            raise DataInsufficientError(f"Configuration section '{section}' is None")
            
    return True

def main():
    """
    Main entry point for the config loader verification script.
    
    Loads both seeds.yaml and paths.yaml, validates them, and exits 0 on success.
    """
    logger.info("Starting configuration verification...")
    
    # Define config paths
    seeds_path = "config/seeds.yaml"
    paths_path = "config/paths.yaml"
    
    try:
        # Load and validate seeds config
        logger.info(f"Loading seeds configuration from {seeds_path}")
        seeds_config = load_yaml_config(seeds_path)
        validate_seeds_config(seeds_config)
        verify_all_keys_exist(seeds_config, 'seeds')
        logger.info("✓ Seeds configuration is valid and complete")
        
        # Load and validate paths config
        logger.info(f"Loading paths configuration from {paths_path}")
        paths_config = load_yaml_config(paths_path)
        validate_paths_config(paths_config)
        verify_all_keys_exist(paths_config, 'paths')
        logger.info("✓ Paths configuration is valid and complete")
        
        logger.info("All configurations verified successfully.")
        return 0
        
    except (DataInsufficientError, CorrosionPipelineError) as e:
        logger.error(f"Configuration verification failed: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error during configuration verification: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
