"""
Artifact Hashing Script for llmXive Project.

Computes SHA-256 hashes for all existing files in the `data/` directory
and updates the project state YAML file to ensure traceability and
integrity (Constitution Principle V).
"""

import os
import hashlib
import yaml
from pathlib import Path
from typing import Dict, Any, List

# Import project configuration for paths
from config import Paths


def compute_sha256(file_path: Path) -> str:
    """
    Computes the SHA-256 hash of a file.

    Args:
        file_path: Path to the file.

    Returns:
        Hexadecimal string of the SHA-256 hash.
    """
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except (IOError, OSError) as e:
        raise RuntimeError(f"Failed to read file {file_path} for hashing: {e}")


def scan_data_directory(data_root: Path) -> List[Dict[str, Any]]:
    """
    Recursively scans the data directory for all files and computes their hashes.

    Args:
        data_root: The root path of the data directory.

    Returns:
        List of dictionaries containing relative path, absolute path, and hash.
    """
    artifacts = []
    if not data_root.exists():
        print(f"Warning: Data directory {data_root} does not exist. Skipping scan.")
        return artifacts

    for root, _, files in os.walk(data_root):
        for file in files:
            abs_path = Path(root) / file
            rel_path = abs_path.relative_to(data_root)
            
            # Skip hidden files or temporary lock files if any
            if file.startswith('.'):
                continue

            file_hash = compute_sha256(abs_path)
            artifacts.append({
                "path": str(rel_path),
                "absolute_path": str(abs_path),
                "sha256": file_hash
            })

    return artifacts


def update_state_yaml(state_path: Path, artifacts: List[Dict[str, Any]]) -> None:
    """
    Updates the state YAML file with the new artifact hashes.

    Args:
        state_path: Path to the state YAML file.
        artifacts: List of artifact dictionaries.
    """
    state_data = {"artifacts": artifacts}
    
    # Ensure parent directory exists
    state_path.parent.mkdir(parents=True, exist_ok=True)

    with open(state_path, "w", encoding="utf-8") as f:
        yaml.dump(state_data, f, default_flow_style=False, sort_keys=False)
    
    print(f"State updated successfully at {state_path} with {len(artifacts)} artifacts.")


def main():
    """
    Main entry point for the hash_artifacts script.
    """
    paths = Paths()
    data_dir = paths.data_root
    state_file = paths.project_root / "state.yaml"

    print(f"Scanning data directory: {data_dir}")
    artifacts = scan_data_directory(data_dir)

    if not artifacts:
        print("No files found to hash in the data directory.")
        # Even if empty, we update the state to reflect the current empty scan
        update_state_yaml(state_file, [])
        return

    print(f"Found {len(artifacts)} files. Computing hashes...")
    update_state_yaml(state_file, artifacts)
    print("Hashing and state update complete.")


if __name__ == "__main__":
    main()