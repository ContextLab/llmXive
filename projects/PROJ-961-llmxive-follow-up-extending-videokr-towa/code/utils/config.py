import os
import random
import json
from pathlib import Path
from typing import Any, Dict, Optional, Union

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

def get_project_root() -> Path:
    return PROJECT_ROOT

def get_path(relative_path: str) -> Path:
    return PROJECT_ROOT / relative_path

def ensure_dir(path: Union[str, Path]) -> None:
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)

def set_seed(seed: int) -> None:
    random.seed(seed)
    # Set numpy seed if available
    try:
        import numpy as np
        np.random.seed(seed)
    except ImportError:
        pass

def get_config() -> Dict[str, Any]:
    config_path = get_path("config.json")
    if config_path.exists():
        with open(config_path, 'r') as f:
            return json.load(f)
    return {}

def main():
    print(f"Project root: {get_project_root()}")
    print(f"Config: {get_config()}")

if __name__ == "__main__":
    main()
