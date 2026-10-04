"""
Configuration management for the project.
Loads settings from YAML files and environment variables.
"""
import os
import yaml
from pathlib import Path
from typing import Dict, Any, List

PROJECT_ROOT = Path('code')
CONFIG_FILE = PROJECT_ROOT / 'specs' / 'config.yaml'

def load_config() -> Dict[str, Any]:
    """
    Load configuration from YAML file.
    
    Returns:
        Dict[str, Any]: Configuration dictionary.
    """
    config = {
        'THRESHOLD_DATA_SCARCITY': 120,
        'PSI4_BASIS': 'sto-3g',
        'CUTOFF_RANGE': [3.0, 3.5, 4.0]
    }

    if CONFIG_FILE.exists():
        try:
            with open(CONFIG_FILE, 'r') as f:
                file_config = yaml.safe_load(f)
                if file_config:
                    config.update(file_config)
        except Exception as e:
            print(f"Warning: Failed to load config file {CONFIG_FILE}: {e}. Using defaults.")
    else:
        print(f"Warning: Config file {CONFIG_FILE} not found. Using defaults.")

    # Override with environment variables if present
    for key in config:
        env_key = key.upper()
        if env_key in os.environ:
            value = os.environ[env_key]
            # Try to parse as int, float, or bool if possible
            try:
                if '.' in value:
                    config[key] = float(value)
                elif value.lower() in ['true', 'false']:
                    config[key] = value.lower() == 'true'
                else:
                    config[key] = int(value)
            except ValueError:
                config[key] = value

    return config

# Global config instance
config = load_config()

if __name__ == "__main__":
    import json
    print(json.dumps(config, indent=2))
