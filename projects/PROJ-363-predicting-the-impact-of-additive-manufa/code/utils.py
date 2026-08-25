import hashlib
import json
import logging
import os
import random
from pathlib import Path
from typing import Any, Dict, Optional, Union

import yaml

def setup_logging(log_level: int = logging.INFO) -> logging.Logger:
    """Configure and return a logger."""
    logger = logging.getLogger(__name__)
    logger.setLevel(log_level)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger

def set_seed(seed: int) -> None:
    """Set random seeds for reproducibility."""
    random.seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)
    try:
        import numpy as np
        np.random.seed(seed)
    except ImportError:
        pass
    try:
        import torch
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
    except ImportError:
        pass

def compute_file_hash(file_path: Union[str, Path]) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def compute_string_hash(data: str) -> str:
    """Compute SHA-256 hash of a string."""
    return hashlib.sha256(data.encode("utf-8")).hexdigest()

def load_state(state_path: Union[str, Path] = "state.yaml") -> Dict[str, Any]:
    """Load state from YAML file."""
    state_path = Path(state_path)
    if not state_path.exists():
        return {"artifacts": {}, "version": 1}
    with open(state_path, "r") as f:
        content = yaml.safe_load(f)
        return content if content else {"artifacts": {}, "version": 1}

def update_state(
    artifact_name: str,
    artifact_path: Union[str, Path],
    state_path: Union[str, Path] = "state.yaml",
) -> None:
    """Update state file with new artifact hash."""
    state = load_state(state_path)
    if "artifacts" not in state:
        state["artifacts"] = {}
    state["artifacts"][artifact_name] = {
        "path": str(artifact_path),
        "hash": compute_file_hash(artifact_path),
    }
    with open(state_path, "w") as f:
        yaml.dump(state, f, default_flow_style=False)

def get_state_hash(state: Dict[str, Any]) -> str:
    """Compute hash of the current state dictionary."""
    return compute_string_hash(json.dumps(state, sort_keys=True))

def validate_hash(state: Dict[str, Any]) -> bool:
    """Validate integrity of stored artifact hashes."""
    for name, info in state.get("artifacts", {}).items():
        path = info.get("path")
        stored_hash = info.get("hash")
        if path and stored_hash:
            if not Path(path).exists():
                return False
            current_hash = compute_file_hash(path)
            if current_hash != stored_hash:
                return False
    return True

def load_config(config_path: Union[str, Path] = "config.yaml") -> Dict[str, Any]:
    """Load configuration from YAML file."""
    config_path = Path(config_path)
    if not config_path.exists():
        return {}
    with open(config_path, "r") as f:
        content = yaml.safe_load(f)
        return content if content else {}

def get_config_value(config: Dict[str, Any], key: str, default: Any = None) -> Any:
    """Get a value from config dictionary with optional default."""
    keys = key.split(".")
    value = config
    for k in keys:
        if isinstance(value, dict) and k in value:
            value = value[k]
        else:
            return default
    return value