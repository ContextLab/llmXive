import os
import json
from pathlib import Path
from typing import Dict, Any, Optional

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
SCHEMA_FILE = "contracts/twin_prime_schema.schema.yaml"
STATE_FILE = "state.yaml"

def get_config() -> Dict[str, Any]:
    """
    Returns the base configuration dictionary.
    Currently static, but extensible for future config file loading.
    """
    return {
        "project_root": str(PROJECT_ROOT),
        "data_root": str(DATA_DIR),
        "raw_dir": str(DATA_DIR / "raw"),
        "results_dir": str(DATA_DIR / "results"),
        "figures_dir": str(DATA_DIR / "figures"),
        "schema_path": str(PROJECT_ROOT / SCHEMA_FILE),
        "state_path": str(PROJECT_ROOT / STATE_FILE),
        "max_prime": 1_000_000_000,
    }

def ensure_directories(config: Optional[Dict[str, Any]] = None) -> Path:
    """
    Creates the required directory structure if it does not exist:
    - data/raw/
    - data/results/
    - data/figures/
    
    Returns the path to the base data directory.
    """
    if config is None:
        config = get_config()
        
    dirs = [
        config["raw_dir"],
        config["results_dir"],
        config["figures_dir"]
    ]
    
    for dir_path in dirs:
        p = Path(dir_path)
        p.mkdir(parents=True, exist_ok=True)
        
    return Path(config["data_root"])

def get_schema_path() -> str:
    """
    Returns the absolute path to the schema definition file.
    """
    return str(PROJECT_ROOT / SCHEMA_FILE)

def get_state_path() -> str:
    """
    Returns the absolute path to the project state YAML file.
    """
    return str(PROJECT_ROOT / STATE_FILE)
