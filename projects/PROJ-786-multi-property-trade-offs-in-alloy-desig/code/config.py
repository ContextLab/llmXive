import os
import argparse
from pathlib import Path
from dotenv import load_dotenv
import logging
import yaml

from utils.logging_config import log_info_with_context

# Global config
_config = {}

def load_environment():
    """Loads .env file if present."""
    load_dotenv()

def parse_cli_args():
    parser = argparse.ArgumentParser(description="Alloy Design Pipeline")
    parser.add_argument("--config", type=str, default="config.yaml", help="Path to config file")
    return parser.parse_args()

def get_config() -> dict:
    global _config
    if _config:
        return _config
    
    args = parse_cli_args()
    load_environment()
    
    config_path = Path(args.config)
    if config_path.exists():
        with open(config_path, 'r') as f:
            _config = yaml.safe_load(f)
    else:
        # Default config
        _config = {
            "data_source": "OQMD/elastic_properties",
            "raw_data_path": "data/raw/oqmd_data.csv",
            "processed_dir": "data/processed",
            "variance_threshold": 0.5,
            "random_seed": 42
        }
    
    return _config

def verify_config(config: dict):
    """Validates required keys in config."""
    required_keys = ["data_source", "processed_dir"]
    for key in required_keys:
        if key not in config:
            raise ValueError(f"Missing required config key: {key}")
    log_info_with_context("Configuration verified", context="config")
