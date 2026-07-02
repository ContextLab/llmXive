"""
Configuration loader for the project.

Handles environment variables, random seeds, and thresholds.
"""
import os
import yaml
from typing import Optional, Dict, Any

class Config:
    """Configuration container."""
    def __init__(self, data: Dict[str, Any]):
        self._data = data
    
    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)

def get_config(config_path: Optional[str] = None) -> Config:
    """
    Load configuration from a YAML file or environment variables.
    
    Args:
        config_path: Optional path to a config.yaml file.
    
    Returns:
        A Config object.
    """
    # Default configuration values
    default_config = {
        "min_sample_count": 10,
        "ingestion_success_threshold": 0.8,
        "random_seed": 42,
        "missing_metric_columns": ["PCE", "J_sc", "V_oc"]
    }

    if config_path and os.path.exists(config_path):
        with open(config_path, 'r') as f:
            file_config = yaml.safe_load(f)
            if file_config:
                default_config.update(file_config)

    # Override with environment variables if present
    for key, value in os.environ.items():
        if key.startswith("PROJ_204_"):
            clean_key = key.replace("PROJ_204_", "").lower()
            try:
                # Try to parse as int or float
                if '.' in value:
                    default_config[clean_key] = float(value)
                else:
                    default_config[clean_key] = int(value)
            except ValueError:
                default_config[clean_key] = value

    return Config(default_config)