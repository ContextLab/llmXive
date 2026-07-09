import hashlib
import json
import logging
import os
import random
import sys
from pathlib import Path
from typing import Any, Dict, Optional

def setup_logging(level: int = logging.INFO) -> logging.Logger:
    """Configure and return the root logger."""
    if logging.getLogger().handlers:
        return logging.getLogger()
    
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger()

def calculate_sha256(file_path: Path) -> str:
    """Calculate SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def save_json(data: Any, path: Path) -> None:
    """Save data to a JSON file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)

def load_json(path: Path) -> Dict[str, Any]:
    """Load data from a JSON file."""
    with open(path, 'r') as f:
        return json.load(f)

def get_env_var(key: str, default: Optional[str] = None) -> Optional[str]:
    """Get an environment variable, with optional default."""
    return os.environ.get(key, default)

def ensure_dir(dir_path: Path) -> Path:
    """Ensure a directory exists, creating it if necessary."""
    dir_path.mkdir(parents=True, exist_ok=True)
    return dir_path

def set_deterministic_seed(seed: int) -> None:
    """Set random seed for reproducibility."""
    random.seed(seed)
    # If numpy is available, set its seed too
    try:
        import numpy as np
        np.random.seed(seed)
    except ImportError:
        pass

def get_dataset_url(key: str) -> Optional[str]:
    """Get dataset URL from environment variable."""
    return get_env_var(key)