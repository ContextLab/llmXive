import hashlib
import os
import yaml
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List

STATE_DIR = Path("state")
STATE_FILE = STATE_DIR / "pipeline_state.yaml"

def compute_sha256(file_path: str) -> str:
    """
    Compute the SHA-256 hash of a file.

    Args:
        file_path: Path to the file to hash.

    Returns:
        Hexadecimal string of the SHA-256 hash.

    Raises:
        FileNotFoundError: If the file does not exist.
        IOError: If the file cannot be read.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    sha256_hash = hashlib.sha256()
    try:
        with open(path, "rb") as f:
            # Read in chunks to handle large files efficiently
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    except IOError as e:
        raise IOError(f"Error reading file {file_path}: {e}")

def load_state() -> Dict[str, Any]:
    """
    Load the current pipeline state from the state file.

    Returns:
        Dictionary containing the pipeline state. Returns an empty dict
        if the state file does not exist.
    """
    if not STATE_FILE.exists():
        return {}

    try:
        with open(STATE_FILE, "r") as f:
            return yaml.safe_load(f) or {}
    except yaml.YAMLError as e:
        raise ValueError(f"Error parsing state file {STATE_FILE}: {e}")

def save_state(state: Dict[str, Any]) -> None:
    """
    Save the pipeline state to the state file.

    Args:
        state: Dictionary containing the pipeline state to save.
    """
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    with open(STATE_FILE, "w") as f:
        yaml.safe_dump(state, f, default_flow_style=False, sort_keys=False)

def update_artifact_state(artifact_name: str, artifact_path: str, state: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Update the state for a specific artifact with its hash and timestamp.

    Args:
        artifact_name: Name of the artifact (e.g., 'evaluation_metrics').
        artifact_path: Path to the artifact file.
        state: Optional existing state dictionary. If None, loads current state.

    Returns:
        Updated state dictionary.
    """
    if state is None:
        state = load_state()

    if "artifacts" not in state:
        state["artifacts"] = {}

    file_path = Path(artifact_path)
    if not file_path.is_absolute():
        file_path = Path.cwd() / file_path

    file_hash = compute_sha256(str(file_path))

    state["artifacts"][artifact_name] = {
        "path": str(file_path),
        "hash": file_hash,
        "updated_at": datetime.utcnow().isoformat()
    }

    save_state(state)
    return state

def update_task_state(task_id: str, status: str, details: Optional[Dict[str, Any]] = None, state: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Update the state for a specific task.

    Args:
        task_id: ID of the task (e.g., 'T034').
        status: Status of the task (e.g., 'completed', 'failed').
        details: Optional dictionary of additional details.
        state: Optional existing state dictionary. If None, loads current state.

    Returns:
        Updated state dictionary.
    """
    if state is None:
        state = load_state()

    if "tasks" not in state:
        state["tasks"] = {}

    task_entry = {
        "status": status,
        "updated_at": datetime.utcnow().isoformat()
    }
    if details:
        task_entry["details"] = details

    state["tasks"][task_id] = task_entry
    save_state(state)
    return state

def hash_multiple_artifacts(artifact_map: Dict[str, str]) -> Dict[str, str]:
    """
    Compute hashes for multiple artifacts at once.

    Args:
        artifact_map: Dictionary mapping artifact names to file paths.

    Returns:
        Dictionary mapping artifact names to their SHA-256 hashes.
    """
    results = {}
    for name, path in artifact_map.items():
        try:
            results[name] = compute_sha256(path)
        except (FileNotFoundError, IOError) as e:
            results[name] = f"ERROR: {str(e)}"
    return results

def get_artifact_hash(artifact_name: str, state: Optional[Dict[str, Any]] = None) -> Optional[str]:
    """
    Retrieve the stored hash for an artifact from the state.

    Args:
        artifact_name: Name of the artifact.
        state: Optional existing state dictionary. If None, loads current state.

    Returns:
        The stored hash string, or None if the artifact is not found in state.
    """
    if state is None:
        state = load_state()

    if "artifacts" in state and artifact_name in state["artifacts"]:
        return state["artifacts"][artifact_name].get("hash")
    return None

def verify_artifact_integrity(artifact_name: str, artifact_path: str, state: Optional[Dict[str, Any]] = None) -> bool:
    """
    Verify that an artifact's current hash matches the stored hash in state.

    Args:
        artifact_name: Name of the artifact.
        artifact_path: Path to the artifact file.
        state: Optional existing state dictionary. If None, loads current state.

    Returns:
        True if the hash matches, False otherwise.
    """
    if state is None:
        state = load_state()

    stored_hash = get_artifact_hash(artifact_name, state)
    if stored_hash is None:
        return False

    try:
        current_hash = compute_sha256(artifact_path)
        return current_hash == stored_hash
    except (FileNotFoundError, IOError):
        return False

def main():
    """
    CLI entry point for update_state utilities.
    Demonstrates usage by hashing the evaluation metrics file if it exists.
    """
    import sys
    import argparse

    parser = argparse.ArgumentParser(description="Manage pipeline state and artifact hashes.")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Command: update-artifact
    parser_artifact = subparsers.add_parser("update-artifact", help="Update state for a specific artifact")
    parser_artifact.add_argument("name", type=str, help="Artifact name (e.g., evaluation_metrics)")
    parser_artifact.add_argument("path", type=str, help="Path to the artifact file")

    # Command: verify
    parser_verify = subparsers.add_parser("verify", help="Verify artifact integrity")
    parser_verify.add_argument("name", type=str, help="Artifact name")
    parser_verify.add_argument("path", type=str, help="Path to the artifact file")

    # Command: update-task
    parser_task = subparsers.add_parser("update-task", help="Update task status")
    parser_task.add_argument("task_id", type=str, help="Task ID (e.g., T034)")
    parser_task.add_argument("status", type=str, help="Status (e.g., completed)")

    args = parser.parse_args()

    if args.command == "update-artifact":
        try:
            state = update_artifact_state(args.name, args.path)
            print(f"Updated state for artifact '{args.name}'")
            print(f"Hash: {state['artifacts'][args.name]['hash']}")
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

    elif args.command == "verify":
        if verify_artifact_integrity(args.name, args.path):
            print(f"Artifact '{args.name}' integrity verified.")
        else:
            print(f"Artifact '{args.name}' integrity check FAILED or not found in state.", file=sys.stderr)
            sys.exit(1)

    elif args.command == "update-task":
        try:
            state = update_task_state(args.task_id, args.status)
            print(f"Updated task '{args.task_id}' status to '{args.status}'")
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)

    else:
        # Default: Check if evaluation_metrics.json exists and hash it if so
        eval_path = Path("results/evaluation_metrics.json")
        if eval_path.exists():
            try:
                state = update_artifact_state("evaluation_metrics", str(eval_path))
                print(f"Automatically updated evaluation_metrics hash: {state['artifacts']['evaluation_metrics']['hash']}")
            except Exception as e:
                print(f"Warning: Could not update evaluation_metrics: {e}", file=sys.stderr)
        else:
            print(f"Note: {eval_path} not found. No automatic update performed.")
            parser.print_help()

if __name__ == "__main__":
    main()