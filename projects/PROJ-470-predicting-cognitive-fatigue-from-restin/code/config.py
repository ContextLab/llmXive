"""Configuration loader for the pipeline."""
import yaml
from pathlib import Path

CONFIG_PATH = Path("code/config.yaml")

def load_config():
    """Load the YAML configuration file."""
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(f"Configuration file not found: {CONFIG_PATH}")
    
    with open(CONFIG_PATH, 'r') as f:
        return yaml.safe_load(f)
