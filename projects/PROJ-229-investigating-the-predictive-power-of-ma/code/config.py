import os
import yaml
from pathlib import Path
from typing import Any, Dict, Optional

CONFIG_PATH = Path("config.yaml")

def load_config(path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Load configuration from a YAML file.
    
    Args:
        path: Path to the config file. Defaults to 'config.yaml' in project root.
    
    Returns:
        Dictionary containing configuration.
    
    Raises:
        FileNotFoundError: If the config file does not exist.
        yaml.YAMLError: If the file is not valid YAML.
    """
    if path is None:
        path = CONFIG_PATH
    
    if not path.exists():
        raise FileNotFoundError(f"Configuration file not found at {path}")
    
    with open(path, 'r') as f:
        return yaml.safe_load(f)

_config_cache: Optional[Dict[str, Any]] = None

def get_config() -> Dict[str, Any]:
    """
    Get the global configuration, loading it once if necessary.
    
    Returns:
        Configuration dictionary.
    """
    global _config_cache
    if _config_cache is None:
        _config_cache = load_config()
    return _config_cache

def save_config_template(path: Optional[Path] = None) -> None:
    """
    Save a default configuration template if no config exists.
    
    Args:
        path: Path to save the template. Defaults to 'config.yaml.template'.
    """
    if path is None:
        path = Path("config.yaml.template")
    
    template = {
        "project": {
            "name": "llmXive-phase-change",
            "version": "0.1.0",
            "random_seed": 42
        },
        "api_keys": {
            "materials_project": "",
            "nist": ""
        },
        "logging": {
            "level": "INFO",
            "file": "logs/pipeline.log"
        },
        "resources": {
            "max_memory_gb": 7,
            "time_limit_hours": 6
        }
    }
    
    with open(path, 'w') as f:
        yaml.dump(template, f, default_flow_style=False)
    print(f"Configuration template saved to {path}")
