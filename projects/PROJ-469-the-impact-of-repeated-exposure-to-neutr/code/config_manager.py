"""
Environment configuration management for llmXive project.

This module provides centralized configuration loading and validation.
It supports both .env files (via python-dotenv) and config.yaml files.
"""
import os
import yaml
from pathlib import Path
from typing import Any, Dict, Optional
from dotenv import load_dotenv
from config import ensure_dirs
from logging_config import get_logger

logger = get_logger(__name__)

# Default paths
ENV_FILE_PATH = ".env"
CONFIG_FILE_PATH = "config.yaml"
DEFAULT_DATA_PATH = "data/raw"
DEFAULT_PROCESSED_PATH = "data/processed"
DEFAULT_RESULTS_PATH = "results"
DEFAULT_LOGS_PATH = "logs"

def load_env_file(env_path: Optional[str] = None) -> Dict[str, str]:
    """
    Load environment variables from a .env file.
    
    Args:
        env_path: Path to the .env file. Defaults to ENV_FILE_PATH.
        
    Returns:
        Dictionary of environment variables loaded.
    """
    if env_path is None:
        env_path = ENV_FILE_PATH
        
    env_vars = {}
    if Path(env_path).exists():
        load_dotenv(env_path)
        logger.info(f"Loaded environment variables from {env_path}")
        # Extract loaded variables
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, _, value = line.partition('=')
                    env_vars[key.strip()] = value.strip()
    else:
        logger.warning(f"Environment file not found at {env_path}. Using system defaults.")
        
    return env_vars

def load_config_file(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load configuration from a YAML file.
    
    Args:
        config_path: Path to the config.yaml file. Defaults to CONFIG_FILE_PATH.
        
    Returns:
        Dictionary of configuration values.
    """
    if config_path is None:
        config_path = CONFIG_FILE_PATH
        
    config = {}
    if Path(config_path).exists():
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f) or {}
        logger.info(f"Loaded configuration from {config_path}")
    else:
        logger.warning(f"Configuration file not found at {config_path}. Using defaults.")
        
    return config

def merge_configs(env_vars: Dict[str, str], config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge environment variables and YAML config, with env vars taking precedence.
    
    Args:
        env_vars: Dictionary from .env file.
        config: Dictionary from config.yaml.
        
    Returns:
        Merged configuration dictionary.
    """
    merged = config.copy()
    
    # Map common env vars to config keys
    env_mapping = {
        'DATA_RAW_PATH': 'data.raw_path',
        'DATA_PROCESSED_PATH': 'data.processed_path',
        'RESULTS_PATH': 'results.path',
        'LOGS_PATH': 'logs.path',
        'RANDOM_SEED': 'analysis.seed',
        'ALPHA_LEVEL': 'analysis.alpha',
    }
    
    for env_key, config_key in env_mapping.items():
        if env_key in env_vars:
            # Parse nested keys like 'data.raw_path'
            keys = config_key.split('.')
            current = merged
            for k in keys[:-1]:
                if k not in current:
                    current[k] = {}
                current = current[k]
            # Set the final value
            current[keys[-1]] = env_vars[env_key]
            
    return merged

def get_config() -> Dict[str, Any]:
    """
    Get the full configuration by loading and merging .env and config.yaml.
    
    Returns:
        Complete configuration dictionary with defaults applied.
    """
    # Load sources
    env_vars = load_env_file()
    config = load_config_file()
    
    # Merge
    merged = merge_configs(env_vars, config)
    
    # Apply defaults
    defaults = {
        'data': {
            'raw_path': DEFAULT_DATA_PATH,
            'processed_path': DEFAULT_PROCESSED_PATH,
        },
        'results': {
            'path': DEFAULT_RESULTS_PATH,
        },
        'logs': {
            'path': DEFAULT_LOGS_PATH,
        },
        'analysis': {
            'seed': 42,
            'alpha': 0.05,
            'bootstrap_count': 1000,
        }
    }
    
    def deep_merge(base: Dict, override: Dict) -> Dict:
        result = base.copy()
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = deep_merge(result[key], value)
            else:
                result[key] = value
        return result
        
    final_config = deep_merge(defaults, merged)
    
    # Ensure directories exist
    ensure_dirs()
    
    logger.info("Configuration loaded successfully")
    return final_config

def get_path(key: str, config: Optional[Dict[str, Any]] = None) -> Path:
    """
    Get a path from configuration.
    
    Args:
        key: Configuration key (e.g., 'data.raw_path', 'results.path').
        config: Optional config dict. If None, loads fresh config.
        
    Returns:
        Path object.
    """
    if config is None:
        config = get_config()
        
    keys = key.split('.')
    value = config
    for k in keys:
        if isinstance(value, dict) and k in value:
            value = value[k]
        else:
            raise KeyError(f"Configuration key '{key}' not found")
            
    return Path(value)

# Convenience functions for common paths
def get_data_raw_path(config: Optional[Dict[str, Any]] = None) -> Path:
    return get_path('data.raw_path', config)

def get_data_processed_path(config: Optional[Dict[str, Any]] = None) -> Path:
    return get_path('data.processed_path', config)

def get_results_path(config: Optional[Dict[str, Any]] = None) -> Path:
    return get_path('results.path', config)

def get_logs_path(config: Optional[Dict[str, Any]] = None) -> Path:
    return get_path('logs.path', config)

def get_analysis_seed(config: Optional[Dict[str, Any]] = None) -> int:
    return int(get_path('analysis.seed', config))

def get_alpha_level(config: Optional[Dict[str, Any]] = None) -> float:
    return float(get_path('analysis.alpha', config))

def get_bootstrap_count(config: Optional[Dict[str, Any]] = None) -> int:
    return int(get_path('analysis.bootstrap_count', config))

def create_sample_env_file(path: str = ".env.example") -> None:
    """Create a sample .env file for reference."""
    content = """# Environment Configuration for llmXive Project
# Copy this file to .env and modify as needed

# Data Paths
DATA_RAW_PATH=data/raw
DATA_PROCESSED_PATH=data/processed

# Results and Logs
RESULTS_PATH=results
LOGS_PATH=logs

# Analysis Parameters
RANDOM_SEED=42
ALPHA_LEVEL=0.05
"""
    with open(path, 'w') as f:
        f.write(content)
    logger.info(f"Created sample environment file at {path}")

def create_sample_config_file(path: str = "config.yaml.example") -> None:
    """Create a sample config.yaml file for reference."""
    content = """# Configuration for llmXive Project
# Copy this file to config.yaml and modify as needed

data:
  raw_path: data/raw
  processed_path: data/processed

results:
  path: results

logs:
  path: logs

analysis:
  seed: 42
  alpha: 0.05
  bootstrap_count: 1000
"""
    with open(path, 'w') as f:
        f.write(content)
    logger.info(f"Created sample config file at {path}")

if __name__ == "__main__":
    # Demonstrate configuration loading
    print("Creating sample configuration files...")
    create_sample_env_file()
    create_sample_config_file()
    
    print("\nLoading configuration...")
    config = get_config()
    print(f"Data Raw Path: {get_data_raw_path(config)}")
    print(f"Data Processed Path: {get_data_processed_path(config)}")
    print(f"Results Path: {get_results_path(config)}")
    print(f"Logs Path: {get_logs_path(config)}")
    print(f"Analysis Seed: {get_analysis_seed(config)}")
    print(f"Alpha Level: {get_alpha_level(config)}")
    print(f"Bootstrap Count: {get_bootstrap_count(config)}")