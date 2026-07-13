import os
import json
from pathlib import Path
from typing import Any, Dict, Optional

CONFIG_PATH = Path(__file__).parent / "config.json"

class Config:
    def __init__(self, data: Dict[str, Any]):
        self._data = data

    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)

def load_config() -> Config:
    """Load configuration from config.json or return defaults."""
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "r") as f:
            data = json.load(f)
        return Config(data)
    
    # Default configuration if file missing
    default_config = {
        "paths": {
            "raw_data": "data/raw",
            "processed_data": "data/processed",
            "outputs": "data/outputs",
            "figures": "figures"
        },
        "random_seed": 42
    }
    return Config(default_config)

def set_global_seed(seed: Optional[int] = None) -> None:
    """Set global random seed for reproducibility."""
    if seed is None:
        config = load_config()
        seed = config.get("random_seed", 42)
    
    import random
    import numpy as np
    
    random.seed(seed)
    np.random.seed(seed)
    
    try:
        import torch
        torch.manual_seed(seed)
    except ImportError:
        pass
