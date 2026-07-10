"""
update_state.py

Automatically updates state/projects/...yaml with artifact hashes for:
- data/raw/
- data/processed/
- data/metadata/
- code/

Uses SHA-256 for all file hashing.
"""

import hashlib
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

import yaml

# Configuration
PROJECT_ROOT = Path(__file__).resolve().parent.parent
STATE_DIR = PROJECT_ROOT / "state" / "projects"
TARGET_DIRS = {
    "data_raw": PROJECT_ROOT / "data" / "raw",
    "data_processed": PROJECT_ROOT / "data" / "processed",
    "data_metadata": PROJECT_ROOT / "data" / "metadata",
    "code": PROJECT_ROOT / "code",
}
# File extensions to include in hashing
INCLUDE_EXTENSIONS = {".py", ".csv", ".json", ".yaml", ".yml", ".txt", ".md", ".parquet"}
# Directories to skip
EXCLUDE_DIRS = {".git", "__pycache__", ".venv", "venv", "node_modules", ".pytest_cache"}


def compute_sha256(file_path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    except (OSError, IOError) as e:
        print(f"Warning: Could not read file {file_path}: {e}", file=sys.stderr)
        return ""


def scan_directory(base_dir: Path) -> Dict[str, str]:
    """
    Scan a directory recursively and return a dict of relative paths -> SHA-256 hashes.
    Only includes files with specified extensions.
    """
    if not base_dir.exists():
        return {}

    file_hashes = {}
    for root, dirs, files in os.walk(base_dir):
        # Filter out excluded directories
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]

        for file in files:
            file_path = Path(root) / file
            ext = file_path.suffix.lower()

            if ext in INCLUDE_EXTENSIONS:
                rel_path = file_path.relative_to(base_dir)
                hash_val = compute_sha256(file_path)
                if hash_val:  # Only include if hash was successfully computed
                    file_hashes[str(rel_path)] = hash_val

    return file_hashes


def load_current_state(state_file: Path) -> Dict[str, Any]:
    """Load existing state file or return empty structure."""
    if state_file.exists():
        try:
            with open(state_file, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        except (yaml.YAMLError, OSError) as e:
            print(f"Warning: Could not read state file {state_file}: {e}", file=sys.stderr)
    return {}


def save_state(state_file: Path, state: Dict[str, Any]) -> None:
    """Save state to YAML file."""
    state_file.parent.mkdir(parents=True, exist_ok=True)
    with open(state_file, "w", encoding="utf-8") as f:
        yaml.dump(state, f, default_flow_style=False, sort_keys=False, allow_unicode=True)


def update_project_state(project_id: str) -> None:
    """
    Update the state file for a specific project with current artifact hashes.
    """
    state_file = STATE_DIR / f"{project_id}.yaml"

    current_state = load_current_state(state_file)

    # Update metadata
    current_state["project_id"] = project_id
    current_state["last_updated"] = datetime.utcnow().isoformat() + "Z"

    # Scan and hash each target directory
    dir_hashes = {}
    for dir_key, dir_path in TARGET_DIRS.items():
        if dir_path.exists():
            hashes = scan_directory(dir_path)
            if hashes:  # Only include if there are files
                dir_hashes[dir_key] = {
                    "path": str(dir_path.relative_to(PROJECT_ROOT)),
                    "files": hashes,
                    "file_count": len(hashes),
                }
            else:
                # Directory exists but no matching files found
                dir_hashes[dir_key] = {
                    "path": str(dir_path.relative_to(PROJECT_ROOT)),
                    "exists": True,
                    "files": {},
                    "file_count": 0,
                }
        else:
            dir_hashes[dir_key] = {
                "path": str(dir_path.relative_to(PROJECT_ROOT)),
                "exists": False,
                "files": {},
                "file_count": 0,
            }

    current_state["artifacts"] = dir_hashes

    save_state(state_file, current_state)
    print(f"Updated state for project {project_id} at {state_file}")


def main() -> None:
    """Main entry point."""
    # Ensure state directory exists
    STATE_DIR.mkdir(parents=True, exist_ok=True)

    # If a project ID is provided as argument, update that specific project
    # Otherwise, scan the state directory for existing projects and update all
    if len(sys.argv) > 1:
        project_id = sys.argv[1]
        update_project_state(project_id)
    else:
        # Find existing project state files
        existing_projects = list(STATE_DIR.glob("*.yaml"))
        if existing_projects:
            for state_file in existing_projects:
                project_id = state_file.stem
                update_project_state(project_id)
        else:
            print("No existing project state files found. Provide a project ID as argument.")
            sys.exit(1)


if __name__ == "__main__":
    main()