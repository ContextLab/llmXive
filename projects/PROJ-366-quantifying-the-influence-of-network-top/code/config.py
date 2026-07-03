import os
import yaml
from typing import Any, Dict, Optional
from pathlib import Path

class Config:
    """
    Configuration manager for the llmXive pipeline.
    Loads settings from code/config.yaml and provides typed accessors.
    """

    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or Path("code/config.yaml")
        self._config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        if not self.config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")
        with open(self.config_path, 'r') as f:
            return yaml.safe_load(f)

    def get(self, key: str, default: Any = None) -> Any:
        keys = key.split('.')
        value = self._config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value

    def get_paths(self) -> Dict[str, Path]:
        """Returns a dictionary of important paths as Path objects."""
        base = Path(self.get("paths.base", "."))
        return {
            "raw": base / self.get("paths.raw", "data/raw"),
            "processed_graphs": base / self.get("paths.processed_graphs", "data/processed/graphs"),
            "processed_conductivities": base / self.get("paths.processed_conductivities", "data/processed/conductivities"),
            "model_outputs": base / self.get("paths.model_outputs", "data/processed/model_outputs"),
            "checksums": base / self.get("paths.checksums", "data/checksums.json"),
            "contracts": base / self.get("paths.contracts", "contracts"),
        }

    def get_simulation_config(self) -> Dict[str, Any]:
        """Returns simulation-specific settings."""
        return self.get("simulation", {})

    def get_gnn_hyperparameters(self) -> Dict[str, Any]:
        """Returns GNN hyperparameters."""
        return self.get("gnn", {})

# Singleton instance
_config_instance: Optional[Config] = None

def get_config() -> Config:
    global _config_instance
    if _config_instance is None:
        _config_instance = Config()
    return _config_instance

def get_config_value(key: str, default: Any = None) -> Any:
    return get_config().get(key, default)

def get_simulation_config() -> Dict[str, Any]:
    return get_config().get_simulation_config()

def get_gnn_hyperparameters() -> Dict[str, Any]:
    return get_config().get_gnn_hyperparameters()

def get_paths() -> Dict[str, Path]:
    return get_config().get_paths()
