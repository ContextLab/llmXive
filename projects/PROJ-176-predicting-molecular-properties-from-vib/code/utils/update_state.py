import hashlib
import os
import yaml
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List

def compute_sha256(file_path: str) -> str:
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def load_state(state_path: str = "state.yaml") -> Dict[str, Any]:
    path = Path(state_path)
    if path.exists():
        with open(path, "r") as f:
            return yaml.safe_load(f) or {}
    return {}

def save_state(state: Dict[str, Any], state_path: str = "state.yaml"):
    with open(state_path, "w") as f:
        yaml.dump(state, f)

def update_artifact_state(artifact_name: str, path: str, status: str = "completed"):
    state = load_state()
    state[artifact_name] = {
        "path": path,
        "hash": compute_sha256(path),
        "status": status,
        "updated_at": datetime.now().isoformat()
    }
    save_state(state)

def update_task_state(task_id: str, status: str):
    state = load_state()
    if "tasks" not in state:
        state["tasks"] = {}
    state["tasks"][task_id] = {
        "status": status,
        "updated_at": datetime.now().isoformat()
    }
    save_state(state)

def hash_multiple_artifacts(paths: List[str]) -> Dict[str, str]:
    return {p: compute_sha256(p) for p in paths}

def get_artifact_hash(path: str) -> str:
    return compute_sha256(path)

def verify_artifact_integrity(path: str, expected_hash: str) -> bool:
    return compute_sha256(path) == expected_hash

def main():
    # Example usage
    pass
