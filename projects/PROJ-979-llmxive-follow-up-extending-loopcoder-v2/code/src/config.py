"""
Configuration management for the project.
"""
import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional

# Default configuration values as per T000-config
DEFAULT_CONFIG = {
    "NON_INFERIORITY_DELTA": 0.05,
    "ENTROPY_N_SAMPLES": 10,
    "CONVERGENCE_K_RANGE": [1, 2, 3],
    "STRATA_THRESHOLD": 50,
    "MODEL_TEMP": 0.7,
    "MODEL_TOP_P": 0.95,
    "RANDOM_SEED": 42,
    "MODEL_NAME": "codellama/CodeLlama-1.3b-Instruct-hf",
    "DATA_DIR": "data",
    "OUTPUT_DIR": "data/processed"
}

CONFIG_PATH = Path("code/src/config.yaml")

def load_config() -> Dict[str, Any]:
    """Load configuration from YAML file or return defaults."""
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, 'r') as f:
            return yaml.safe_load(f)
    return DEFAULT_CONFIG

def get_config_value(key: str, default: Any = None) -> Any:
    """Get a specific configuration value."""
    config = load_config()
    return config.get(key, default if default is not None else DEFAULT_CONFIG.get(key))

def ensure_config_file():
    """Ensure the config file exists with defaults."""
    if not CONFIG_PATH.exists():
        CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_PATH, 'w') as f:
            yaml.dump(DEFAULT_CONFIG, f)

def main():
    ensure_config_file()
    config = load_config()
    print(f"Loaded config: {config}")

if __name__ == "__main__":
    main()
