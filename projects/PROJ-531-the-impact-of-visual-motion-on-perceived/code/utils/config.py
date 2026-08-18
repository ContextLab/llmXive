import os
from pathlib import Path
from typing import Optional, Dict, Any
import json

class ConfigManager:
    """
    Manages environment variables and configuration for the project.
    Handles API keys, data paths, and project settings.
    """
    
    def __init__(self, env_file: Optional[Path] = None):
        self.project_root = Path(__file__).resolve().parents[2]
        self.env_file = env_file or self.project_root / ".env"
        self._config: Dict[str, Any] = {}
        self._load_env()
        self._load_defaults()

    def _load_env(self) -> None:
        """Load environment variables from .env file if it exists."""
        if self.env_file.exists():
            with open(self.env_file, "r") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, value = line.split("=", 1)
                        # Remove quotes if present
                        value = value.strip('"').strip("'")
                        os.environ[key] = value

    def _load_defaults(self) -> None:
        """Set default values for configuration if not already set."""
        defaults = {
            "DATA_PATH_RAW": "data/raw",
            "DATA_PATH_PROCESSED": "data/processed",
            "DATA_PATH_RESULTS": "data/results",
            "FIGURES_PATH": "data/results/plots",
            "LOG_PATH": "logs",
            "API_KEY_OPENML": "",
            "API_KEY_HF": "",
            "DEBUG_MODE": "False",
            "RANDOM_SEED": "42"
        }
        
        for key, default_val in defaults.items():
            if key not in os.environ:
                os.environ[key] = default_val

    def get(self, key: str, default: Optional[Any] = None) -> Any:
        """Get a configuration value by key."""
        value = os.environ.get(key, default)
        
        # Type conversion for common types
        if value is not None:
            if value.lower() in ("true", "false"):
                return value.lower() == "true"
            try:
                return int(value)
            except ValueError:
                try:
                    return float(value)
                except ValueError:
                    return value
        return value

    def get_path(self, key: str) -> Path:
        """Get a configuration value as a Path object."""
        path_str = self.get(key)
        if path_str is None:
            raise ValueError(f"Path configuration '{key}' is not set")
        
        path = Path(path_str)
        if not path.is_absolute():
            path = self.project_root / path
        return path

    def ensure_dirs(self) -> None:
        """Ensure all configured directories exist."""
        dirs = [
            self.get_path("DATA_PATH_RAW"),
            self.get_path("DATA_PATH_PROCESSED"),
            self.get_path("DATA_PATH_RESULTS"),
            self.get_path("FIGURES_PATH"),
            self.get_path("LOG_PATH")
        ]
        for dir_path in dirs:
            dir_path.mkdir(parents=True, exist_ok=True)

    def validate_api_keys(self) -> Dict[str, bool]:
        """
        Validate that required API keys are present.
        Returns a dict of key_name: is_valid
        """
        results = {}
        api_keys = ["API_KEY_OPENML", "API_KEY_HF"]
        for key in api_keys:
            val = self.get(key)
            results[key] = bool(val and len(val) > 0)
        return results

    def to_dict(self) -> Dict[str, Any]:
        """Return current configuration as a dictionary."""
        return {
            "project_root": str(self.project_root),
            "data_raw": str(self.get_path("DATA_PATH_RAW")),
            "data_processed": str(self.get_path("DATA_PATH_PROCESSED")),
            "data_results": str(self.get_path("DATA_PATH_RESULTS")),
            "figures": str(self.get_path("FIGURES_PATH")),
            "log_path": str(self.get_path("LOG_PATH")),
            "debug_mode": self.get("DEBUG_MODE"),
            "random_seed": self.get("RANDOM_SEED"),
            "api_keys_valid": self.validate_api_keys()
        }

    def save_config(self, output_path: Optional[Path] = None) -> Path:
        """Save current configuration to a JSON file."""
        if output_path is None:
            output_path = self.project_root / "config_snapshot.json"
        
        config_dict = self.to_dict()
        with open(output_path, "w") as f:
            json.dump(config_dict, f, indent=2)
        
        return output_path


def get_config(env_file: Optional[Path] = None) -> ConfigManager:
    """
    Factory function to get a ConfigManager instance.
    
    Args:
        env_file: Optional path to .env file. If None, looks for .env in project root.
    
    Returns:
        ConfigManager instance with loaded configuration.
    """
    return ConfigManager(env_file=env_file)
