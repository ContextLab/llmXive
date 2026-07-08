"""
State Manager Module for llmXive Pipeline

Computes content hashes for artifacts and updates the state/ YAML file
to track data provenance and reproducibility.
"""
import hashlib
import os
import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional

from config import ensure_directories


def compute_file_hash(file_path: Path, algorithm: str = "sha256") -> str:
    """
    Compute the hash of a file's contents.

    Args:
        file_path: Path to the file to hash.
        algorithm: Hash algorithm to use (default: sha256).

    Returns:
        Hex digest of the file hash.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If an unsupported algorithm is requested.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    hasher = hashlib.new(algorithm)
    with open(file_path, "rb") as f:
        # Read in chunks to handle large files (e.g., NIfTI)
        for chunk in iter(lambda: f.read(65536), b""):
            hasher.update(chunk)

    return hasher.hexdigest()


def compute_directory_hash(dir_path: Path, extensions: Optional[List[str]] = None) -> str:
    """
    Compute a deterministic hash for a directory based on its file contents.

    The hash is computed by sorting files, hashing each, and then hashing
    the concatenation of all file hashes.

    Args:
        dir_path: Path to the directory.
        extensions: Optional list of file extensions to include (e.g., ['.csv', '.json']).
                    If None, all files are included.

    Returns:
        Hex digest of the directory hash.
    """
    if not dir_path.exists() or not dir_path.is_dir():
        raise NotADirectoryError(f"Directory not found: {dir_path}")

    hasher = hashlib.new("sha256")
    files = sorted(dir_path.glob("**/*"))
    files = [f for f in files if f.is_file()]

    if extensions:
        files = [f for f in files if f.suffix.lower() in [ext.lower() for ext in extensions]]

    # Sort again after filtering to ensure determinism
    files = sorted(files)

    for file_path in files:
        try:
            file_hash = compute_file_hash(file_path)
            # Include relative path in hash to detect moves/renames
            relative_path = file_path.relative_to(dir_path)
            hasher.update(relative_path.as_posix().encode("utf-8"))
            hasher.update(file_hash.encode("utf-8"))
        except (FileNotFoundError, PermissionError):
            # Skip inaccessible files but log a warning if needed
            continue

    return hasher.hexdigest()


def load_state(state_path: Path) -> Dict[str, Any]:
    """
    Load the existing state YAML file.

    Args:
        state_path: Path to the state.yaml file.

    Returns:
        Dictionary containing the state, or an empty dict if file doesn't exist.
    """
    if not state_path.exists():
        return {"artifacts": {}, "metadata": {}}

    with open(state_path, "r", encoding="utf-8") as f:
        try:
            return yaml.safe_load(f) or {"artifacts": {}, "metadata": {}}
        except yaml.YAMLError as e:
            raise RuntimeError(f"Failed to parse state file {state_path}: {e}")


def save_state(state: Dict[str, Any], state_path: Path) -> None:
    """
    Save the state dictionary to a YAML file.

    Args:
        state: Dictionary containing the state.
        state_path: Path to the state.yaml file.
    """
    ensure_directories()  # Ensure state directory exists
    with open(state_path, "w", encoding="utf-8") as f:
        yaml.safe_dump(state, f, sort_keys=False, default_flow_style=False)


def update_state_artifact(
    artifact_path: Path,
    state_path: Optional[Path] = None,
    description: Optional[str] = None
) -> None:
    """
    Compute the hash of an artifact and update the state file.

    Args:
        artifact_path: Path to the artifact file.
        state_path: Optional custom path for the state file (defaults to state/state.yaml).
        description: Optional description to store with the artifact entry.
    """
    if state_path is None:
        state_path = Path("state/state.yaml")

    if not artifact_path.exists():
        raise FileNotFoundError(f"Cannot update state: artifact not found at {artifact_path}")

    state = load_state(state_path)
    relative_path = artifact_path.relative_to(Path.cwd())

    entry = {
        "path": str(relative_path),
        "hash": compute_file_hash(artifact_path),
        "algorithm": "sha256"
    }

    if description:
        entry["description"] = description

    state["artifacts"][str(relative_path)] = entry

    # Update metadata timestamp
    state["metadata"]["last_updated"] = str(Path.cwd().resolve())

    save_state(state, state_path)


def update_state_directory(
    dir_path: Path,
    state_path: Optional[Path] = None,
    description: Optional[str] = None,
    extensions: Optional[List[str]] = None
) -> None:
    """
    Compute the hash of a directory and update the state file.

    Args:
        dir_path: Path to the directory.
        state_path: Optional custom path for the state file.
        description: Optional description to store with the directory entry.
        extensions: Optional list of file extensions to include in the hash.
    """
    if state_path is None:
        state_path = Path("state/state.yaml")

    if not dir_path.exists() or not dir_path.is_dir():
        raise NotADirectoryError(f"Cannot update state: directory not found at {dir_path}")

    state = load_state(state_path)
    relative_path = dir_path.relative_to(Path.cwd())

    entry = {
        "path": str(relative_path),
        "hash": compute_directory_hash(dir_path, extensions),
        "algorithm": "sha256",
        "type": "directory"
    }

    if description:
        entry["description"] = description

    state["artifacts"][str(relative_path)] = entry
    save_state(state, state_path)


def verify_artifact_integrity(artifact_path: Path, state_path: Optional[Path] = None) -> bool:
    """
    Verify that an artifact's current hash matches the recorded hash in state.

    Args:
        artifact_path: Path to the artifact file.
        state_path: Optional custom path for the state file.

    Returns:
        True if the artifact matches the recorded hash, False otherwise.
    """
    if state_path is None:
        state_path = Path("state/state.yaml")

    if not artifact_path.exists():
        return False

    state = load_state(state_path)
    relative_path = str(artifact_path.relative_to(Path.cwd()))

    if relative_path not in state.get("artifacts", {}):
        return False

    recorded_entry = state["artifacts"][relative_path]
    current_hash = compute_file_hash(artifact_path)
    return current_hash == recorded_entry.get("hash")


def main():
    """
    CLI entry point for state management operations.
    """
    import argparse

    parser = argparse.ArgumentParser(description="Manage pipeline state and artifact hashes")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Update command
    update_parser = subparsers.add_parser("update", help="Update state for an artifact or directory")
    update_parser.add_argument("path", help="Path to file or directory to hash")
    update_parser.add_argument("--dir", action="store_true", help="Treat path as a directory")
    update_parser.add_argument("--desc", help="Description for the state entry")
    update_parser.add_argument("--ext", nargs="*", help="File extensions to include (for directories)")

    # Verify command
    verify_parser = subparsers.add_parser("verify", help="Verify artifact integrity")
    verify_parser.add_argument("path", help="Path to artifact to verify")

    # Show command
    show_parser = subparsers.add_parser("show", help="Display current state")

    args = parser.parse_args()

    if args.command == "update":
        path = Path(args.path)
        if args.dir:
            update_state_directory(path, description=args.desc, extensions=args.ext)
            print(f"Updated state for directory: {path}")
        else:
            update_state_artifact(path, description=args.desc)
            print(f"Updated state for file: {path}")

    elif args.command == "verify":
        path = Path(args.path)
        if verify_artifact_integrity(path):
            print(f"✓ Integrity verified: {path}")
        else:
            print(f"✗ Integrity check failed: {path}")
            return 1

    elif args.command == "show":
        state = load_state(Path("state/state.yaml"))
        print(yaml.safe_dump(state, default_flow_style=False))

    else:
        parser.print_help()
        return 1

    return 0


if __name__ == "__main__":
    exit(main())