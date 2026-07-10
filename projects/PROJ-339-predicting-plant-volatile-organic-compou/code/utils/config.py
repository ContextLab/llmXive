"""
Configuration management utilities.
Implements T008.
"""
import os
from pathlib import Path
from typing import Optional, Dict, Any
from dotenv import load_dotenv

class ConfigError(Exception):
    pass

class ProjectConfig:
    def __init__(self, env_path: Optional[Path] = None):
        load_dotenv(dotenv_path=env_path)
        self.root = Path(__file__).resolve().parent.parent.parent
        self.data_raw = self.root / "data" / "raw"
        self.data_processed = self.root / "data" / "processed"
        self.data_results = self.root / "data" / "results"
        self.data_models = self.root / "data" / "models"
        self.seed = int(os.getenv("RANDOM_SEED", "42"))

_config: Optional[ProjectConfig] = None

def get_config() -> ProjectConfig:
    global _config
    if _config is None:
        _config = ProjectConfig()
    return _config

def reset_config():
    global _config
    _config = None
