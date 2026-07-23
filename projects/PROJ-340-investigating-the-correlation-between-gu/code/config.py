import os
import json
from pathlib import Path
from typing import Any, Dict, Optional

class Config:
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or 'data/config/config.json'
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        if os.path.exists(self.config_path):
            with open(self.config_path, 'r') as f:
                return json.load(f)
        return {}

    def get(self, key: str, default: Any = None) -> Any:
        return self.config.get(key, default)

def get_config() -> Config:
    return Config()

def load_config(path: str) -> Dict[str, Any]:
    with open(path, 'r') as f:
        return json.load(f)

if __name__ == "__main__":
    pass
