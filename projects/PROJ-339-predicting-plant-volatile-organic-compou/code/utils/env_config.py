import os
import json
from pathlib import Path
from typing import Optional, Dict, Any
from dotenv import load_dotenv

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

# Global config instance
_config: Optional[EnvConfig] = None

def get_config(env_path: Optional[str] = None) -> EnvConfig:
    global _config
    if _config is None or (env_path and _config.env_path != env_path):
        _config = EnvConfig(env_path)
    return _config

def reset_config():
    global _config
    _config = None

def main():
    config = get_config()
    print("Environment Config:")
    for key in os.environ:
        print(f"{key}: {config.get(key)}")

if __name__ == "__main__":
    main()
