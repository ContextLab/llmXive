import os
import sys
import json
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional

import yaml

# Add parent directory to path for imports if running as script
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

PROJECT_ID = "PROJ-866-llmxive-follow-up-extending-foundation-p"
STATE_DIR = Path("state")
PROJECT_STATE_FILE = STATE_DIR / "projects" / f"{PROJECT_ID}.yaml"

def compute_file_hash(file_path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    if not file_path.exists():
        return "missing"
    
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        # Read in chunks to handle large files
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def compute_directory_hashes(dir_path: Path, pattern: Optional[str] = None) -> Dict[str, str]:
    """Compute hashes for all files in a directory recursively."""
    hashes = {}
    if not dir_path.exists():
        return hashes
    
    for file_path in dir_path.rglob("*"):
        if file_path.is_file():
            rel_path = file_path.relative_to(dir_path)
            if pattern is None or str(rel_path).endswith(pattern):
                hashes[str(rel_path)] = compute_file_hash(file_path)
    return hashes

def load_state() -> Dict[str, Any]:
    """Load the current project state file."""
    if not PROJECT_STATE_FILE.exists():
        return {
            "project_id": PROJECT_ID,
            "created_at": datetime.now().isoformat(),
            "updated_at": None,
            "artifacts": {}
        }
    
    with open(PROJECT_STATE_FILE, "r") as f:
        return yaml.safe_load(f)

def save_state(state: Dict[str, Any]) -> None:
    """Save the project state to the YAML file."""
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    PROJECT_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    with open(PROJECT_STATE_FILE, "w") as f:
        yaml.dump(state, f, default_flow_style=False, sort_keys=False)

def update_state_with_artifacts() -> Dict[str, Any]:
    """
    Scan data directories, compute hashes, and update the state file.
    Returns the updated state dictionary.
    """
    state = load_state()
    
    # Define artifacts to track
    artifacts = {
        "raw_workflows": compute_directory_hashes(Path("data/raw"), ".json"),
        "processed_logs": compute_directory_hashes(Path("data/processed"), ".json"),
        "results": compute_directory_hashes(Path("data/results"))
    }
    
    state["artifacts"] = artifacts
    state["updated_at"] = datetime.now().isoformat()
    
    save_state(state)
    return state

def main():
    """CLI entry point to update the state file."""
    print(f"Updating state for project: {PROJECT_ID}")
    state = update_state_with_artifacts()
    
    print(f"State updated at: {state['updated_at']}")
    print(f"Artifacts tracked:")
    
    for category, hashes in state["artifacts"].items():
        count = len(hashes)
        print(f"  - {category}: {count} files")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
