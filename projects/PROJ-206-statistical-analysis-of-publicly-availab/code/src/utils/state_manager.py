import hashlib
import os
import yaml
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

from src.utils.config import get_state_root, get_project_root

def compute_file_hash(file_path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        # Read in chunks to handle large files
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def get_state_file_path() -> Path:
    """Get the path to the project state YAML file."""
    project_root = get_project_root()
    project_id = project_root.name.replace(" ", "-")
    state_root = get_state_root()
    state_file = state_root / f"{project_id}.yaml"
    return state_file

def load_state() -> Dict[str, Any]:
    """Load existing state from YAML file or return empty state."""
    state_file = get_state_file_path()
    if state_file.exists():
        with open(state_file, "r") as f:
            return yaml.safe_load(f) or {}
    return {
        "project_id": project_root.name.replace(" ", "-"),
        "artifacts": {},
        "last_updated": None
    }

def update_state_artifact(artifact_name: str, artifact_path: Path, description: Optional[str] = None) -> None:
    """
    Update the state file with a new artifact hash.
    
    Args:
        artifact_name: Name of the artifact (e.g., 'poll_data_cleaned.csv')
        artifact_path: Path to the artifact file
        description: Optional description of the artifact
    """
    if not artifact_path.exists():
        raise FileNotFoundError(f"Cannot hash non-existent file: {artifact_path}")
    
    state = load_state()
    file_hash = compute_file_hash(artifact_path)
    
    if "artifacts" not in state:
        state["artifacts"] = {}
    
    state["artifacts"][artifact_name] = {
        "path": str(artifact_path),
        "hash": file_hash,
        "updated_at": datetime.now().isoformat(),
        "description": description or f"Generated artifact: {artifact_name}"
    }
    
    state["last_updated"] = datetime.now().isoformat()
    
    # Ensure state directory exists
    state_file = get_state_file_path()
    state_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(state_file, "w") as f:
        yaml.dump(state, f, default_flow_style=False, sort_keys=False)

def verify_artifact_integrity(artifact_name: str) -> bool:
    """
    Verify that an artifact's current hash matches the stored hash.
    
    Returns:
        True if verification passes, False otherwise
    """
    state = load_state()
    if "artifacts" not in state or artifact_name not in state["artifacts"]:
        return False
    
    stored_hash = state["artifacts"][artifact_name]["hash"]
    artifact_path = Path(state["artifacts"][artifact_name]["path"])
    
    if not artifact_path.exists():
        return False
    
    current_hash = compute_file_hash(artifact_path)
    return stored_hash == current_hash

def main():
    """CLI entry point for state management utilities."""
    import argparse
    
    parser = argparse.ArgumentParser(description="State management utilities")
    parser.add_argument("command", choices=["hash", "verify", "list"], help="Command to execute")
    parser.add_argument("--artifact", help="Artifact name for hash/verify commands")
    parser.add_argument("--path", help="Path to file for hash command")
    
    args = parser.parse_args()
    
    if args.command == "hash":
        if not args.path:
            parser.error("--path is required for hash command")
        file_path = Path(args.path)
        print(f"Hash: {compute_file_hash(file_path)}")
    
    elif args.command == "verify":
        if not args.artifact:
            parser.error("--artifact is required for verify command")
        is_valid = verify_artifact_integrity(args.artifact)
        print(f"Verification {'passed' if is_valid else 'failed'} for {args.artifact}")
    
    elif args.command == "list":
        state = load_state()
        print("Registered artifacts:")
        for name, info in state.get("artifacts", {}).items():
            print(f"  - {name}: {info['hash'][:16]}... ({info['updated_at']})")

if __name__ == "__main__":
    main()
