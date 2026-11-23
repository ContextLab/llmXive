"""
Environment Configuration Management Module.

Provides functionality to load and apply environment-specific configurations
for CI (Sampled) vs Full (HPC) execution modes.

Usage:
    config = load_environment_config(mode='ci_sampled')
    constraints = get_constraint(config, 'max_replicates_per_species')
"""
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List
import yaml
from loguru import logger

# Import existing logger setup
from code.utils.logger import setup_logger

# Ensure logger is configured
setup_logger()

CONFIG_FILE_PATH = Path(__file__).parent.parent / "config" / "environments.yaml"

def load_environment_config(mode: Optional[str] = None) -> Dict[str, Any]:
    """
    Load environment configuration from the YAML file.
    
    Args:
        mode: Specific mode to load ('ci_sampled' or 'hpc_full'). 
              If None, loads the default mode specified in the config.
              
    Returns:
        Dict containing the configuration for the specified mode.
        
    Raises:
        FileNotFoundError: If config file is missing.
        KeyError: If requested mode is not found.
        yaml.YAMLError: If config file is malformed.
    """
    if not CONFIG_FILE_PATH.exists():
        logger.critical(f"Environment config file not found: {CONFIG_FILE_PATH}")
        raise FileNotFoundError(f"Environment config file not found: {CONFIG_FILE_PATH}")
    
    with open(CONFIG_FILE_PATH, 'r') as f:
        config_data = yaml.safe_load(f)
    
    if mode is None:
        mode = config_data.get('default_mode', 'ci_sampled')
    
    if mode not in config_data.get('modes', {}):
        available_modes = list(config_data['modes'].keys())
        logger.error(f"Mode '{mode}' not found. Available modes: {available_modes}")
        raise KeyError(f"Mode '{mode}' not found in configuration. Available: {available_modes}")
    
    logger.info(f"Loaded environment configuration for mode: {mode}")
    return config_data['modes'][mode]

def get_constraint(config: Dict[str, Any], constraint_name: str, default: Any = None) -> Any:
    """
    Retrieve a specific constraint value from the loaded configuration.
    
    Args:
        config: The loaded environment configuration dictionary.
        constraint_name: Name of the constraint (e.g., 'max_replicates_per_species').
        default: Default value if constraint is not found.
        
    Returns:
        The constraint value or default.
    """
    constraints = config.get('constraints', {})
    value = constraints.get(constraint_name, default)
    if value is None:
        logger.warning(f"Constraint '{constraint_name}' not found in mode '{config.get('description', 'unknown')}'. Using default: {default}")
    return value

def get_tool_param(config: Dict[str, Any], tool_name: str, param_name: str, default: Any = None) -> Any:
    """
    Retrieve a specific tool parameter from the loaded configuration.
    
    Args:
        config: The loaded environment configuration dictionary.
        tool_name: Name of the tool (e.g., 'star_params', 'suppa_params').
        param_name: Name of the parameter within the tool config.
        default: Default value if parameter is not found.
        
    Returns:
        The parameter value or default.
    """
    tool_params = config.get('data_sources', {}) or config.get('constraints', {})
    # Navigate nested params (e.g., config['constraints']['star_params']['runMode'])
    try:
        if tool_name in config:
            tool_config = config[tool_name]
            if isinstance(tool_config, dict):
                return tool_config.get(param_name, default)
    except (KeyError, TypeError):
        pass
    
    # Fallback to nested constraints if tool_name is not top-level
    constraints = config.get('constraints', {})
    if tool_name in constraints:
        tool_config = constraints[tool_name]
        if isinstance(tool_config, dict):
            return tool_config.get(param_name, default)
    
    logger.debug(f"Tool param '{tool_name}.{param_name}' not found. Using default: {default}")
    return default

def validate_replicate_count(config: Dict[str, Any], actual_count: int, species: str) -> bool:
    """
    Validate that the actual replicate count meets the mode's constraints.
    
    Args:
        config: The loaded environment configuration dictionary.
        actual_count: Number of replicates available.
        species: Species name for logging purposes.
        
    Returns:
        True if valid, False otherwise.
        
    Raises:
        ValueError: If constraints are violated.
    """
    min_rep = get_constraint(config, 'min_replicates_per_species', 1)
    max_rep = get_constraint(config, 'max_replicates_per_species', 10)
    is_ci = config.get('use_synthetic_data', False)
    
    if is_ci:
        # CI mode has relaxed validation
        if actual_count < 1:
            raise ValueError(f"CI Mode: {species} must have at least 1 replicate.")
        logger.info(f"CI Mode: {species} has {actual_count} replicate(s). Validation relaxed.")
        return True
    
    # Full HPC mode strict validation
    if actual_count < min_rep:
        raise ValueError(f"HPC Mode: {species} has {actual_count} replicates, but minimum required is {min_rep}.")
    if actual_count > max_rep:
        raise ValueError(f"HPC Mode: {species} has {actual_count} replicates, but maximum allowed is {max_rep}.")
    
    logger.info(f"HPC Mode: {species} has {actual_count} replicates. Validation passed.")
    return True

def main():
    """
    Main entry point for testing the environment configuration loader.
    """
    logger.info("Testing environment configuration loading...")
    
    # Test CI Mode
    try:
        ci_config = load_environment_config('ci_sampled')
        logger.info(f"CI Mode Constraints: max_rep={get_constraint(ci_config, 'max_replicates_per_species')}")
        logger.info(f"CI Mode STAR params: runMode={get_tool_param(ci_config, 'star_params', 'runMode')}")
        
        # Test validation
        validate_replicate_count(ci_config, 1, "Human")
    except Exception as e:
        logger.error(f"CI Mode test failed: {e}")
    
    # Test HPC Mode
    try:
        hpc_config = load_environment_config('hpc_full')
        logger.info(f"HPC Mode Constraints: min_rep={get_constraint(hpc_config, 'min_replicates_per_species')}, max_rep={get_constraint(hpc_config, 'max_replicates_per_species')}")
        
        # Test validation
        validate_replicate_count(hpc_config, 3, "Human")
        try:
            validate_replicate_count(hpc_config, 2, "Human")
        except ValueError as ve:
            logger.info(f"Expected validation error for HPC mode: {ve}")
            
    except Exception as e:
        logger.error(f"HPC Mode test failed: {e}")

if __name__ == "__main__":
    main()
