import os
import yaml
from pathlib import Path
from typing import Any, Dict, Optional
import sys
from pathlib import Path as PathLib

# Default configuration
_DEFAULT_CONFIG = {
    'SEED': 42,
    'DATA_PATH': 'data/raw',
    'OUTPUT_PATH': 'data/processed',
    'BENCHMARK_ACCURACY': 65.0,  # Per Constitution Principle VII
    'RAM_LIMIT_GB': 7.0,
    'CPU_LIMIT': 2
}

_config_instance = _DEFAULT_CONFIG.copy()

def get_default_config() -> Dict[str, Any]:
    return _DEFAULT_CONFIG.copy()

def get_env_config() -> Dict[str, Any]:
    # Override with environment variables if present
    env_config = {}
    if 'SEED' in os.environ:
        env_config['SEED'] = int(os.environ['SEED'])
    if 'DATA_PATH' in os.environ:
        env_config['DATA_PATH'] = os.environ['DATA_PATH']
    if 'OUTPUT_PATH' in os.environ:
        env_config['OUTPUT_PATH'] = os.environ['OUTPUT_PATH']
    if 'BENCHMARK_ACCURACY' in os.environ:
        env_config['BENCHMARK_ACCURACY'] = float(os.environ['BENCHMARK_ACCURACY'])
    return env_config

def deep_merge(base: Dict, override: Dict) -> Dict:
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result

def load_config(path: Optional[str] = None) -> Dict[str, Any]:
    if path and os.path.exists(path):
        with open(path, 'r') as f:
            file_config = yaml.safe_load(f) or {}
        return deep_merge(_DEFAULT_CONFIG, file_config)
    return _DEFAULT_CONFIG.copy()

def get_config() -> Dict[str, Any]:
    return _config_instance.copy()

def set_random_seed(seed: Optional[int] = None):
    import random
    import numpy as np
    import torch
    
    if seed is None:
        seed = _config_instance.get('SEED', 42)
    
    random.seed(seed)
    np.random.seed(seed)
    if torch.cuda.is_available():
        torch.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)

def get_seed() -> int:
    return _config_instance.get('SEED', 42)

def get_paths() -> Dict[str, str]:
    base = Path(__file__).parent.parent
    data_path = base / _config_instance.get('DATA_PATH', 'data/raw')
    output_path = base / _config_instance.get('OUTPUT_PATH', 'data/processed')
    return {
        'data': str(data_path),
        'output': str(output_path),
        'base': str(base)
    }

def ensure_directories():
    paths = get_paths()
    for path in paths.values():
        Path(path).mkdir(parents=True, exist_ok=True)

def main():
    print("Configuration Module")
    print(f"Default Config: {_DEFAULT_CONFIG}")
    print(f"Current Config: {get_config()}")
    print(f"Paths: {get_paths()}")

if __name__ == "__main__":
    main()