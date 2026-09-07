"""
State Manager for llmXive Project PROJ-846.

This module handles the generation and maintenance of project state files,
specifically computing content hashes for all relevant files in the project
tree to ensure reproducibility and integrity tracking.

Artifacts produced:
  - state/projects/PROJ-846-llmxive-follow-up-extending-guava-an-eff.yaml
"""
import hashlib
import os
import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

# Project specific constants
PROJECT_ROOT = Path(__file__).parent.parent.parent
PROJECT_ID = "PROJ-846-llmxive-follow-up-extending-guava-an-eff"
STATE_DIR = PROJECT_ROOT / "state" / "projects"
STATE_FILE = STATE_DIR / f"{PROJECT_ID}.yaml"

# Directories to include in state hashing
# We exclude __pycache__, .git, and the state directory itself to avoid
# circular dependencies and noise from generated files
HASHABLE_DIRS = [
    PROJECT_ROOT / "code",
    PROJECT_ROOT / "data",
    PROJECT_ROOT / "tests",
    PROJECT_ROOT / "specs",
]
EXCLUDE_PATTERNS = {"__pycache__", ".git", ".pyc", ".swp", "state"}

def calculate_file_hash(file_path: Path) -> str:
    """
    Calculate SHA-256 hash of a file's contents.

    Args:
        file_path: Path to the file to hash.

    Returns:
        Hexadecimal string of the SHA-256 hash.
    """
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            # Read in chunks to handle large files
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    except (IOError, OSError) as e:
        raise RuntimeError(f"Failed to read file {file_path}: {e}")

def get_all_files(base_dirs: List[Path], exclude_patterns: set) -> List[Path]:
    """
    Recursively collect all files in the given directories, excluding patterns.

    Args:
        base_dirs: List of root directories to scan.
        exclude_patterns: Set of directory/file name patterns to exclude.

    Returns:
        Sorted list of Path objects for all found files.
    """
    all_files = []
    for base_dir in base_dirs:
        if not base_dir.exists():
            continue
        for root, dirs, files in os.walk(base_dir):
            # Filter out excluded directories in-place to prevent descent
            dirs[:] = [d for d in dirs if d not in exclude_patterns]
            
            for file in files:
                if file in exclude_patterns or file.endswith(tuple(exclude_patterns)):
                    continue
                file_path = Path(root) / file
                # Ensure the file is actually under one of our base dirs
                # (os.walk might behave unexpectedly with symlinks, though unlikely here)
                if file_path.is_file():
                    all_files.append(file_path)
    
    # Sort for deterministic ordering
    return sorted(all_files)

def generate_state_hash(file_hashes: Dict[str, str]) -> str:
    """
    Generate a single aggregate hash for the entire project state.

    Args:
        file_hashes: Dictionary mapping relative paths to their individual hashes.

    Returns:
        Hexadecimal string of the SHA-256 hash of the sorted concatenated hashes.
    """
    # Sort keys to ensure deterministic output
    sorted_items = sorted(file_hashes.items())
    content = "\n".join(f"{k}:{v}" for k, v in sorted_items)
    return hashlib.sha256(content.encode("utf-8")).hexdigest()

def update_state_file() -> Dict[str, Any]:
    """
    Scan the project directories, compute hashes, and write/update the state YAML.

    This function:
    1. Scans `code/`, `data/`, `tests/`, and `specs/`.
    2. Computes SHA-256 hashes for every file found.
    3. Calculates an aggregate project hash.
    4. Writes the results to `state/projects/PROJ-846-llmxive-follow-up-extending-guava-an-eff.yaml`.

    Returns:
        Dictionary containing the generated state summary.
    """
    # Ensure state directory exists
    STATE_DIR.mkdir(parents=True, exist_ok=True)

    # Collect files
    files = get_all_files(HASHABLE_DIRS, EXCLUDE_PATTERNS)
    
    if not files:
        raise RuntimeError("No files found to hash in the specified directories.")

    file_hashes = {}
    for file_path in files:
        try:
            # Store path relative to project root
            rel_path = str(file_path.relative_to(PROJECT_ROOT))
            file_hashes[rel_path] = calculate_file_hash(file_path)
        except ValueError:
            # Skip files not under project root (shouldn't happen with logic above)
            continue

    aggregate_hash = generate_state_hash(file_hashes)

    state_data = {
        "project_id": PROJECT_ID,
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "aggregate_hash": aggregate_hash,
        "file_count": len(file_hashes),
        "files": file_hashes,
        "metadata": {
            "directories_scanned": [str(d.relative_to(PROJECT_ROOT)) for d in HASHABLE_DIRS if d.exists()],
            "excluded_patterns": list(EXCLUDE_PATTERNS),
        }
    }

    with open(STATE_FILE, "w", encoding="utf-8") as f:
        yaml.dump(state_data, f, default_flow_style=False, sort_keys=False, allow_unicode=True)

    return state_data

def verify_state_integrity() -> bool:
    """
    Verify that the current file hashes match the stored state file.

    Returns:
        True if the current state matches the stored state, False otherwise.
    """
    if not STATE_FILE.exists():
        print(f"State file not found: {STATE_FILE}. Run update_state_file() first.")
        return False

    with open(STATE_FILE, "r", encoding="utf-8") as f:
        stored_state = yaml.safe_load(f)

    current_files = get_all_files(HASHABLE_DIRS, EXCLUDE_PATTERNS)
    current_hashes = {}
    for file_path in current_files:
        try:
            rel_path = str(file_path.relative_to(PROJECT_ROOT))
            current_hashes[rel_path] = calculate_file_hash(file_path)
        except ValueError:
            continue

    # Compare counts first
    if len(current_hashes) != stored_state.get("file_count", -1):
        print(f"File count mismatch: {len(current_hashes)} vs {stored_state.get('file_count')}")
        return False

    # Compare hashes
    stored_files = stored_state.get("files", {})
    for path, hash_val in current_hashes.items():
        if path not in stored_files:
            print(f"New file detected: {path}")
            return False
        if stored_files[path] != hash_val:
            print(f"Hash mismatch for: {path}")
            return False

    # Check for deleted files
    if set(current_hashes.keys()) != set(stored_files.keys()):
        print("File set mismatch: files were deleted or added.")
        return False

    return True

def main():
    """CLI entry point for state management."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Manage project state hashes.")
    parser.add_argument("action", choices=["update", "verify"], help="Action to perform")
    args = parser.parse_args()

    if args.action == "update":
        print(f"Updating state file for project {PROJECT_ID}...")
        try:
            state = update_state_file()
            print(f"Success! State file written to: {STATE_FILE}")
            print(f"Aggregate Hash: {state['aggregate_hash']}")
            print(f"Files tracked: {state['file_count']}")
        except Exception as e:
            print(f"Error updating state: {e}")
            raise
    elif args.action == "verify":
        print(f"Verifying state integrity for project {PROJECT_ID}...")
        if verify_state_integrity():
            print("State integrity verified. No changes detected.")
        else:
            print("State integrity check FAILED. Files have changed or state file is missing.")
            raise SystemExit(1)

if __name__ == "__main__":
    main()