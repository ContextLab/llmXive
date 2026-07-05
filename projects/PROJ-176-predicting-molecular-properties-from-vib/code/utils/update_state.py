"""
State management utility for llmXive research pipeline.

Implements Principle V: Deterministic State Management.
Computes SHA-256 hashes for artifacts and updates state YAML files
to track pipeline progress and data integrity.
"""

import hashlib
import os
import yaml
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List


def compute_sha256(file_path: str) -> str:
    """
    Compute SHA-256 hash of a file.

    Args:
        file_path: Path to the file to hash.

    Returns:
        Hexadecimal string of the SHA-256 hash.

    Raises:
        FileNotFoundError: If the file does not exist.
        IOError: If the file cannot be read.
    """
    sha256_hash = hashlib.sha256()
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)

    return sha256_hash.hexdigest()


def load_state(state_path: str) -> Dict[str, Any]:
    """
    Load existing state file or create a new one if it doesn't exist.

    Args:
        state_path: Path to the state YAML file.

    Returns:
        Dictionary containing the state data.
    """
    path = Path(state_path)

    if path.exists():
        with open(path, "r") as f:
            return yaml.safe_load(f) or {}

    # Initialize new state structure
    return {
        "pipeline_version": "1.0.0",
        "last_updated": None,
        "artifacts": {},
        "tasks": {},
        "metadata": {}
    }


def save_state(state: Dict[str, Any], state_path: str) -> None:
    """
    Save state dictionary to a YAML file.

    Args:
        state: Dictionary containing state data.
        state_path: Path to the state YAML file.
    """
    path = Path(state_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    state["last_updated"] = datetime.utcnow().isoformat()

    with open(path, "w") as f:
        yaml.safe_dump(state, f, default_flow_style=False, sort_keys=False)


def update_artifact_state(
    artifact_path: str,
    state_path: str,
    artifact_name: Optional[str] = None,
    task_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Update the state file with information about a generated artifact.

    Args:
        artifact_path: Path to the artifact file.
        state_path: Path to the state YAML file.
        artifact_name: Optional custom name for the artifact.
        task_id: Optional task ID that generated this artifact.
        metadata: Optional additional metadata to store.

    Returns:
        Updated state dictionary.
    """
    state = load_state(state_path)
    artifact_name = artifact_name or Path(artifact_path).name

    if "artifacts" not in state:
        state["artifacts"] = {}

    state["artifacts"][artifact_name] = {
        "path": str(Path(artifact_path).resolve()),
        "hash": compute_sha256(artifact_path),
        "size_bytes": Path(artifact_path).stat().st_size,
        "task_id": task_id,
        "created_at": datetime.utcnow().isoformat(),
        "metadata": metadata or {}
    }

    save_state(state, state_path)
    return state


def update_task_state(
    task_id: str,
    status: str,
    state_path: str,
    details: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Update the state file with task execution status.

    Args:
        task_id: Unique identifier for the task.
        status: Task status (e.g., 'completed', 'failed', 'running').
        state_path: Path to the state YAML file.
        details: Optional additional details about the task execution.

    Returns:
        Updated state dictionary.
    """
    state = load_state(state_path)

    if "tasks" not in state:
        state["tasks"] = {}

    state["tasks"][task_id] = {
        "status": status,
        "updated_at": datetime.utcnow().isoformat(),
        "details": details or {}
    }

    save_state(state, state_path)
    return state


def hash_multiple_artifacts(
    artifact_paths: List[str],
    state_path: str,
    task_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Compute hashes for multiple artifacts and update state.

    Args:
        artifact_paths: List of paths to artifact files.
        state_path: Path to the state YAML file.
        task_id: Optional task ID associated with these artifacts.

    Returns:
        Updated state dictionary.
    """
    state = load_state(state_path)

    if "artifacts" not in state:
        state["artifacts"] = {}

    for artifact_path in artifact_paths:
        path = Path(artifact_path)
        if not path.exists():
            continue

        artifact_name = path.name
        state["artifacts"][artifact_name] = {
            "path": str(path.resolve()),
            "hash": compute_sha256(artifact_path),
            "size_bytes": path.stat().st_size,
            "task_id": task_id,
            "created_at": datetime.utcnow().isoformat()
        }

    save_state(state, state_path)
    return state


def get_artifact_hash(artifact_path: str) -> str:
    """
    Get the SHA-256 hash of an artifact without updating state.

    Args:
        artifact_path: Path to the artifact file.

    Returns:
        Hexadecimal string of the SHA-256 hash.
    """
    return compute_sha256(artifact_path)


def verify_artifact_integrity(artifact_path: str, expected_hash: str) -> bool:
    """
    Verify that an artifact's hash matches an expected value.

    Args:
        artifact_path: Path to the artifact file.
        expected_hash: Expected SHA-256 hash.

    Returns:
        True if hashes match, False otherwise.
    """
    actual_hash = compute_sha256(artifact_path)
    return actual_hash == expected_hash


def main():
    """
    CLI entry point for testing state management utilities.
    """
    import argparse

    parser = argparse.ArgumentParser(
        description="State management utility for llmXive pipeline"
    )
    parser.add_argument(
        "--action",
        choices=["hash", "update-artifact", "update-task", "verify"],
        required=True,
        help="Action to perform"
    )
    parser.add_argument(
        "--path",
        required=True,
        help="Path to the file or state file"
    )
    parser.add_argument(
        "--state-path",
        default="state/pipeline_state.yaml",
        help="Path to the state YAML file"
    )
    parser.add_argument(
        "--task-id",
        help="Task ID for task state updates"
    )
    parser.add_argument(
        "--status",
        choices=["completed", "failed", "running"],
        help="Task status for task state updates"
    )
    parser.add_argument(
        "--expected-hash",
        help="Expected hash for verification"
    )

    args = parser.parse_args()

    if args.action == "hash":
        try:
            hash_value = compute_sha256(args.path)
            print(f"SHA-256: {hash_value}")
        except Exception as e:
            print(f"Error: {e}")
            return 1

    elif args.action == "update-artifact":
        try:
            state = update_artifact_state(
                args.path,
                args.state_path,
                task_id=args.task_id
            )
            print(f"State updated. Artifact hash: {state['artifacts'][Path(args.path).name]['hash']}")
        except Exception as e:
            print(f"Error: {e}")
            return 1

    elif args.action == "update-task":
        if not args.task_id or not args.status:
            print("Error: --task-id and --status required for task updates")
            return 1
        try:
            state = update_task_state(args.task_id, args.status, args.state_path)
            print(f"Task {args.task_id} status updated to {args.status}")
        except Exception as e:
            print(f"Error: {e}")
            return 1

    elif args.action == "verify":
        if not args.expected_hash:
            print("Error: --expected-hash required for verification")
            return 1
        try:
            is_valid = verify_artifact_integrity(args.path, args.expected_hash)
            print(f"Integrity check: {'PASSED' if is_valid else 'FAILED'}")
            return 0 if is_valid else 1
        except Exception as e:
            print(f"Error: {e}")
            return 1

    return 0


if __name__ == "__main__":
    exit(main())
