"""
State Manager for llmXive Project.

This module handles the management of project state by:
1. Calculating content hashes for all tracked artifacts.
2. Generating a state hash for the entire project.
3. Updating a central YAML state file atomically.
4. Verifying state integrity.

The state file is located at: state/PROJ-846-llmxive-follow-up-extending-guava-an-eff.yaml
"""

import hashlib
import os
import tempfile
import yaml
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional


# Project root relative to this file's location
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
STATE_DIR = PROJECT_ROOT / "state"
PROJECT_ID = "PROJ-846-llmxive-follow-up-extending-guava-an-eff"
STATE_FILE_NAME = f"{PROJECT_ID}.yaml"
STATE_FILE_PATH = STATE_DIR / STATE_FILE_NAME

# Directories to track for state hashing
TRACKED_DIRS = [
    "code",
    "data",
    "tests",
    "specs",
    "docs"
]

# File extensions to include in hashing
TRACKED_EXTENSIONS = {".py", ".yaml", ".yml", ".json", ".txt", ".md", ".toml", ".cfg", ".ini", ".gitignore", ".ruff.toml", ".gitkeep"}

# Directories to exclude from hashing
EXCLUDED_DIRS = {".git", "__pycache__", ".pytest_cache", ".ruff_cache", "venv", ".venv", "node_modules", "build", "dist"}


def calculate_file_hash(file_path: Path) -> str:
    """
    Calculate the SHA-256 hash of a file's contents.

    Args:
        file_path: Path to the file to hash.

    Returns:
        Hexadecimal string of the SHA-256 hash.
    """
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    except (IOError, OSError) as e:
        raise RuntimeError(f"Failed to read file {file_path} for hashing: {e}")


def get_all_files(base_dir: Path, tracked_dirs: List[str], extensions: set, excluded_dirs: set) -> List[Path]:
    """
    Recursively find all tracked files in the specified directories.

    Args:
        base_dir: Root directory to start scanning from.
        tracked_dirs: List of directory names to include.
        extensions: Set of file extensions to include.
        excluded_dirs: Set of directory names to exclude.

    Returns:
        List of Path objects for all matching files.
    """
    files = []
    base_dir = base_dir.resolve()

    for dir_name in tracked_dirs:
        target_dir = base_dir / dir_name
        if not target_dir.exists():
            continue

        for root, dirs, filenames in os.walk(target_dir):
            # Modify dirs in-place to skip excluded directories
            dirs[:] = [d for d in dirs if d not in excluded_dirs]

            for filename in filenames:
                file_path = Path(root) / filename
                if file_path.suffix in extensions:
                    files.append(file_path)

    return files


def generate_state_hash(file_hashes: Dict[str, str]) -> str:
    """
    Generate a single hash representing the state of all files.

    Args:
        file_hashes: Dictionary mapping relative paths to their content hashes.

    Returns:
        Hexadecimal string of the combined state hash.
    """
    combined = "".join(f"{k}:{v}" for k, v in sorted(file_hashes.items()))
    return hashlib.sha256(combined.encode("utf-8")).hexdigest()


