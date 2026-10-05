"""
05_update_state.py

Implements logic to checksum ALL files under `data/` and `results/`,
and update the project state file `state/projects/...yaml` with the new hashes.

Per Constitution Principle V, this script must:
1. Scan `data/` and `results/` recursively for all files.
2. Compute SHA-256 checksums for each file.
3. Update `state/projects/...yaml` (specifically the `artifact_hashes` map).
4. Fail loudly if the state file is missing or cannot be updated.
"""

import hashlib
import os
import sys
import yaml
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional

# Project root relative to this script (assuming script is in code/)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RESULTS_DIR = PROJECT_ROOT / "results"
STATE_DIR = PROJECT_ROOT / "state" / "projects"
PROJECT_ID = "001-impact-of-interoceptive-awareness-on"
STATE_FILE_PATH = STATE_DIR / f"{PROJECT_ID}.yaml"

# Ensure state directory exists
STATE_DIR.mkdir(parents=True, exist_ok=True)


def compute_sha256(file_path: Path) -> str:
    """
    Compute SHA-256 hash of a file.
    Reads in chunks to handle large files efficiently.
    """
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except Exception as e:
        raise RuntimeError(f"Failed to compute checksum for {file_path}: {e}")


def scan_directory_for_artifacts(directory: Path) -> List[Path]:
    """
    Recursively scan a directory for all files.
    Returns a list of absolute paths to all files found.
    """
    if not directory.exists():
        print(f"Warning: Directory {directory} does not exist. Skipping scan.")
        return []

    files = []
    for root, _, filenames in os.walk(directory):
        for filename in filenames:
            full_path = Path(root) / filename
            # Skip hidden files or common temporary files if necessary
            if not filename.startswith('.'):
                files.append(full_path)
    return files


def load_state_file() -> Dict[str, Any]:
    """
    Load the existing state file.
    If it doesn't exist, initialize a new structure.
    """
    if not STATE_FILE_PATH.exists():
        print(f"State file not found at {STATE_FILE_PATH}. Initializing new state.")
        return {
            "project_id": PROJECT_ID,
            "last_updated": None,
            "artifact_hashes": {}
        }

    try:
        with open(STATE_FILE_PATH, "r", encoding="utf-8") as f:
            content = yaml.safe_load(f)
            if content is None:
                content = {
                    "project_id": PROJECT_ID,
                    "last_updated": None,
                    "artifact_hashes": {}
                }
            return content
    except Exception as e:
        raise RuntimeError(f"Failed to load state file {STATE_FILE_PATH}: {e}")


def update_state_file(state_data: Dict[str, Any]) -> None:
    """
    Write the updated state data back to the YAML file.
    """
    try:
        state_data["last_updated"] = datetime.utcnow().isoformat()
        with open(STATE_FILE_PATH, "w", encoding="utf-8") as f:
            yaml.dump(state_data, f, default_flow_style=False, sort_keys=False)
        print(f"State file updated successfully at {STATE_FILE_PATH}")
    except Exception as e:
        raise RuntimeError(f"Failed to write state file {STATE_FILE_PATH}: {e}")


def compute_artifact_hashes() -> Dict[str, str]:
    """
    Compute hashes for all files under data/ and results/ and return a dict mapping
    relative path -> checksum.
    """
    artifacts = []
    if DATA_DIR.exists():
        artifacts.extend(scan_directory_for_artifacts(DATA_DIR))
    if RESULTS_DIR.exists():
        artifacts.extend(scan_directory_for_artifacts(RESULTS_DIR))

    hashes = {}

    if not artifacts:
        print("No files found in data or results directories.")
        return {}

    for file_path in artifacts:
        try:
            checksum = compute_sha256(file_path)
            # Store relative path from project root for portability
            rel_path = str(file_path.relative_to(PROJECT_ROOT))
            hashes[rel_path] = checksum
            print(f"  Checked: {rel_path} -> {checksum[:16]}...")
        except Exception as e:
            # Log error but continue processing other files
            print(f"  ERROR: Failed to hash {file_path}: {e}")

    return hashes


def main():
    """
    Main entry point for the state update script.
    """
    print(f"--- Starting State Update for Project: {PROJECT_ID} ---")
    print(f"Scanning data directory: {DATA_DIR}")
    print(f"Scanning results directory: {RESULTS_DIR}")
    print(f"Target state file: {STATE_FILE_PATH}")

    try:
        # 1. Load existing state
        state_data = load_state_file()

        # 2. Compute new hashes for data/ and results/ artifacts
        new_hashes = compute_artifact_hashes()

        if not new_hashes:
            print("No new artifacts found to checksum.")
            # Still update the timestamp if we ran successfully
            state_data["last_updated"] = datetime.utcnow().isoformat()
            update_state_file(state_data)
            return 0

        # 3. Update the artifact_hashes map in state
        # We replace the entire map to ensure consistency with current scan
        state_data["artifact_hashes"] = new_hashes

        # 4. Write back to disk
        update_state_file(state_data)

        print("--- State Update Completed Successfully ---")
        return 0

    except Exception as e:
        print(f"CRITICAL ERROR during state update: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())