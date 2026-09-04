import os
import yaml
from pathlib import Path
from typing import Any, Dict, Optional
import sys
from pathlib import Path as PathLib

CONFIG = {
    'SEED': 42,
    'DATA_PATH': 'data/raw',
    'OUTPUT_PATH': 'data/processed',
    'BENCHMARK_ACCURACY': 'targetThreshold',
    'OPENNEURO_DATASET': 'ds0001171'
}

def get_default_config():
    """Return the default configuration dictionary."""
    return CONFIG.copy()

def get_env_config():
    """Load config from environment variables if present."""
    cfg = get_default_config()
    if 'SEED' in os.environ:
        cfg['SEED'] = int(os.environ['SEED'])
    if 'DATA_PATH' in os.environ:
        cfg['DATA_PATH'] = os.environ['DATA_PATH']
    if 'OUTPUT_PATH' in os.environ:
        cfg['OUTPUT_PATH'] = os.environ['OUTPUT_PATH']
    return cfg

def deep_merge(base: Dict, override: Dict) -> Dict:
    """Deep merge two dictionaries."""
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result

def load_config(path: Optional[str] = None) -> Dict:
    """Load configuration from a YAML file if provided."""
    if path and os.path.exists(path):
        with open(path, 'r') as f:
            file_cfg = yaml.safe_load(f)
            return deep_merge(get_default_config(), file_cfg)
    return get_default_config()

def get_config() -> Dict:
    """Get the active configuration."""
    return load_config()

def set_random_seed(seed: Optional[int] = None):
    """Set random seed for reproducibility."""
    import random
    import numpy as np
    seed = seed or get_config().get('SEED', 42)
    random.seed(seed)
    np.random.seed(seed)
    if 'tensorflow' in sys.modules:
        import tensorflow as tf
        tf.random.set_seed(seed)
    return seed

def get_seed() -> int:
    """Get the current random seed."""
    return get_config().get('SEED', 42)

def get_paths() -> Dict[str, Path]:
    """Get resolved Path objects for data directories."""
    cfg = get_config()
    return {
        'raw': Path(cfg['DATA_PATH']),
        'processed': Path(cfg['OUTPUT_PATH']),
        'figures': Path(cfg['OUTPUT_PATH']) / 'figures',
        'logs': Path('logs')
    }

def ensure_directories():
    """Ensure all required directories exist."""
    paths = get_paths()
    for path in paths.values():
        path.mkdir(parents=True, exist_ok=True)

def main():
    """CLI entry point for config operations."""
    import argparse
    parser = argparse.ArgumentParser(description="Configuration Manager")
    parser.add_argument('--show', action='store_true', help="Show current config")
    parser.add_argument('--validate', action='store_true', help="Validate config")
    args = parser.parse_args()

    cfg = get_config()
    if args.show:
        print(yaml.dump(cfg, default_flow_style=False))
    if args.validate:
        required = ['SEED', 'DATA_PATH', 'OUTPUT_PATH']
        missing = [k for k in required if k not in cfg]
        if missing:
            print(f"Validation failed: Missing keys {missing}")
            sys.exit(1)
        print("Configuration valid.")

if __name__ == "__main__":
    main()