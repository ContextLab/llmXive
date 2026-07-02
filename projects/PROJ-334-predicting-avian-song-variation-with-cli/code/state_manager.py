"""
State Manager for Constitution Principle V.
Tracks artifact hashes and timestamps to ensure reproducibility and auditability.
"""
import os
import sys
import hashlib
import yaml
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List

# Import project paths utility
from utils import get_project_paths

STATE_FILE_PATH = "state.yaml"

def compute_file_hash(file_path: Path) -> str:
    """
    Compute SHA-256 hash of a file.
    Reads file in chunks to handle large files efficiently.
    """
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except FileNotFoundError:
        raise FileNotFoundError(f"Cannot compute hash: file not found at {file_path}")
    except Exception as e:
        raise RuntimeError(f"Error computing hash for {file_path}: {str(e)}")

def load_state(state_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Load existing state file or return empty structure if not found.
    """
    if state_path is None:
        state_path = Path(STATE_FILE_PATH)
    
    if state_path.exists():
        with open(state_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {"artifacts": {}, "metadata": {}}
    else:
        return {
            "metadata": {
                "project": "PROJ-334-predicting-avian-song-variation-with-cli",
                "created_at": datetime.utcnow().isoformat(),
                "last_updated": None
            },
            "artifacts": {}
        }

def save_state(state: Dict[str, Any], state_path: Optional[Path] = None) -> None:
    """
    Save state dictionary to YAML file.
    """
    if state_path is None:
        state_path = Path(STATE_FILE_PATH)
    
    state["metadata"]["last_updated"] = datetime.utcnow().isoformat()
    
    with open(state_path, "w", encoding="utf-8") as f:
        yaml.dump(state, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

def register_artifact(
    artifact_path: Path,
    artifact_type: str,
    description: str,
    task_id: str,
    state_path: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Register a new artifact in the state file with its hash and timestamp.
    Returns the registered artifact entry.
    """
    if not artifact_path.exists():
        raise FileNotFoundError(f"Artifact not found at {artifact_path}")
    
    state = load_state(state_path)
    
    file_hash = compute_file_hash(artifact_path)
    file_size = artifact_path.stat().st_size
    timestamp = datetime.utcnow().isoformat()
    
    # Create a unique key for the artifact (relative path from project root)
    try:
        relative_path = artifact_path.resolve().relative_to(Path.cwd().resolve())
    except ValueError:
        relative_path = artifact_path.resolve()
    
    key = str(relative_path)
    
    artifact_entry = {
        "path": str(relative_path),
        "hash": file_hash,
        "size_bytes": file_size,
        "type": artifact_type,
        "description": description,
        "task_id": task_id,
        "created_at": timestamp,
        "last_modified": timestamp
    }
    
    state["artifacts"][key] = artifact_entry
    save_state(state, state_path)
    
    return artifact_entry

def update_artifact(
    artifact_path: Path,
    state_path: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Update an existing artifact's hash and timestamp.
    Raises KeyError if artifact is not registered.
    """
    if not artifact_path.exists():
        raise FileNotFoundError(f"Artifact not found at {artifact_path}")
    
    state = load_state(state_path)
    
    try:
        relative_path = artifact_path.resolve().relative_to(Path.cwd().resolve())
    except ValueError:
        relative_path = artifact_path.resolve()
    
    key = str(relative_path)
    
    if key not in state["artifacts"]:
        raise KeyError(f"Artifact not registered: {key}")
    
    old_hash = state["artifacts"][key]["hash"]
    new_hash = compute_file_hash(artifact_path)
    
    if old_hash != new_hash:
        state["artifacts"][key]["hash"] = new_hash
        state["artifacts"][key]["size_bytes"] = artifact_path.stat().st_size
        state["artifacts"][key]["last_modified"] = datetime.utcnow().isoformat()
        save_state(state, state_path)
    
    return state["artifacts"][key]

def verify_artifact_integrity(
    artifact_path: Path,
    state_path: Optional[Path] = None
) -> bool:
    """
    Verify that an artifact's current hash matches the recorded hash in state.
    Returns True if valid, False otherwise.
    """
    if not artifact_path.exists():
        return False
    
    state = load_state(state_path)
    
    try:
        relative_path = artifact_path.resolve().relative_to(Path.cwd().resolve())
    except ValueError:
        relative_path = artifact_path.resolve()
    
    key = str(relative_path)
    
    if key not in state["artifacts"]:
        return False
    
    recorded_hash = state["artifacts"][key]["hash"]
    current_hash = compute_file_hash(artifact_path)
    
    return recorded_hash == current_hash

def get_artifact_history(
    artifact_path: Path,
    state_path: Optional[Path] = None
) -> Optional[Dict[str, Any]]:
    """
    Retrieve the full history entry for an artifact.
    Returns None if artifact is not registered.
    """
    state = load_state(state_path)
    
    try:
        relative_path = artifact_path.resolve().relative_to(Path.cwd().resolve())
    except ValueError:
        relative_path = artifact_path.resolve()
    
    key = str(relative_path)
    
    return state["artifacts"].get(key)

def list_all_artifacts(
    state_path: Optional[Path] = None,
    task_id: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    List all registered artifacts, optionally filtered by task_id.
    """
    state = load_state(state_path)
    artifacts = list(state["artifacts"].values())
    
    if task_id:
        artifacts = [a for a in artifacts if a.get("task_id") == task_id]
    
    return artifacts

def main():
    """
    CLI entry point for state management operations.
    Usage:
      python code/state_manager.py register <path> <type> <description> <task_id>
      python code/state_manager.py update <path>
      python code/state_manager.py verify <path>
      python code/state_manager.py list [--task-id <id>]
      python code/state_manager.py init
    """
    if len(sys.argv) < 2:
        print("Usage: python code/state_manager.py <command> [args...]")
        print("Commands: register, update, verify, list, init")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "init":
        state = load_state()
        save_state(state)
        print(f"Initialized state file at {STATE_FILE_PATH}")
    
    elif command == "register":
        if len(sys.argv) < 6:
            print("Usage: register <path> <type> <description> <task_id>")
            sys.exit(1)
        path = Path(sys.argv[2])
        artifact_type = sys.argv[3]
        description = sys.argv[4]
        task_id = sys.argv[5]
        
        entry = register_artifact(path, artifact_type, description, task_id)
        print(f"Registered artifact: {entry['path']} (hash: {entry['hash'][:16]}...)")
    
    elif command == "update":
        if len(sys.argv) < 3:
            print("Usage: update <path>")
            sys.exit(1)
        path = Path(sys.argv[2])
        entry = update_artifact(path)
        print(f"Updated artifact: {entry['path']} (hash: {entry['hash'][:16]}...)")
    
    elif command == "verify":
        if len(sys.argv) < 3:
            print("Usage: verify <path>")
            sys.exit(1)
        path = Path(sys.argv[2])
        is_valid = verify_artifact_integrity(path)
        status = "VALID" if is_valid else "INVALID or MISSING"
        print(f"Artifact {path}: {status}")
        sys.exit(0 if is_valid else 1)
    
    elif command == "list":
        task_id = None
        if "--task-id" in sys.argv:
            idx = sys.argv.index("--task-id")
            if idx + 1 < len(sys.argv):
                task_id = sys.argv[idx + 1]
        
        artifacts = list_all_artifacts(task_id=task_id)
        if not artifacts:
            print("No artifacts found.")
        else:
            print(f"Found {len(artifacts)} artifact(s):")
            for a in artifacts:
                print(f"  - {a['path']} [{a['task_id']}] ({a['type']})")
    
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)

if __name__ == "__main__":
    main()
