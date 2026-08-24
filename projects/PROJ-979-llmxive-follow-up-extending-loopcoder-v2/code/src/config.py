import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional

# Default configuration values
DEFAULT_CONFIG = {
    "NON_INFERIORITY_DELTA": 0.05,
    "ENTROPY_N_SAMPLES": 10,
    "CONVERGENCE_K_RANGE": [1, 2, 3],
    "STRATA_THRESHOLD": 50,
    "MODEL_TEMP": 0.7,
    "MODEL_TOP_P": 0.95,
    "RANDOM_SEED": 42,
    "MODEL_PATH": "codellama/CodeLlama-1.3b-Instruct-hf",
    "DATA_PATH": "data/processed",
    "OUTPUT_PATH": "data/processed"
}

def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """Load configuration from a YAML file or return defaults."""
    if config_path is None:
        # Try to load from default location
        base_dir = Path(__file__).parent.parent
        config_file = base_dir / "config.yaml"
        if config_file.exists():
            with open(config_file, 'r') as f:
                return yaml.safe_load(f)
        return DEFAULT_CONFIG
    
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def get_config_value(key: str, default: Any = None) -> Any:
    """Get a specific configuration value."""
    config = load_config()
    return config.get(key, default)

def ensure_config_file():
    """Ensure a config.yaml file exists in the project root."""
    base_dir = Path(__file__).parent.parent
    config_file = base_dir / "config.yaml"
    if not config_file.exists():
        with open(config_file, 'w') as f:
            yaml.dump(DEFAULT_CONFIG, f)
        return config_file
    return config_file
