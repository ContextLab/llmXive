import os
import json
import random
import numpy as np
from pathlib import Path
from typing import Any, Dict, Optional, Union

CONFIG_PATH = Path(__file__).parent / "config.yaml"

class Config:
    def __init__(self, data: Dict[str, Any]):
        self._data = data
        self._root = Path(__file__).parent
        self._base_path = self._root.parent

    @property
    def random_seed(self) -> int:
        return self._data.get("random_seed", 42)

    @property
    def data_path(self) -> Path:
        return self._base_path / Path(self._data.get("data_path", "data"))

    @property
    def output_path(self) -> Path:
        return self._base_path / Path(self._data.get("output_path", "data/outputs"))

    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, default)

    def __getitem__(self, key: str) -> Any:
        return self._data[key]

    def __contains__(self, key: str) -> bool:
        return key in self._data

_global_config: Optional[Config] = None

def load_config(path: Optional[Path] = None) -> Config:
    global _global_config
    if path is None:
        path = CONFIG_PATH
    
    if not path.exists():
        raise FileNotFoundError(f"Config file not found at {path}")
    
    with open(path, 'r') as f:
        data = yaml.safe_load(f)
    
    _global_config = Config(data)
    return _global_config

def set_global_seed(seed: Optional[int] = None) -> None:
    config = get_config()
    if seed is None:
        seed = config.random_seed
    
    random.seed(seed)
    np.random.seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)

def get_config() -> Config:
    global _global_config
    if _global_config is None:
        _global_config = load_config()
    return _global_config

def get_path(*args: Any, create: bool = False, **kwargs: Any) -> Path:
    """
    Flexible path resolver supporting multiple call signatures:
    
    1. get_path(config, "processed", "dataset_cleaned.csv") -> config.data_path / "processed" / "dataset_cleaned.csv"
    2. get_path(config, "outputs", create=True) -> config.output_path / "outputs" (created if needed)
    3. get_path("config.yaml") -> returns Path to config.yaml
    4. get_path("data/processed") -> returns Path relative to project root
    5. get_path("data/outputs") -> returns Path relative to project root
    6. get_path() -> returns project root
    """
    config = get_config()
    
    if not args:
        return Path(__file__).parent.parent
    
    first_arg = args[0]
    
    # Case: get_path("config.yaml") or get_path("data/processed")
    if isinstance(first_arg, str):
        # Check if it's a config key lookup (e.g., "data_path", "output_path")
        if first_arg in config:
            val = config[first_arg]
            base = Path(val) if isinstance(val, str) else val
            if len(args) > 1:
                return base / Path(args[1])
            return base
        
        # Otherwise treat as relative path
        base_path = Path(__file__).parent.parent
        result = base_path / first_arg
        if create:
            result.mkdir(parents=True, exist_ok=True)
        return result
    
    # Case: get_path(config, "processed", "dataset_cleaned.csv")
    if isinstance(first_arg, Config):
        base = config.data_path if len(args) == 1 else config.output_path
        if len(args) == 1:
            return base
        
        # Determine base from second argument if it looks like a subdirectory key
        second_arg = args[1]
        if second_arg in ["data_path", "output_path", "processed", "raw", "outputs", "logs"]:
            if second_arg == "data_path":
                base = config.data_path
            elif second_arg == "output_path":
                base = config.output_path
            elif second_arg == "processed":
                base = config.data_path / "processed"
            elif second_arg == "raw":
                base = config.data_path / "raw"
            elif second_arg == "outputs":
                base = config.output_path
            elif second_arg == "logs":
                base = config.data_path / "logs"
            else:
                base = config.data_path / second_arg
            
            if len(args) > 2:
                result = base / args[2]
            else:
                result = base
        else:
            # Fallback: treat second arg as subdirectory
            base = config.data_path
            result = base / second_arg
            if len(args) > 2:
                result = result / args[2]
        
        if create:
            result.mkdir(parents=True, exist_ok=True)
        return result
    
    raise ValueError(f"Unsupported get_path signature with args: {args}")

def get_config_path() -> Path:
    return CONFIG_PATH

# Import yaml here to avoid circular issues if loaded at module level
import yaml
