"""
Checksum verification logic for data integrity.

Implements SHA-256 verification and writes checksums to the state file
as required by Constitution Principle III.
"""
import hashlib
import os
from pathlib import Path
from typing import Dict, Optional
import yaml

def compute_sha256(file_path: str) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def verify_checksum(file_path: str, expected_checksum: str) -> bool:
    """Verify file checksum against expected value."""
    actual = compute_sha256(file_path)
    return actual == expected_checksum

def update_state_checksums(
    project_id: str,
    file_paths: Dict[str, str],
    state_dir: str = "state"
) -> None:
    """
    Update the project state file with checksums for given files.

    Args:
        project_id: The project identifier (e.g., 'PROJ-772-...')
        file_paths: Dict mapping logical name to absolute file path
        state_dir: Base directory for state files
    """
    state_file = Path(state_dir) / "projects" / f"{project_id}.yaml"
    state_file.parent.mkdir(parents=True, exist_ok=True)

    state_data = {"project_id": project_id, "checksums": {}}

    # Load existing if present
    if state_file.exists():
        with open(state_file, "r") as f:
            state_data = yaml.safe_load(f) or state_data

    for name, path in file_paths.items():
        if os.path.exists(path):
            state_data["checksums"][name] = compute_sha256(path)
        else:
            state_data["checksums"][name] = "MISSING"

    with open(state_file, "w") as f:
        yaml.dump(state_data, f, default_flow_style=False)
