import os
import random
from pathlib import Path
from typing import Any, Dict
import numpy as np
import yaml

# Base project directory
PROJECT_ROOT = Path(__file__).parent.parent

class DataSourceConfig:
    DATASET_SOURCE = "ADReSS"
    ALLOWED_SOURCES = ["ADReSS"]
    # Explicitly exclude DementiaBank per T000a
    EXCLUDED_SOURCES = ["DementiaBank"]

class ModelConfig:
    CPU_ONLY = True
    MAX_WORKERS = 1
    BATCH_SIZE = 32
    EMBEDDING_MODEL = "all-MiniLM-L6-v2"

def set_seed(seed: int = 42) -> None:
    """Set random seeds for reproducibility."""
    random.seed(seed)
    np.random.seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)

def get_seed() -> int:
    return 42

def get_device() -> str:
    return "cpu"

def get_max_workers() -> int:
    return 1

def get_path(relative_path: str) -> str:
    """Get absolute path relative to project root."""
    return str(PROJECT_ROOT / relative_path)

def ensure_dirs(file_path: str) -> None:
    """Ensure the directory for the given file path exists."""
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)

def save_config(config: Dict[str, Any], path: str) -> None:
    ensure_dirs(path)
    with open(path, 'w') as f:
        yaml.dump(config, f)

def load_config(path: str) -> Dict[str, Any]:
    if os.path.exists(path):
        with open(path, 'r') as f:
            return yaml.safe_load(f)
    return {}
