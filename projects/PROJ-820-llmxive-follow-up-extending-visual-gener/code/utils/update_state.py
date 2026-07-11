"""
update_state.py

Calculates SHA-256 hashes of artifacts in the project's data directories
and updates the corresponding state YAML files under state/projects/.

Usage:
    python code/utils/update_state.py
"""
import os
import sys
import hashlib
import json
from pathlib import Path
from typing import Dict, List, Any, Optional

import yaml

# Project root is assumed to be the parent of 'code'
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
STATE_DIR = PROJECT_ROOT / "state"
PROJECT_STATE_DIR = STATE_DIR / "projects"

# Directories to scan for artifacts (relative to DATA_DIR)
ARTIFACT_DIRS = [
    "raw",
    "derived/physics_constraints",
    "derived/prompts",
    "derived/generated_images",
    "derived/evaluation_results",
    "processed",
]

# Mapping of directory names to state file names (without extension)
STATE_FILE_MAP = {
    "raw": "raw_state",
    "derived/physics_constraints": "physics_constraints_state",
    "derived/prompts": "prompts_state",
    "derived/generated_images": "generated_images_state",
    "derived/evaluation_results": "evaluation_results_state",
    "processed": "processed_state",
}

def calculate_sha256(file_path: Path) -> str:
    """Calculate SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except Exception as e:
        print(f"Error reading {file_path}: {e}", file=sys.stderr)
        return ""

def scan_directory(dir_path: Path) -> Dict[str, Any]:
    """
    Scan a directory recursively for files and compute their hashes.
    Returns a dict with 'files' (list of {path, hash, size}) and 'total_files'.
    """
    if not dir_path.exists():
        return {"files": [], "total_files": 0, "status": "missing"}

    files_info = []
    total_files = 0

    for root, _, files in os.walk(dir_path):
        for file_name in files:
            file_path = Path(root) / file_name
            # Skip hidden files or non-data files if necessary
            if file_name.startswith('.'):
                continue

            file_size = file_path.stat().st_size
            file_hash = calculate_sha256(file_path)

            # Store relative path from data directory
            rel_path = file_path.relative_to(DATA_DIR)

            files_info.append({
                "path": str(rel_path),
                "hash": file_hash,
                "size": file_size
            })
            total_files += 1

    return {
        "files": files_info,
        "total_files": total_files,
        "status": "ok" if total_files > 0 else "empty",
        "directory": str(dir_path.relative_to(PROJECT_ROOT))
    }

def update_state_file(state_key: str, scan_result: Dict[str, Any]) -> None:
    """
    Update or create the state YAML file for a given directory.
    State files are stored in state/projects/
    """
    state_file_name = f"{state_key}.yaml"
    state_file_path = PROJECT_STATE_DIR / state_file_name

    # Ensure state directory exists
    PROJECT_STATE_DIR.mkdir(parents=True, exist_ok=True)

    # Load existing state if it exists
    existing_state = {}
    if state_file_path.exists():
        try:
            with open(state_file_path, "r", encoding="utf-8") as f:
                existing_state = yaml.safe_load(f) or {}
        except yaml.YAMLError as e:
            print(f"Warning: Could not parse existing state file {state_file_path}: {e}", file=sys.stderr)

    # Update with new scan result
    existing_state["last_updated"] = scan_result.get("directory", "unknown") # Placeholder for timestamp logic if needed
    existing_state["scan_result"] = scan_result
    existing_state["status"] = "updated"

    # Write back to file
    try:
        with open(state_file_path, "w", encoding="utf-8") as f:
            yaml.dump(existing_state, f, default_flow_style=False, sort_keys=False)
        print(f"Updated state file: {state_file_path}")
    except Exception as e:
        print(f"Error writing state file {state_file_path}: {e}", file=sys.stderr)

def main() -> int:
    """Main entry point."""
    print(f"Project Root: {PROJECT_ROOT}")
    print(f"Data Directory: {DATA_DIR}")
    print(f"State Directory: {PROJECT_STATE_DIR}")

    if not DATA_DIR.exists():
        print(f"Error: Data directory {DATA_DIR} does not exist.", file=sys.stderr)
        return 1

    if not PROJECT_STATE_DIR.exists():
        PROJECT_STATE_DIR.mkdir(parents=True, exist_ok=True)
        print(f"Created state directory: {PROJECT_STATE_DIR}")

    success = True

    for dir_name in ARTIFACT_DIRS:
        dir_path = DATA_DIR / dir_name
        state_key = STATE_FILE_MAP.get(dir_name, f"{dir_name}_state")

        print(f"\nScanning: {dir_path}")
        scan_result = scan_directory(dir_path)

        if scan_result["status"] == "missing":
            print(f"  -> Directory does not exist. Creating empty state.")
            # Create empty state for missing dirs
            scan_result = {
                "files": [],
                "total_files": 0,
                "status": "missing",
                "directory": str(dir_path.relative_to(PROJECT_ROOT))
            }

        update_state_file(state_key, scan_result)

        if scan_result["status"] == "missing" and dir_path.exists() is False:
            # This is expected for initial runs, but we log it
            pass

    print("\nState update complete.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
