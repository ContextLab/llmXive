"""
Minimal configuration utilities.
"""
import os
import json

def get_config(config_path: str = "code/config.yaml"):
    """Load optional YAML config; returns empty dict if missing."""
    if not os.path.exists(config_path):
        return {}
    try:
        import yaml
    except ImportError:
        raise RuntimeError("PyYAML is required to load configuration files.")
    with open(config_path, "r") as f:
        return yaml.safe_load(f)

def validate_data_sources():
    """Placeholder for data source validation."""
    return True
