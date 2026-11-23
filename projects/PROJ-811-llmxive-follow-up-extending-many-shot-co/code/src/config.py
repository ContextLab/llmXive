"""
Configuration management for the project.
Loads settings from environment variables or YAML config files.
"""
import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional
import logging
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Project root is the directory containing the project
PROJECT_ROOT = Path(__file__).parent.parent.parent

class Config:
    """Singleton configuration manager."""
    _instance = None
    _config = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
            cls._instance._load_config()
        return cls._instance

    def _load_config(self):
        """Load configuration from .env and config.yaml."""
        # Load .env if it exists
        env_path = PROJECT_ROOT / ".env"
        if env_path.exists():
            load_dotenv(env_path)
        
        # Default configuration
        self._config = {
            "dataset": {
                "name": os.getenv("DATASET_NAME", "aaabiao/DAG_sft"),
                "split": os.getenv("DATASET_SPLIT", "train"),
            },
            "seeds": [int(s) for s in os.getenv("SEEDS", "0 1 2 3 4 5 6 7 8 9").split()],
            "paths": {
                "data_raw": PROJECT_ROOT / "data" / "raw",
                "data_processed": PROJECT_ROOT / "data" / "processed",
                "data_results": PROJECT_ROOT / "data" / "results",
                "artifacts": PROJECT_ROOT / "artifacts",
            }
        }
        
        # Try to load config.yaml if it exists
        config_path = PROJECT_ROOT / "config.yaml"
        if config_path.exists():
            try:
                with open(config_path, 'r') as f:
                    yaml_config = yaml.safe_load(f)
                    if yaml_config:
                        self._update_nested(self._config, yaml_config)
            except Exception as e:
                logger.warning(f"Failed to load config.yaml: {e}")

    def _update_nested(self, base: Dict, update: Dict):
        """Recursively update a nested dictionary."""
        for key, value in update.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._update_nested(base[key], value)
            else:
                base[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value using dot notation."""
        keys = key.split('.')
        value = self._config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value

    def get_dataset_name(self) -> str:
        """Get the dataset name."""
        return self._config["dataset"]["name"]

    def get_seeds(self) -> List[int]:
        """Get the list of seeds."""
        return self._config["seeds"]

    def get_processed_dir(self) -> Path:
        """Get the processed data directory."""
        return self._config["paths"]["data_processed"]

    def to_dict(self) -> Dict[str, Any]:
        """Return the configuration as a dictionary."""
        return self._config

def get_config() -> Config:
    """Get the global config instance."""
    return Config()
