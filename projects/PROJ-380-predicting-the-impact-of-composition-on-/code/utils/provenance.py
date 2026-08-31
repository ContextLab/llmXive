"""
Provenance tracking module for the BMG Shear Modulus prediction pipeline.
Implements Constitution Principle V: All artifacts must be checksummed and recorded.
"""
import hashlib
import os
import yaml
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List

from utils.config import get_paths

# Constants
PROJECT_ID = "PROJ-380-predicting-the-impact-of-composition-on-"
STATE_DIR_NAME = "state"
PROJECTS_DIR_NAME = "projects"
STATE_FILE_NAME = f"{PROJECT_ID}.yaml"


def ensure_state_directory() -> Path:
    """
    Ensure the state directory structure exists.
    Returns the path to the projects directory.
    """
    root, _, _ = get_paths()
    state_dir = root / STATE_DIR_NAME
    projects_dir = state_dir / PROJECTS_DIR_NAME
    
    projects_dir.mkdir(parents=True, exist_ok=True)
    return projects_dir


def get_provenance_state_file() -> Path:
    """
    Get the path to the canonical state YAML file for this project.
    """
    projects_dir = ensure_state_directory()
    return projects_dir / STATE_FILE_NAME


def compute_file_checksum(file_path: Path) -> str:
    """
    Compute SHA-256 checksum of a file.
    
    Args:
        file_path: Path to the file to checksum.
        
    Returns:
        Hexadecimal string of the SHA-256 hash.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        IOError: If the file cannot be read.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found for checksum: {file_path}")
    
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        # Read in chunks to handle large files
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    
    return sha256_hash.hexdigest()


def load_existing_state() -> Dict[str, Any]:
    """
    Load the existing state file if it exists, otherwise return a new structure.
    
    Returns:
        Dictionary containing the state structure.
    """
    state_file = get_provenance_state_file()
    
    if state_file.exists():
        with open(state_file, "r") as f:
            return yaml.safe_load(f) or {}
    
    # Initialize new state structure
    return {
        "project_id": PROJECT_ID,
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
        "artifacts": {}
    }


def save_state(state: Dict[str, Any]) -> Path:
    """
    Save the state dictionary to the canonical YAML file.
    
    Args:
        state: The state dictionary to save.
        
    Returns:
        Path to the saved file.
    """
    state_file = get_provenance_state_file()
    state["updated_at"] = datetime.utcnow().isoformat()
    
    with open(state_file, "w") as f:
        yaml.dump(state, f, default_flow_style=False, sort_keys=False)
    
    return state_file


def record_artifact(
    artifact_path: Path, 
    description: Optional[str] = None,
    tags: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Compute checksum for an artifact and record it in the state file.
    This is the core implementation of Constitution Principle V.
    
    Args:
        artifact_path: Path to the artifact file.
        description: Optional human-readable description.
        tags: Optional list of tags for categorization.
        
    Returns:
        Dictionary containing the artifact record.
        
    Raises:
        FileNotFoundError: If the artifact does not exist.
    """
    if not artifact_path.exists():
        raise FileNotFoundError(f"Cannot record non-existent artifact: {artifact_path}")
    
    state = load_existing_state()
    
    checksum = compute_file_checksum(artifact_path)
    rel_path = str(artifact_path)
    
    record = {
        "path": rel_path,
        "checksum": checksum,
        "checksum_algorithm": "sha256",
        "recorded_at": datetime.utcnow().isoformat(),
        "description": description or f"Artifact: {rel_path}",
        "tags": tags or []
    }
    
    # Store under artifacts key using path as unique identifier
    state["artifacts"][rel_path] = record
    
    save_state(state)
    return record


def verify_artifact(artifact_path: Path) -> bool:
    """
    Verify that an artifact's current checksum matches the recorded checksum.
    
    Args:
        artifact_path: Path to the artifact to verify.
        
    Returns:
        True if checksum matches, False otherwise.
        
    Raises:
        FileNotFoundError: If the artifact or state file is missing.
    """
    state = load_existing_state()
    rel_path = str(artifact_path)
    
    if rel_path not in state.get("artifacts", {}):
        raise FileNotFoundError(f"No recorded checksum for artifact: {rel_path}")
    
    recorded = state["artifacts"][rel_path]
    current_checksum = compute_file_checksum(artifact_path)
    
    return current_checksum == recorded["checksum"]


def list_artifacts(tags: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    """
    List all recorded artifacts, optionally filtered by tags.
    
    Args:
        tags: Optional list of tags to filter by.
        
    Returns:
        List of artifact records.
    """
    state = load_existing_state()
    artifacts = state.get("artifacts", {}).values()
    
    if tags:
        filtered = []
        for record in artifacts:
            record_tags = record.get("tags", [])
            if any(tag in record_tags for tag in tags):
                filtered.append(record)
        return filtered
    
    return list(artifacts)


def main():
    """
    CLI entry point for provenance operations.
    Usage examples:
      python -m utils.provenance --record data/raw/some_file.csv --desc "Raw data"
      python -m utils.provenance --verify data/raw/some_file.csv
      python -m utils.provenance --list
    """
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="Manage artifact provenance")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--record", type=str, help="Path to artifact to record")
    group.add_argument("--verify", type=str, help="Path to artifact to verify")
    group.add_argument("--list", action="store_true", help="List all recorded artifacts")
    parser.add_argument("--desc", type=str, help="Description for new record")
    parser.add_argument("--tags", type=str, help="Comma-separated tags")

    args = parser.parse_args()

    try:
        if args.record:
            path = Path(args.record)
            tags = [t.strip() for t in args.tags.split(",")] if args.tags else None
            record = record_artifact(path, description=args.desc, tags=tags)
            print(f"Recorded: {record['path']}")
            print(f"Checksum: {record['checksum']}")
        
        elif args.verify:
            path = Path(args.verify)
            is_valid = verify_artifact(path)
            status = "VALID" if is_valid else "INVALID"
            print(f"Verification for {path}: {status}")
            sys.exit(0 if is_valid else 1)
        
        elif args.list:
            artifacts = list_artifacts()
            if not artifacts:
                print("No artifacts recorded.")
            else:
                print(f"Found {len(artifacts)} recorded artifacts:")
                for art in artifacts:
                    print(f"  - {art['path']} ({art['checksum'][:16]}...)")
    
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()