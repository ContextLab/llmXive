"""
T004: State manager for SHA-256 hashes.
"""
import hashlib
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

STATE_PATH = Path(__file__).parent.parent.parent / "state" / "artifacts.yaml"

class StateError(Exception):
    pass

def compute_sha256(file_path: Path) -> str:
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def load_state() -> Dict[str, Any]:
    if not STATE_PATH.exists():
        return {"artifacts": {}}
    # Simple YAML-like parser or use pyyaml if available
    # For robustness, we assume pyyaml is installed (T001b)
    try:
        import yaml
        with open(STATE_PATH) as f:
            return yaml.safe_load(f)
    except ImportError:
        # Fallback manual parsing if needed, but assuming yaml exists
        return {"artifacts": {}}

def save_state(state: Dict[str, Any]):
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    import yaml
    with open(STATE_PATH, "w") as f:
        yaml.safe_dump(state, f)

def update_artifact_state(file_path: Path):
    state = load_state()
    if "artifacts" not in state:
        state["artifacts"] = {}
    
    rel_path = str(file_path.relative_to(Path(__file__).parent.parent.parent))
    checksum = compute_sha256(file_path)
    
    state["artifacts"][rel_path] = {
        "sha256": checksum,
        "updated_at": datetime.now().isoformat()
    }
    save_state(state)
    print(f"Updated state for {rel_path}")

def update_state_for_multiple_artifacts(files: List[Path]):
    for f in files:
        update_artifact_state(f)

def verify_artifact(file_path: Path) -> bool:
    state = load_state()
    rel_path = str(file_path.relative_to(Path(__file__).parent.parent.parent))
    if rel_path not in state.get("artifacts", {}):
        return False
    stored_hash = state["artifacts"][rel_path]["sha256"]
    current_hash = compute_sha256(file_path)
    return stored_hash == current_hash

def main():
    if len(sys.argv) < 3:
        print("Usage: python -m code.utils.state_manager <update|verify> <file_path>")
        sys.exit(1)
    
    action = sys.argv[1]
    file_path = Path(sys.argv[2])
    
    if action == "update":
        update_artifact_state(file_path)
    elif action == "verify":
        if verify_artifact(file_path):
            print("Verified")
        else:
            print("Failed")
            sys.exit(1)
    else:
        print("Unknown action")
        sys.exit(1)

if __name__ == "__main__":
    main()