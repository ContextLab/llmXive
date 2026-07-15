import hashlib
import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional

def ensure_state_dir():
    """Ensure state directory exists."""
    state_dir = Path('state')
    state_dir.mkdir(exist_ok=True)
    return state_dir

def compute_sha256(file_path: str) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def load_artifacts_state(state_path: str = 'state/artifacts.yaml') -> Dict[str, Any]:
    """Load artifacts state from YAML file."""
    if not os.path.exists(state_path):
        return {'artifacts': {}}
    
    with open(state_path, 'r') as f:
        return yaml.safe_load(f)

def save_artifacts_state(state: Dict[str, Any], state_path: str = 'state/artifacts.yaml'):
    """Save artifacts state to YAML file."""
    with open(state_path, 'w') as f:
        yaml.dump(state, f, default_flow_style=False)

def register_artifact(file_path: str, metadata: Dict[str, Any], artifact_hash: str):
    """Register an artifact with its metadata and hash."""
    state = load_artifacts_state()
    state['artifacts'][file_path] = {
        'metadata': metadata,
        'hash': artifact_hash
    }
    save_artifacts_state(state)

def verify_artifact(file_path: str, expected_hash: str) -> bool:
    """Verify an artifact's hash."""
    if not os.path.exists(file_path):
        return False
    
    actual_hash = compute_sha256(file_path)
    return actual_hash == expected_hash

def get_artifact_hash(file_path: str) -> Optional[str]:
    """Get the hash of a registered artifact."""
    state = load_artifacts_state()
    return state.get('artifacts', {}).get(file_path, {}).get('hash')
