"""
Configuration management for the neural correlates pipeline.
"""
import os
import json
from pathlib import Path
from typing import Any, Dict, Optional
import sys
from pathlib import Path as PathLib

# Default configuration
DEFAULT_CONFIG = {
    'SEED': 42,
    'DATA_PATH': 'data/raw',
    'OUTPUT_PATH': 'data/processed',
    'BENCHMARK_ACCURACY': None,  # Deferred per Constitution Principle VII
    'LOWCUT': 1.0,
    'HIGHCUT': 40.0,
    'NOTCH_FREQ': 50.0,
    'EPOCH_TMIN': -1.0,
    'EPOCH_TMAX': 1.0,
    'FREQUENCY_RANGE': (8.0, 30.0),
    'N_PERMUTATIONS': 1000,
    'MIN_EPOCHS_PER_CONDITION': 50,
    'TARGET_ELECTRODES': ['P3', 'Pz', 'P4', 'F3', 'Fz', 'F4']
}

def get_default_config() -> Dict[str, Any]:
    """Return the default configuration dictionary."""
    return DEFAULT_CONFIG.copy()

def get_env_config() -> Dict[str, Any]:
    """Get configuration from environment variables if set."""
    config = get_default_config()
    env_map = {
        'SEED': 'SEED',
        'DATA_PATH': 'DATA_PATH',
        'OUTPUT_PATH': 'OUTPUT_PATH',
        'BENCHMARK_ACCURACY': 'BENCHMARK_ACCURACY',
        'LOWCUT': 'LOWCUT',
        'HIGHCUT': 'HIGHCUT',
        'NOTCH_FREQ': 'NOTCH_FREQ',
        'EPOCH_TMIN': 'EPOCH_TMIN',
        'EPOCH_TMAX': 'EPOCH_TMAX',
        'N_PERMUTATIONS': 'N_PERMUTATIONS',
        'MIN_EPOCHS_PER_CONDITION': 'MIN_EPOCHS_PER_CONDITION',
    }

    for key, env_var in env_map.items():
        if env_var in os.environ:
            value = os.environ[env_var]
            # Try to convert to appropriate type
            try:
                if '.' in value:
                    config[key] = float(value)
                else:
                    config[key] = int(value)
            except ValueError:
                config[key] = value

    return config

def deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """Deep merge two dictionaries."""
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge(result[key], value)
        else:
            result[key] = value
    return result

def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """Load configuration from a JSON file if provided, otherwise use defaults."""
    config = get_default_config()
    if config_path and os.path.exists(config_path):
        with open(config_path, 'r') as f:
            file_config = json.load(f)
        config = deep_merge(config, file_config)
    return config

# Global configuration instance
_config = None

def get_config() -> Dict[str, Any]:
    """Get the global configuration."""
    global _config
    if _config is None:
        _config = deep_merge(get_default_config(), get_env_config())
    return _config

def set_random_seed(seed: Optional[int] = None) -> None:
    """Set random seed for reproducibility."""
    import random
    import numpy as np

    if seed is None:
        seed = get_config().get('SEED', 42)

    random.seed(seed)
    np.random.seed(seed)

    # Set seed for PyTorch if available
    try:
        import torch
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
    except ImportError:
        pass

def get_seed() -> int:
    """Get the current random seed."""
    return get_config().get('SEED', 42)

def get_paths() -> Dict[str, Path]:
    """Get path objects from configuration."""
    config = get_config()
    return {
        'DATA_PATH': Path(config['DATA_PATH']),
        'OUTPUT_PATH': Path(config['OUTPUT_PATH']),
        'RAW_PATH': Path(config['DATA_PATH']) / 'raw',
        'PROCESSED_PATH': Path(config['OUTPUT_PATH']),
    }

def ensure_directories() -> None:
    """Ensure all required directories exist."""
    paths = get_paths()
    for path in paths.values():
        path.mkdir(parents=True, exist_ok=True)

def main() -> None:
    """Main entry point for configuration testing."""
    config = get_config()
    print("Configuration loaded:")
    for key, value in config.items():
        print(f"  {key}: {value}")

    paths = get_paths()
    print("\nPaths:")
    for key, value in paths.items():
        print(f"  {key}: {value}")

    ensure_directories()
    print("\nDirectories ensured.")

if __name__ == "__main__":
    main()