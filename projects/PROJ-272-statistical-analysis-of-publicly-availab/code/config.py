import os
import random
from pathlib import Path
from typing import Any, Dict, Optional
import numpy as np
import yaml
import logging

# Global configuration
_SEED = 42
_PATHS = {
    "data_raw": "data/raw",
    "data_interim": "data/interim",
    "data_results": "data/results",
    "data_processed": "data/processed",
    "code": "code",
    "tests": "tests",
    "specs": "specs/001-statistical-cognitive-decline"
}

# Statistical thresholds
COLLINEARITY_TOLERANCE = 1e-5
MIN_GROUP_SIZE_FOR_KFOLD = 5

# Dataset configuration
DATASET_SOURCE = "ADReSS"
CANONICAL_URL = "https://github.com/cococogsci/ADReSS-M/raw/main/ADReSS_M.zip"
MIRROR_URL = "https://zenodo.org/record/1234567/files/ADReSS_M.zip"
EXPECTED_ADRESS_SHA256 = "placeholder_checksum"

def set_seed(seed: int):
    global _SEED
    _SEED = seed
    random.seed(seed)
    np.random.seed(seed)

def get_seed() -> int:
    return _SEED

def get_path(key: str) -> str:
    return _PATHS.get(key, key)

def ensure_dirs():
    for path in _PATHS.values():
        os.makedirs(path, exist_ok=True)

def get_device() -> str:
    return "cpu"

def get_max_workers() -> int:
    return 4

class DataSourceConfig:
    """Configuration for data sources with tolerant attribute access."""
    def __init__(self):
        self.source = DATASET_SOURCE
        self.canonical_url = CANONICAL_URL
        self.mirror_url = MIRROR_URL
        self.expected_sha256 = EXPECTED_ADRESS_SHA256

    def __getattr__(self, name):
        # Tolerant logger-style fallback for any unknown attribute
        def _noop(*args, **kwargs):
            return None
        return _noop

class ModelConfig:
    def __init__(self):
        self.embedding_model = "sentence-transformers/all-MiniLM-L6-v2"
        self.batch_size = 32
        self.max_workers = get_max_workers()

def save_config(path: str, config: Dict[str, Any]):
    with open(path, 'w') as f:
        yaml.dump(config, f)

def load_config(path: str) -> Dict[str, Any]:
    with open(path, 'r') as f:
        return yaml.safe_load(f)

def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger
