import hashlib
import os
from pathlib import Path
from typing import Dict, Any, Optional
import yaml

def compute_file_sha256(file_path: str) -> str:
    """
    Compute the SHA-256 checksum of a file.

    Args:
        file_path: Path to the file.

    Returns:
        Hexadecimal string of the SHA-256 hash.
    """
    sha256_hash = hashlib.sha256()
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    with open(path, "rb") as f:
        # Read in chunks to handle large files
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)

    return sha256_hash.hexdigest()

def load_state_file(state_path: str) -> Dict[str, Any]:
    """
    Load the state YAML file, creating it with default structure if it doesn't exist.

    Args:
        state_path: Path to the state YAML file.

    Returns:
        Dictionary containing the state data.
    """
    path = Path(state_path)
    if not path.exists():
        # Create default structure for the specific project state file
        default_state = {
            "project_id": "PROJ-573-https-arxiv-org-abs-2604-27351",
            "updated_at": "",
            "artifact_hashes": {}
        }
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            yaml.dump(default_state, f, default_flow_style=False)
        return default_state

    with open(path, "r") as f:
        return yaml.safe_load(f) or {}

def save_state_file(state_path: str, data: Dict[str, Any]) -> None:
    """
    Save the state dictionary to the YAML file.

    Args:
        state_path: Path to the state YAML file.
        data: Dictionary to save.
    """
    path = Path(state_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        yaml.dump(data, f, default_flow_style=False, sort_keys=False)

def update_artifact_hash(
    state_path: str,
    artifact_path: str,
    hash_value: Optional[str] = None
) -> str:
    """
    Update the artifact hash in the state file.

    If hash_value is not provided, it is computed from the file at artifact_path.

    Args:
        state_path: Path to the state YAML file.
        artifact_path: Path to the artifact file.
        hash_value: Optional pre-computed hash.

    Returns:
        The hash value that was stored.
    """
    state = load_state_file(state_path)
    if "artifact_hashes" not in state:
        state["artifact_hashes"] = {}

    if hash_value is None:
        hash_value = compute_file_sha256(artifact_path)

    state["artifact_hashes"][artifact_path] = {
        "sha256": hash_value
    }

    save_state_file(state_path, state)
    return hash_value

def main():
    """
    CLI entry point for checksum utilities.
    """
    import sys
    import argparse

    parser = argparse.ArgumentParser(description="Checksum utilities for artifact tracking")
    parser.add_argument("--state", required=True, help="Path to state YAML file")
    parser.add_argument("--file", required=True, help="Path to file to hash")
    parser.add_argument("--update", action="store_true", help="Update state file with hash")

    args = parser.parse_args()

    hash_val = compute_file_sha256(args.file)
    print(f"SHA256: {hash_val}")

    if args.update:
        update_artifact_hash(args.state, args.file, hash_val)
        print(f"Updated state file: {args.state}")

if __name__ == "__main__":
    main()
