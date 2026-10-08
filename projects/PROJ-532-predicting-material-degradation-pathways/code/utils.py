"""
Utility functions for the project.
Includes logging setup, checksumming, JSON handling, and environment configuration.
"""
import hashlib
import json
import logging
import os
import random
import sys
from pathlib import Path
from typing import Any, Dict, Optional

def setup_logging(log_level: int = logging.INFO) -> logging.Logger:
    """Configure and return the root logger."""
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)]
    )
    return logging.getLogger(__name__)

def calculate_sha256(file_path: Path) -> str:
    """Calculate SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def save_json(data: Dict[str, Any], file_path: Path) -> None:
    """Save data as a JSON file."""
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)

def load_json(file_path: Path) -> Dict[str, Any]:
    """Load data from a JSON file."""
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)

def get_env_var(var_name: str, default: Optional[str] = None) -> Optional[str]:
    """Get an environment variable."""
    return os.getenv(var_name, default)

def ensure_dir(path: Path) -> None:
    """Ensure a directory exists, creating it if necessary."""
    path.mkdir(parents=True, exist_ok=True)

def set_deterministic_seed(seed: int) -> None:
    """Set random seeds for reproducibility."""
    random.seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)
    # Note: numpy and torch seeds are set in their respective modules

def get_dataset_url() -> str:
    """Retrieve the dataset URL from environment variables."""
    url = os.getenv("ZENODO_DATASET_URL")
    if not url:
        raise ValueError("ZENODO_DATASET_URL environment variable is not set.")
    return url

def configure_seed_from_env() -> int:
    """Configure random seed from environment variable or default."""
    seed_str = os.getenv("RANDOM_SEED", "42")
    try:
        seed = int(seed_str)
    except ValueError:
        logging.warning(f"Invalid RANDOM_SEED '{seed_str}', using default 42")
        seed = 42
    set_deterministic_seed(seed)
    return seed