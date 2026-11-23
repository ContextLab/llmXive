import os
from pathlib import Path
from typing import Dict, Any, List

# Project root detection
def _get_project_root() -> Path:
    """
    Attempt to find the project root by looking for 'code' and 'data' directories.
    Falls back to current working directory if not found.
    """
    current = Path.cwd()
    while current != current.parent:
        if (current / "code").exists() and (current / "data").exists():
            return current
        current = current.parent
    return Path.cwd()

PROJECT_ROOT = _get_project_root()

# Default directory structure
DIRS = {
    "code": PROJECT_ROOT / "code",
    "data": PROJECT_ROOT / "data",
    "data_raw": PROJECT_ROOT / "data" / "raw",
    "data_processed": PROJECT_ROOT / "data" / "processed",
    "tests": PROJECT_ROOT / "tests",
    "specs": PROJECT_ROOT / "specs",
    "contracts": PROJECT_ROOT / "contracts",
    "figures": PROJECT_ROOT / "figures",
    "logs": PROJECT_ROOT / "logs",
}

# Default configuration values
DEFAULT_CONFIG = {
    "random_seed": 42,
    "log_level": "INFO",
    "log_file": "pipeline.log",
    "data": {
        "nasa_url": "https://ntrs.nasa.gov/api/citations/19930091406/downloads/19930091406.pdf", # Placeholder, actual URL handled in loader
        "nist_url": "https://nist.gov/materials-data", # Placeholder
        "raw_dir": str(DIRS["data_raw"]),
        "processed_dir": str(DIRS["data_processed"]),
    },
    "models": {
        "baseline": {
            "type": "linear_regression",
            "features": ["log_delta_k"],
            "target": "log_da_dN",
        },
        "augmented": {
            "type": "xgboost", # Default to XGBoost for US2
            "features": ["log_delta_k", "composition", "heat_treatment"],
            "target": "log_da_dN",
            "n_estimators": 100,
            "max_depth": 5,
            "learning_rate": 0.1,
        },
        "tuning": {
            "n_trials": 50,
            "timeout": 3600,
        }
    },
    "validation": {
        "schema_path": str(DIRS["contracts"] / "dataset.schema.yaml"),
        "output_schema_path": str(DIRS["contracts"] / "output.schema.yaml"),
    }
}

def ensure_dirs() -> None:
    """
    Create all required directories if they do not exist.
    """
    for dir_path in DIRS.values():
        dir_path.mkdir(parents=True, exist_ok=True)

def get_config_dict() -> Dict[str, Any]:
    """
    Returns the full configuration dictionary.
    """
    return DEFAULT_CONFIG

def get_path(key: str) -> Path:
    """
    Retrieves a specific directory path by key from DIRS.
    """
    if key not in DIRS:
        raise KeyError(f"Directory key '{key}' not found in config.")
    return DIRS[key]
