import os
import json
from pathlib import Path
from typing import Optional, Dict, Any
from dotenv import load_dotenv

class ConfigError(Exception):
    pass

class EnvConfigError(Exception):
    pass

class EnvConfig:
    """Configuration loader for environment variables."""
    def __init__(self, env_path: Optional[str] = None):
        self.env_path = env_path or ".env"
        load_dotenv(self.env_path)
        self._config = {}

    def get(self, key: str, default: Any = None) -> Any:
        return os.getenv(key, default)

    def get_dict(self, key: str) -> Dict[str, Any]:
        val = self.get(key)
        if val is None:
            return {}
        try:
            return json.loads(val)
        except json.JSONDecodeError:
            return {}

class ProjectConfig:
    """Project-wide configuration."""
    def __init__(self):
        self.env_config = EnvConfig()
        self._paths = {
            "raw_data": self.env_config.get("RAW_DATA_PATH", "data/raw"),
            "processed_data": self.env_config.get("PROCESSED_DATA_PATH", "data/processed/merged_dataset.csv"),
            "results": self.env_config.get("RESULTS_PATH", "data/results"),
            "models": self.env_config.get("MODELS_PATH", "data/models"),
            "reference": self.env_config.get("REFERENCE_PATH", "data/reference")
        }

    @property
    def paths(self) -> Dict[str, str]:
        return self._paths

# Global config instance
_config: Optional[ProjectConfig] = None

def get_config() -> ProjectConfig:
    global _config
    if _config is None:
        _config = ProjectConfig()
    return _config

def get_project_config() -> ProjectConfig:
    return get_config()

def reset_config():
    global _config
    _config = None

def main():
    config = get_config()
    print("Project Configuration:")
    print(json.dumps(config.paths, indent=2))

if __name__ == "__main__":
    main()
