import os
import argparse
from pathlib import Path
from dotenv import load_dotenv
import logging
import yaml

from utils.logging_config import log_info_with_context

# Global config
_config = {}

# Global constants exposed as per task requirements
variance_threshold = None
random_seed = None
data_source = None

def load_environment():
    """
    Loads .env file if present.
    Gracefully handles missing .env files.
    """
    load_dotenv(override=True)

def _load_defaults():
    """
    Loads default configuration from config_default.yaml.
    Returns a dictionary of default settings.
    """
    default_path = Path("config_default.yaml")
    if default_path.exists():
        with open(default_path, 'r') as f:
            return yaml.safe_load(f)
    # Fallback defaults if file missing
    return {
        "data_source": "OQMD/elastic_properties",
        "raw_data_path": "data/raw/oqmd_data.csv",
        "processed_dir": "data/processed",
        "variance_threshold": 0.5,
        "random_seed": 42
    }

def parse_cli_args():
    parser = argparse.ArgumentParser(description="Alloy Design Pipeline")
    parser.add_argument("--config", type=str, default="config.yaml", help="Path to config file")
    return parser.parse_args()

def get_config() -> dict:
    global _config, variance_threshold, random_seed, data_source
    
    if _config:
        # Update global constants if config was already loaded
        variance_threshold = _config.get("variance_threshold", 0.5)
        random_seed = _config.get("random_seed", 42)
        data_source = _config.get("data_source", "OQMD/elastic_properties")
        return _config
    
    args = parse_cli_args()
    load_environment()
    
    config_path = Path(args.config)
    
    # Load defaults first
    config = _load_defaults()
    
    # Override with user-provided config file if it exists
    if config_path.exists():
        with open(config_path, 'r') as f:
            user_config = yaml.safe_load(f)
            if user_config:
                config.update(user_config)
    
    _config = config
    
    # Update global constants
    variance_threshold = _config.get("variance_threshold", 0.5)
    random_seed = _config.get("random_seed", 42)
    data_source = _config.get("data_source", "OQMD/elastic_properties")
    
    return _config

def verify_config(config: dict):
    """Validates required keys in config."""
    required_keys = ["data_source", "processed_dir"]
    for key in required_keys:
        if key not in config:
            raise ValueError(f"Missing required config key: {key}")
    log_info_with_context("Configuration verified", context="config")
