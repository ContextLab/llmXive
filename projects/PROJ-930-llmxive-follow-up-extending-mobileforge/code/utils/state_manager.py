import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

STATE_DIR_NAME = "state"
CHECKSUM_FILE = "checksums.json"
METADATA_FILE = "metadata.json"

def get_state_dir(project_root: Optional[Path] = None) -> Path:
    """Get the path to the state directory relative to the project root."""
    if project_root is None:
        project_root = Path.cwd()
    return project_root / STATE_DIR_NAME

def initialize_state_structure(project_root: Optional[Path] = None) -> Path:
    """
    Initialize the state directory structure for artifact checksums and versioning.
    Creates the directory if it does not exist.
    Returns the path to the state directory.
    """
    if project_root is None:
        project_root = Path.cwd()
    
    state_dir = get_state_dir(project_root)
    state_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize checksums file if it doesn't exist
    checksums_path = state_dir / CHECKSUM_FILE
    if not checksums_path.exists():
        with open(checksums_path, 'w') as f:
            json.dump({}, f, indent=2)
    
    # Initialize metadata file if it doesn't exist
    metadata_path = state_dir / METADATA_FILE
    if not metadata_path.exists():
        metadata = {
            "version": "1.0.0",
            "created_at": None,
            "last_updated": None,
            "artifacts": []
        }
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)
    
    return state_dir

def compute_sha256(file_path: Path) -> str:
    """
    Compute the SHA-256 checksum of a file.
    
    Args:
        file_path: Path to the file to hash.
        
    Returns:
        Hexadecimal string of the SHA-256 hash.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        IOError: If the file cannot be read.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    
    return sha256_hash.hexdigest()

def register_artifact(
    artifact_path: Path,
    task_id: str,
    description: str = "",
    project_root: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Register an artifact by computing its checksum and updating the state files.
    
    Args:
        artifact_path: Path to the artifact file.
        task_id: ID of the task that produced this artifact.
        description: Optional description of the artifact.
        project_root: Project root directory.
        
    Returns:
        Dictionary containing artifact registration info.
        
    Raises:
        FileNotFoundError: If the artifact file does not exist.
    """
    if project_root is None:
        project_root = Path.cwd()
    
    state_dir = initialize_state_structure(project_root)
    checksums_path = state_dir / CHECKSUM_FILE
    metadata_path = state_dir / METADATA_FILE
    
    # Compute checksum
    checksum = compute_sha256(artifact_path)
    
    # Load existing checksums
    with open(checksums_path, 'r') as f:
        checksums = json.load(f)
    
    # Update checksums
    artifact_key = str(artifact_path.relative_to(project_root))
    checksums[artifact_key] = {
        "checksum": checksum,
        "task_id": task_id,
        "registered_at": str(Path.cwd())  # Simplified timestamp
    }
    
    with open(checksums_path, 'w') as f:
        json.dump(checksums, f, indent=2)
    
    # Load and update metadata
    with open(metadata_path, 'r') as f:
        metadata = json.load(f)
    
    artifact_entry = {
        "path": artifact_key,
        "checksum": checksum,
        "task_id": task_id,
        "description": description
    }
    
    metadata["artifacts"].append(artifact_entry)
    metadata["last_updated"] = str(Path.cwd())  # Simplified timestamp
    
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    return {
        "path": artifact_key,
        "checksum": checksum,
        "task_id": task_id,
        "description": description
    }

