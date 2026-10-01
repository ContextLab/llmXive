import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional

# Default configuration values as Python variables
NON_INFERIORITY_DELTA = 0.05
ENTROPY_N_SAMPLES = 10
CONVERGENCE_K_RANGE = [1, 2, 3]
STRATA_THRESHOLD = 50
MODEL_TEMP = 0.7
MODEL_TOP_P = 0.95
RANDOM_SEED = 42
MODEL_PARAMS = 1300000000  # Approx 1.3B for CodeLlama-1.3b-Instruct

# Paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
CODE_DIR = PROJECT_ROOT / "code"

def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load configuration from a YAML file or return defaults.
    """
    defaults = {
        "NON_INFERIORITY_DELTA": NON_INFERIORITY_DELTA,
        "ENTROPY_N_SAMPLES": ENTROPY_N_SAMPLES,
        "CONVERGENCE_K_RANGE": CONVERGENCE_K_RANGE,
        "STRATA_THRESHOLD": STRATA_THRESHOLD,
        "MODEL_TEMP": MODEL_TEMP,
        "MODEL_TOP_P": MODEL_TOP_P,
        "RANDOM_SEED": RANDOM_SEED,
        "MODEL_PARAMS": MODEL_PARAMS,
        "DATA_DIR": str(DATA_DIR),
        "RAW_DATA_DIR": str(RAW_DATA_DIR),
        "PROCESSED_DATA_DIR": str(PROCESSED_DATA_DIR),
        "CODE_DIR": str(CODE_DIR),
    }

    if config_path:
        path = Path(config_path)
        if path.exists():
            with open(path, 'r') as f:
                file_config = yaml.safe_load(f)
                if file_config:
                    defaults.update(file_config)
    
    return defaults

def get_config_value(key: str, default: Any = None) -> Any:
    """Get a specific config value."""
    config = load_config()
    return config.get(key, default)

def ensure_config_file(config_path: Optional[str] = None) -> None:
    """Ensure a config file exists, creating it with defaults if not."""
    if config_path is None:
        config_path = PROJECT_ROOT / "config.yaml"
    
    path = Path(config_path)
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        defaults = load_config()
        with open(path, 'w') as f:
            yaml.dump(defaults, f)