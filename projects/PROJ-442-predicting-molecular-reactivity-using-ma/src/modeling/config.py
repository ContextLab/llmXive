import os
import yaml
from pathlib import Path
from typing import Dict, Any

CONFIG_PATH = Path("src/modeling/config.yaml")

def load_config() -> Dict[str, Any]:
    """
    Load configuration from the YAML file.
    Returns an empty dict if the file is missing or invalid.
    """
    if not CONFIG_PATH.exists():
        # Return a default structure if config is missing
        return {
            "reaction_templates": {},
            "training": {},
            "data": {}
        }
    
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        try:
            return yaml.safe_load(f) or {}
        except yaml.YAMLError as e:
            print(f"Error loading config file: {e}")
            return {}