def verify_artifact(
    artifact_path: Path,
    project_root: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Verify an artifact's checksum against the registered value.
    
    Args:
        artifact_path: Path to the artifact file.
        project_root: Project root directory.
        
    Returns:
        Dictionary with verification result.
    """
    if project_root is None:
        project_root = Path.cwd()
    
    state_dir = get_state_dir(project_root)
    checksums_path = state_dir / CHECKSUM_FILE
    
    if not checksums_path.exists():
        return {
            "verified": False,
            "reason": "No checksums file found"
        }
    
    with open(checksums_path, 'r') as f:
        checksums = json.load(f)
    
    artifact_key = str(artifact_path.relative_to(project_root))
    
    if artifact_key not in checksums:
        return {
            "verified": False,
            "reason": "Artifact not registered in state"
        }
    
    registered_checksum = checksums[artifact_key]["checksum"]
    current_checksum = compute_sha256(artifact_path)
    
    return {
        "verified": registered_checksum == current_checksum,
        "registered_checksum": registered_checksum,
        "current_checksum": current_checksum,
        "task_id": checksums[artifact_key]["task_id"]
    }

def list_artifacts_by_task(
    task_id: str,
    project_root: Optional[Path] = None
) -> List[Dict[str, Any]]:
    """
    List all artifacts registered for a specific task.
    
    Args:
        task_id: The task ID to filter by.
        project_root: Project root directory.
        
    Returns:
        List of artifact dictionaries.
    """
    if project_root is None:
        project_root = Path.cwd()
    
    state_dir = get_state_dir(project_root)
    metadata_path = state_dir / METADATA_FILE
    
    if not metadata_path.exists():
        return []
    
    with open(metadata_path, 'r') as f:
        metadata = json.load(f)
    
    return [
        artifact for artifact in metadata.get("artifacts", [])
        if artifact.get("task_id") == task_id
    ]

def get_state_summary(project_root: Optional[Path] = None) -> Dict[str, Any]:
    """
    Get a summary of the state directory contents.
    
    Args:
        project_root: Project root directory.
        
    Returns:
        Dictionary with state summary information.
    """
    if project_root is None:
        project_root = Path.cwd()
    
    state_dir = get_state_dir(project_root)
    checksums_path = state_dir / CHECKSUM_FILE
    metadata_path = state_dir / METADATA_FILE
    
    summary = {
        "state_dir_exists": state_dir.exists(),
        "checksums_file_exists": checksums_path.exists(),
        "metadata_file_exists": metadata_path.exists(),
        "artifact_count": 0,
        "task_count": 0
    }
    
    if checksums_path.exists():
        with open(checksums_path, 'r') as f:
            checksums = json.load(f)
        summary["artifact_count"] = len(checksums)
    
    if metadata_path.exists():
        with open(metadata_path, 'r') as f:
            metadata = json.load(f)
        summary["metadata_version"] = metadata.get("version", "unknown")
        summary["last_updated"] = metadata.get("last_updated", "never")
        tasks = set(a.get("task_id") for a in metadata.get("artifacts", []))
        summary["task_count"] = len(tasks)
    
    return summary

def main():
    """CLI entry point for state manager operations."""
    import argparse
    
    parser = argparse.ArgumentParser(description="State Manager CLI")
    parser.add_argument(
        "--init",
        action="store_true",
        help="Initialize state directory structure"
    )
    parser.add_argument(
        "--register",
        type=str,
        metavar="FILE",
        help="Register an artifact file"
    )
    parser.add_argument(
        "--task-id",
        type=str,
        help="Task ID for registration"
    )
    parser.add_argument(
        "--verify",
        type=str,
        metavar="FILE",
        help="Verify an artifact file"
    )
    parser.add_argument(
        "--list",
        type=str,
        metavar="TASK_ID",
        help="List artifacts for a task"
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Show state summary"
    )
    
    args = parser.parse_args()
    
    if args.init:
        state_dir = initialize_state_structure()
        print(f"State directory initialized at: {state_dir}")
    
    elif args.register:
        if not args.task_id:
            print("Error: --task-id is required for registration")
            sys.exit(1)
        artifact_path = Path(args.register)
        if not artifact_path.exists():
            print(f"Error: File not found: {artifact_path}")
            sys.exit(1)
        result = register_artifact(artifact_path, args.task_id)
        print(f"Registered: {result['path']} (checksum: {result['checksum'][:16]}...)")
    
    elif args.verify:
        artifact_path = Path(args.verify)
        if not artifact_path.exists():
            print(f"Error: File not found: {artifact_path}")
            sys.exit(1)
        result = verify_artifact(artifact_path)
        if result["verified"]:
            print(f"Verified: {artifact_path} (checksum matches)")
        else:
            print(f"Verification failed: {result.get('reason', 'unknown')}")
            sys.exit(1)
    
    elif args.list:
        artifacts = list_artifacts_by_task(args.list)
        if not artifacts:
            print(f"No artifacts found for task: {args.list}")
        else:
            print(f"Artifacts for task {args.list}:")
            for a in artifacts:
                print(f"  - {a['path']} ({a['checksum'][:16]}...)")
    
    elif args.summary:
        summary = get_state_summary()
        print(json.dumps(summary, indent=2))
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
