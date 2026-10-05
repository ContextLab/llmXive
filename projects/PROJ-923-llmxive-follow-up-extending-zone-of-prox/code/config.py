import os
import yaml
from pathlib import Path
from typing import Any, Dict, Optional

class Config:
    def __init__(self, config_path: Optional[str] = None):
        self.path = config_path or "config.yaml"
        self.data: Dict[str, Any] = {}
        self._load()

    def _load(self):
        if os.path.exists(self.path):
            with open(self.path, 'r') as f:
                self.data = yaml.safe_load(f) or {}
        else:
            # Defaults
            self.data = {
                "alpha": 0.1,
                "initial_candidate_pool_size": 10,
                "epsilon": 0.05,
                "num_cycles": 50,
                "batch_size": 32,
                "seed": 42
            }

    @property
    def alpha(self) -> float:
        return float(self.data.get("alpha", 0.1))

    @property
    def initial_candidate_pool_size(self) -> int:
        return int(self.data.get("initial_candidate_pool_size", 10))

    @property
    def epsilon(self) -> float:
        return float(self.data.get("epsilon", 0.05))

    @property
    def num_cycles(self) -> int:
        return int(self.data.get("num_cycles", 50))

    @property
    def seed(self) -> int:
        return int(self.data.get("seed", 42))

_global_config: Optional[Config] = None

def get_config() -> Config:
    global _global_config
    if _global_config is None:
        _global_config = Config()
    return _global_config

def reload_config(path: Optional[str] = None):
    global _global_config
    _global_config = Config(path)
