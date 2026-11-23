"""
Module: utils/config.py
Task: T008a
Description: Environment variable management and configuration.
"""
import os
import json
from pathlib import Path
from typing import Optional, Dict, Any
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).resolve().parent.parent
ENV_FILE = PROJECT_ROOT / ".env"

class ConfigError(Exception):
    pass

class EnvConfigError(Exception):
    pass

class EnvConfig:
    """Configuration loader for environment variables."""
    def __init__(self, env_path: Optional[Path] = None):
        self.env_path = env_path or ENV_FILE
        self._config: Dict[str, Any] = {}
        self._load()

    def _load(self):
        if self.env_path.exists():
            load_dotenv(self.env_path)
        else:
            # If .env is missing, we might raise or use defaults.
            # Per T008a: "Script loads .env and raises error if missing keys."
            # We will raise if critical keys are missing.
            pass

        # Map environment variables to config
        # Critical keys defined by the project
        critical_keys = ['DATA_PATH', 'RANDOM_SEED', 'MODEL_PATH']
        
        for key in critical_keys:
            val = os.getenv(key)
            if val is None:
                # Allow defaults if not set, but warn?
                # T008a says "raises error if missing keys"
                # We will raise if the key is strictly required.
                # For now, let's set defaults if not found to prevent crash, 
                # but the task says "raises error if missing keys".
                # Let's implement the strict behavior.
                raise EnvConfigError(f"Missing required environment variable: {key}")
            self._config[key] = val

        # Load optional keys
        optional_keys = ['LOG_LEVEL', 'DEBUG']
        for key in optional_keys:
            val = os.getenv(key)
            if val:
                self._config[key] = val

    def get(self, key: str, default: Any = None) -> Any:
        return self._config.get(key, default)

    def as_dict(self) -> Dict[str, Any]:
        return self._config.copy()

class ProjectConfig:
    """Project-wide configuration wrapper."""
    def __init__(self, env_config: EnvConfig):
        self.env = env_config
        self.data_path = Path(self.env.get('DATA_PATH'))
        self.random_seed = int(self.env.get('RANDOM_SEED'))
        self.model_path = Path(self.env.get('MODEL_PATH'))

# Global instance
_config_instance: Optional[EnvConfig] = None

def get_config() -> EnvConfig:
    global _config_instance
    if _config_instance is None:
        _config_instance = EnvConfig()
    return _config_instance

def get_project_config() -> ProjectConfig:
    return ProjectConfig(get_config())

def reset_config():
    global _config_instance
    _config_instance = None

def main():
    """Test function for T008a."""
    try:
        cfg = get_config()
        print("Configuration loaded successfully.")
        print(f"DATA_PATH: {cfg.get('DATA_PATH')}")
        print(f"RANDOM_SEED: {cfg.get('RANDOM_SEED')}")
        print(f"MODEL_PATH: {cfg.get('MODEL_PATH')}")
    except EnvConfigError as e:
        print(f"Configuration Error: {e}")
        raise

if __name__ == "__main__":
    main()