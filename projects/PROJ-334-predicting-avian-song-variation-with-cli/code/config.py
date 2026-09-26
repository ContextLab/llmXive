import os
import json
from pathlib import Path
from typing import Optional, Dict, Any, List
import yaml

class Config:
    """
    Base configuration loader for environment variables and paths.
    
    Handles:
    - Loading configuration from a YAML file (defaults to `config.yaml` in project root)
    - Overriding specific values via environment variables (e.g., XC_API_KEY)
    - Providing a configurable `join_radius_km` parameter (default 10km based on WorldClim resolution)
    - Resolving absolute paths for data, code, and logs directories
    """

    DEFAULT_CONFIG_PATH = "config.yaml"
    DEFAULT_JOIN_RADIUS_KM = 10.0  # Based on WorldClim v2.1 resolution (~1km) and spatial join tolerance

    def __init__(self, config_path: Optional[str] = None):
        self._config: Dict[str, Any] = {}
        self._base_path = Path.cwd()
        self._load_config(config_path)

    def _load_config(self, config_path: Optional[str]) -> None:
        """
        Load configuration from YAML file and override with environment variables.
        """
        path_str = config_path or os.getenv("CONFIG_PATH", self.DEFAULT_CONFIG_PATH)
        config_file = Path(path_str)

        if not config_file.is_absolute():
            config_file = self._base_path / config_file

        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    self._config = yaml.safe_load(f) or {}
            except yaml.YAMLError as e:
                raise RuntimeError(f"Failed to parse config file {config_file}: {e}")
        else:
            # Initialize with defaults if file doesn't exist
            self._config = {}

        # Apply environment variable overrides
        self._apply_env_overrides()

    def _apply_env_overrides(self) -> None:
        """
        Override config values with environment variables.
        Convention: Uppercase keys in env vars map to config keys.
        Example: XC_API_KEY -> config['xeno_canto']['api_key']
        """
        env_map = {
            "JOIN_RADIUS_KM": ("spatial", "join_radius_km"),
            "DATA_DIR": ("paths", "data_dir"),
            "CODE_DIR": ("paths", "code_dir"),
            "LOGS_DIR": ("paths", "logs_dir"),
            "XC_API_KEY": ("xeno_canto", "api_key"),
            "WC_URL_TEMPLATE": ("worldclim", "url_template"),
        }

        for env_key, config_path in env_map.items():
            value = os.getenv(env_key)
            if value is not None:
                self._set_nested_value(self._config, config_path, value)

    def _set_nested_value(self, config: Dict, path: List[str], value: Any) -> None:
        """Helper to set a value in a nested dict based on a path."""
        current = config
        for key in path[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        current[path[-1]] = value

    @property
    def join_radius_km(self) -> float:
        """
        Get the spatial join radius in kilometers.
        Defaults to 10.0km if not specified in config or env.
        """
        return float(self._config.get("spatial", {}).get("join_radius_km", self.DEFAULT_JOIN_RADIUS_KM))

    @property
    def data_dir(self) -> Path:
        """Get the absolute path to the data directory."""
        raw = self._config.get("paths", {}).get("data_dir", "data")
        path = Path(raw)
        if not path.is_absolute():
            path = self._base_path / path
        return path

    @property
    def code_dir(self) -> Path:
        """Get the absolute path to the code directory."""
        raw = self._config.get("paths", {}).get("code_dir", "code")
        path = Path(raw)
        if not path.is_absolute():
            path = self._base_path / path
        return path

    @property
    def logs_dir(self) -> Path:
        """Get the absolute path to the logs directory."""
        raw = self._config.get("paths", {}).get("logs_dir", "data/logs")
        path = Path(raw)
        if not path.is_absolute():
            path = self._base_path / path
        return path

    @property
    def xeno_canto_config(self) -> Dict[str, Any]:
        """Get Xeno-Canto specific configuration."""
        return self._config.get("xeno_canto", {})

    @property
    def worldclim_config(self) -> Dict[str, Any]:
        """Get WorldClim specific configuration."""
        return self._config.get("worldclim", {})

    def get(self, key: str, default: Any = None) -> Any:
        """Generic getter for nested keys using dot notation (e.g., 'paths.data_dir')."""
        keys = key.split('.')
        value = self._config
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        return value

    def to_dict(self) -> Dict[str, Any]:
        """Return the full configuration as a dictionary."""
        return self._config.copy()

# Global instance for convenience in scripts that don't need injection
_global_config: Optional[Config] = None

def load_config(config_path: Optional[str] = None) -> Config:
    """
    Load or retrieve the global configuration instance.
    Useful for scripts that need a consistent config object without passing it around.
    """
    global _global_config
    if _global_config is None or config_path is not None:
        _global_config = Config(config_path)
    return _global_config