def update_state_file(artifact_hashes: Optional[Dict[str, str]] = None, state_file_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Update the central state YAML file with current file hashes and timestamp.

    Uses atomic write (write to temp, rename) to ensure consistency.

    Args:
        artifact_hashes: Optional pre-computed map of relative paths to hashes.
        state_file_path: Optional override for the state file location.

    Returns:
        The updated state dictionary.
    """
    if state_file_path is None:
        state_file_path = STATE_FILE_PATH

    # Ensure state directory exists
    state_file_path.parent.mkdir(parents=True, exist_ok=True)

    # If no hashes provided, calculate them
    if artifact_hashes is None:
        files = get_all_files(PROJECT_ROOT, TRACKED_DIRS, TRACKED_EXTENSIONS, EXCLUDED_DIRS)
        artifact_hashes = {}
        for f in files:
            try:
                rel_path = f.relative_to(PROJECT_ROOT)
                artifact_hashes[str(rel_path)] = calculate_file_hash(f)
            except ValueError:
                # File is not relative to PROJECT_ROOT (shouldn't happen given logic)
                continue

    # Construct the state data
    state_data = {
        "project_id": PROJECT_ID,
        "updated_at": datetime.utcnow().isoformat() + "Z",
        "artifact_hashes": artifact_hashes,
        "state_hash": generate_state_hash(artifact_hashes),
        "tracked_directories": TRACKED_DIRS,
        "excluded_directories": list(EXCLUDED_DIRS)
    }

    # Atomic write: Write to a temp file in the same directory, then rename
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            dir=state_file_path.parent,
            prefix=f".{state_file_path.name}.tmp_",
            suffix=".yaml",
            delete=False
        ) as tmp_file:
            yaml.dump(state_data, tmp_file, default_flow_style=False, sort_keys=False)
            tmp_path = Path(tmp_file.name)

        # Atomic rename
        os.replace(tmp_path, state_file_path)

    except Exception as e:
        # Clean up temp file if rename fails
        if 'tmp_path' in locals() and tmp_path.exists():
            tmp_path.unlink()
        raise RuntimeError(f"Failed to update state file atomically: {e}")

    return state_data


def verify_state_integrity(state_file_path: Optional[Path] = None) -> bool:
    """
    Verify the integrity of the state file by recalculating hashes and comparing.

    Args:
        state_file_path: Optional override for the state file location.

    Returns:
        True if the state is consistent, False otherwise.
    """
    if state_file_path is None:
        state_file_path = STATE_FILE_PATH

    if not state_file_path.exists():
        return False

    try:
        with open(state_file_path, "r") as f:
            current_state = yaml.safe_load(f)

        stored_hashes = current_state.get("artifact_hashes", {})
        stored_state_hash = current_state.get("state_hash")

        # Recalculate hashes for the files listed in the state
        recalc_hashes = {}
        for rel_path_str, stored_hash in stored_hashes.items():
            file_path = PROJECT_ROOT / rel_path_str
            if file_path.exists():
                try:
                    recalc_hashes[rel_path_str] = calculate_file_hash(file_path)
                except RuntimeError:
                    # File exists but cannot be read
                    return False
            else:
                # File missing but recorded in state
                return False

        # Check if all current tracked files are in the state (optional strictness)
        # For now, we just verify the stored files haven't changed.

        recalc_state_hash = generate_state_hash(recalc_hashes)

        return recalc_state_hash == stored_state_hash

    except (yaml.YAMLError, KeyError, TypeError) as e:
        return False


def get_state_summary(state_file_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Get a summary of the current project state.

    Args:
        state_file_path: Optional override for the state file location.

    Returns:
        Dictionary with summary information.
    """
    if state_file_path is None:
        state_file_path = STATE_FILE_PATH

    if not state_file_path.exists():
        return {"exists": False}

    try:
        with open(state_file_path, "r") as f:
            state = yaml.safe_load(f)
        return {
            "exists": True,
            "project_id": state.get("project_id"),
            "updated_at": state.get("updated_at"),
            "state_hash": state.get("state_hash"),
            "artifact_count": len(state.get("artifact_hashes", {}))
        }
    except Exception:
        return {"exists": False, "error": "Could not parse state file"}


def main():
    """
    CLI entry point to update and verify the project state.
    """
    import argparse

    parser = argparse.ArgumentParser(description="Manage llmXive project state")
    parser.add_argument("--update", action="store_true", help="Update the state file")
    parser.add_argument("--verify", action="store_true", help="Verify state integrity")
    parser.add_argument("--summary", action="store_true", help="Show state summary")
    parser.add_argument("--file", type=str, help="Override state file path")

    args = parser.parse_args()

    state_path = Path(args.file) if args.file else STATE_FILE_PATH

    if args.update:
        print(f"Updating state file: {state_path}")
        try:
            state = update_state_file(state_file_path=state_path)
            print(f"Success. State hash: {state['state_hash']}")
            print(f"Tracked {len(state['artifact_hashes'])} artifacts.")
        except Exception as e:
            print(f"Error updating state: {e}")
            return 1

    if args.verify:
        print(f"Verifying state file: {state_path}")
        if verify_state_integrity(state_file_path=state_path):
            print("State integrity verified.")
        else:
            print("State integrity check FAILED.")
            return 1

    if args.summary:
        summary = get_state_summary(state_file_path=state_path)
        if summary["exists"]:
            print(f"Project: {summary['project_id']}")
            print(f"Updated: {summary['updated_at']}")
            print(f"State Hash: {summary['state_hash']}")
            print(f"Artifacts: {summary['artifact_count']}")
        else:
            print("State file does not exist or is invalid.")

    if not (args.update or args.verify or args.summary):
        parser.print_help()
        return 0

    return 0


if __name__ == "__main__":
    exit(main())