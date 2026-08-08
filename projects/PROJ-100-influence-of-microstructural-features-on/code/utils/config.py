import os
import random
import numpy as np
from typing import Dict, Any, Optional
import json

def set_seed(seed: int = 42) -> None:
    """Set random seeds for reproducibility."""
    os.environ['PYTHONHASHSEED'] = str(seed)
    random.seed(seed)
    np.random.seed(seed)

def get_config_value(key: str, default: Any = None) -> Any:
    """Retrieve a configuration value from environment or defaults."""
    return os.getenv(key, default)

def save_config(config: Dict[str, Any], path: str = "code/utils/project_config.json") -> None:
    """Saves the project configuration to a JSON file."""
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'w') as f:
        json.dump(config, f, indent=4)