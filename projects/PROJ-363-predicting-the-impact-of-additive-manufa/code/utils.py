import hashlib
import json
import logging
import os
import random
from pathlib import Path
from typing import Any, Dict, Optional

import yaml


def setup_logging(level: int = logging.INFO) -> logging.Logger:
    """Configure and return a logger."""
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )
    return logging.getLogger(__name__)


def set_seed(seed: int = 42) -> None:
    """Set random seeds for reproducibility."""
    random.seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)
    # Note: numpy and torch seeds set in respective modules if needed


def compute_file_hash(file_path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def compute_string_hash(content: str) -> str:
    """Compute SHA-256 hash of a string."""
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def load_state(state_path: Path) -> Dict[str, Any]:
    """Load state.yaml file."""
    if not state_path.exists():
        return {}
    with open(state_path, "r") as f:
        return yaml.safe_load(f) or {}


def update_state(state_path: Path, artifact_name: str, artifact_hash: str) -> None:
    """Update state.yaml with a new artifact hash."""
    state = load_state(state_path)
    state[artifact_name] = {
        "hash": artifact_hash,
        "updated_at": str(Path.now()) if hasattr(Path, "now") else "2023-01-01",
    }
    with open(state_path, "w") as f:
        yaml.dump(state, f)


def get_state_hash(state: Dict[str, Any]) -> str:
    """Compute hash of the current state dictionary."""
    return compute_string_hash(json.dumps(state, sort_keys=True))


def validate_hash(file_path: Path, expected_hash: str) -> bool:
    """Validate file hash against expected value."""
    if not file_path.exists():
        return False
    actual_hash = compute_file_hash(file_path)
    return actual_hash == expected_hash
