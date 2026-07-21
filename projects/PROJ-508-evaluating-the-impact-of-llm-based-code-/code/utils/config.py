import os
from pathlib import Path
from typing import Optional, Dict, Any
import json

class Config:
    def __init__(self, config_dict: Optional[Dict[str, Any]] = None):
        self.config_dict = config_dict or {}
        self._load_from_env()
    
    def _load_from_env(self):
        self.github_token = os.getenv("GITHUB_TOKEN", "")
        self.project_root = os.getenv("PROJECT_ROOT", str(Path(__file__).parent.parent.parent))
        self.repo_list_path = os.getenv("REPO_LIST_PATH", "")
        self.default_repo_list = os.getenv("DEFAULT_REPO_LIST", "").split(",") if os.getenv("DEFAULT_REPO_LIST") else []
    
    def get(self, key: str, default: Any = None) -> Any:
        if key == "github_token":
            return self.github_token
        elif key == "project_root":
            return self.project_root
        elif key == "repo_list_path":
            return self.repo_list_path or self.config_dict.get("repo_list_path", "")
        elif key == "default_repo_list":
            return self.default_repo_list or self.config_dict.get("default_repo_list", [])
        return self.config_dict.get(key, default)

_config_instance: Optional[Config] = None

def get_config() -> Config:
    global _config_instance
    if _config_instance is None:
        _config_instance = Config()
    return _config_instance
