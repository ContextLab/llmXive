"""
State management utility for artifact versioning.

Implements Constitution Principle V: Track artifact provenance and versioning.
This module manages the state/manifest.yaml to record checksums, versions,
and dependencies of all generated artifacts in the research pipeline.
"""

import os
import json
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
import datetime

from .data_manifest import calculate_file_checksum, load_manifest, save_manifest

STATE_DIR = Path("state")
MANIFEST_PATH = STATE_DIR / "manifest.yaml"
VERSION_FILE = STATE_DIR / "version.txt"


def ensure_state_dir() -> Path:
    """Ensure the state directory exists."""
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    return STATE_DIR


def get_current_version() -> str:
    """
    Get the current pipeline version.
    Reads from state/version.txt, defaults to '0.0.0' if not found.
    """
    ensure_state_dir()
    if VERSION_FILE.exists():
        return VERSION_FILE.read_text().strip()
    return "0.0.0"


def set_version(version: str) -> None:
    """
    Set the current pipeline version.
    Writes to state/version.txt.
    """
    ensure_state_dir()
    VERSION_FILE.write_text(version)


def get_artifact_metadata(file_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Calculate metadata for a specific artifact file.

    Args:
        file_path: Path to the artifact file.

    Returns:
        Dictionary containing file path, checksum, size, and timestamp.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Artifact file not found: {file_path}")

    checksum = calculate_file_checksum(path)
    stat = path.stat()

    return {
        "path": str(path.relative_to(Path.cwd())),
        "checksum": checksum,
        "size_bytes": stat.st_size,
        "created_at": datetime.datetime.fromtimestamp(stat.st_ctime).isoformat(),
        "modified_at": datetime.datetime.fromtimestamp(stat.st_mtime).isoformat(),
    }


def update_state_for_artifact(
    file_path: Union[str, Path],
    task_id: str,
    description: str,
    dependencies: Optional[List[str]] = None,
    version: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Update the state manifest with a new or updated artifact.

    This function records the artifact's checksum, size, and metadata
    in state/manifest.yaml, linking it to the task that produced it.

    Args:
        file_path: Path to the artifact file.
        task_id: The task ID that produced this artifact (e.g., 'T006').
        description: Human-readable description of the artifact.
        dependencies: Optional list of upstream task IDs this artifact depends on.
        version: Optional specific version string. If None, uses current version.

    Returns:
        The updated manifest entry for this artifact.

    Raises:
        FileNotFoundError: If the artifact file does not exist.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Cannot update state for non-existent file: {file_path}")

    if version is None:
        version = get_current_version()

    metadata = get_artifact_metadata(path)
    entry = {
        "task_id": task_id,
        "version": version,
        "description": description,
        "dependencies": dependencies or [],
        "metadata": metadata,
        "updated_at": datetime.datetime.now().isoformat(),
    }

    manifest = load_manifest()
    manifest["artifacts"][str(path.relative_to(Path.cwd()))] = entry
    manifest["last_updated"] = datetime.datetime.now().isoformat()

    save_manifest(manifest)
    return entry


def get_artifact_state(file_path: Union[str, Path]) -> Optional[Dict[str, Any]]:
    """
    Retrieve the current state entry for an artifact.

    Args:
        file_path: Path to the artifact file.

    Returns:
        The artifact's state entry if found, None otherwise.
    """
    manifest = load_manifest()
    rel_path = str(Path(file_path).relative_to(Path.cwd()))
    return manifest.get("artifacts", {}).get(rel_path)


def verify_artifact_integrity(file_path: Union[str, Path]) -> bool:
    """
    Verify that an artifact's current checksum matches the recorded checksum.

    Args:
        file_path: Path to the artifact file.

    Returns:
        True if the checksum matches the recorded value, False otherwise.
    """
    state_entry = get_artifact_state(file_path)
    if not state_entry:
        return False

    current_checksum = calculate_file_checksum(file_path)
    recorded_checksum = state_entry["metadata"]["checksum"]

    return current_checksum == recorded_checksum


def get_pipeline_version_history() -> List[Dict[str, Any]]:
    """
    Get the version history from the manifest.

    Returns:
        List of version records with timestamps and artifact counts.
    """
    manifest = load_manifest()
    return manifest.get("version_history", [])


def record_version_snapshot(task_id: str, description: str) -> str:
    """
    Record a version snapshot in the manifest.

    This creates a new entry in the version_history list, capturing
    the current state of all registered artifacts.

    Args:
        task_id: The task ID triggering this snapshot.
        description: Description of what changed in this version.

    Returns:
        The new version string (format: YYYYMMDDHHMMSS).
    """
    ensure_state_dir()
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    version = f"v{timestamp}"

    manifest = load_manifest()

    # Create version entry
    version_entry = {
        "version": version,
        "task_id": task_id,
        "description": description,
        "timestamp": datetime.datetime.now().isoformat(),
        "artifact_count": len(manifest.get("artifacts", {})),
        "checksums": {
            path: entry["metadata"]["checksum"]
            for path, entry in manifest.get("artifacts", {}).items()
        },
    }

    manifest.setdefault("version_history", []).append(version_entry)
    manifest["current_version"] = version
    manifest["last_updated"] = datetime.datetime.now().isoformat()

    save_manifest(manifest)
    set_version(version)

    return version


def main():
    """
    CLI entry point for state management operations.

    Usage:
        python code/utils/update_state.py --update <file_path> --task <task_id> --desc <description>
        python code/utils/update_state.py --verify <file_path>
        python code/utils/update_state.py --snapshot --task <task_id> --desc <description>
        python code/utils/update_state.py --list
    """
    import argparse

    parser = argparse.ArgumentParser(
        description="Manage artifact state and versioning for the research pipeline."
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Update command
    update_parser = subparsers.add_parser("update", help="Update state for an artifact")
    update_parser.add_argument("file_path", help="Path to the artifact file")
    update_parser.add_argument("--task", required=True, help="Task ID that produced this artifact")
    update_parser.add_argument("--desc", required=True, help="Description of the artifact")
    update_parser.add_argument("--deps", nargs="*", default=[], help="List of upstream task IDs")
    update_parser.add_argument("--version", help="Specific version string (optional)")

    # Verify command
    verify_parser = subparsers.add_parser("verify", help="Verify artifact integrity")
    verify_parser.add_argument("file_path", help="Path to the artifact file")

    # Snapshot command
    snapshot_parser = subparsers.add_parser("snapshot", help="Record a version snapshot")
    snapshot_parser.add_argument("--task", required=True, help="Task ID triggering this snapshot")
    snapshot_parser.add_argument("--desc", required=True, help="Description of changes")

    # List command
    subparsers.add_parser("list", help="List all registered artifacts")

    args = parser.parse_args()

    if args.command == "update":
        try:
            entry = update_state_for_artifact(
                args.file_path,
                args.task,
                args.desc,
                args.deps,
                args.version,
            )
            print(f"Updated state for: {entry['metadata']['path']}")
            print(f"Checksum: {entry['metadata']['checksum']}")
            print(f"Version: {entry['version']}")
        except FileNotFoundError as e:
            print(f"Error: {e}")
            return 1

    elif args.command == "verify":
        if verify_artifact_integrity(args.file_path):
            print(f"Integrity verified: {args.file_path}")
            return 0
        else:
            print(f"Integrity check FAILED: {args.file_path}")
            return 1

    elif args.command == "snapshot":
        version = record_version_snapshot(args.task, args.desc)
        print(f"Recorded version snapshot: {version}")

    elif args.command == "list":
        manifest = load_manifest()
        artifacts = manifest.get("artifacts", {})
        if not artifacts:
            print("No artifacts registered in state manifest.")
        else:
            print("Registered artifacts:")
            for path, entry in artifacts.items():
                print(f"  {path}")
                print(f"    Task: {entry['task_id']}")
                print(f"    Version: {entry['version']}")
                print(f"    Checksum: {entry['metadata']['checksum']}")
                print()

    else:
        parser.print_help()
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
