"""
update_state_yaml.py

Implements Constitution Principle V and FR-020:
Update state.yaml with artifact hashes (SHA-256) and metadata (size, timestamp)
for all relevant artifacts in the project.
"""

import argparse
import hashlib
import json
import os
import sys
import time
from pathlib import Path
from typing import Dict, Any, List, Optional

import yaml

# Project root is assumed to be the parent of 'code/'
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
STATE_FILE_PATH = PROJECT_ROOT / "state" / "projects" / "PROJ-964-llmxive-follow-up-extending-wan-streamer.yaml"

# Directories to scan for artifacts
ARTIFACT_DIRS = [
    "data/raw",
    "data/processed",
    "data/models",
    "data/metrics",
    "code/models",
    "code/data",
    "figures",
]

# Extensions to include
FILE_EXTENSIONS = {".parquet", ".pt", ".pth", ".json", ".csv", ".yaml", ".yml", ".txt", ".png", ".jpg"}


def compute_file_hash(file_path: Path, algorithm: str = "sha256") -> str:
    """
    Compute the SHA-256 hash of a file.

    Args:
        file_path: Path to the file.
        algorithm: Hash algorithm (default: sha256).

    Returns:
        Hex digest of the file hash.
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        # Read in chunks to handle large files
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def get_file_size_mb(file_path: Path) -> float:
    """
    Get the file size in megabytes.

    Args:
        file_path: Path to the file.

    Returns:
        File size in MB.
    """
    return file_path.stat().st_size / (1024 * 1024)


def scan_directories(base_dir: Path, extensions: set) -> List[Path]:
    """
    Scan a directory tree for files with specific extensions.

    Args:
        base_dir: Base directory to scan.
        extensions: Set of allowed file extensions.

    Returns:
        List of matching file paths.
    """
    artifacts = []
    if not base_dir.exists():
        return artifacts

    for root, _, files in os.walk(base_dir):
        for file in files:
            if Path(file).suffix.lower() in extensions:
                artifacts.append(Path(root) / file)
    return artifacts


def load_state_yaml(state_path: Path) -> Dict[str, Any]:
    """
    Load the existing state.yaml file. If it doesn't exist, return a new structure.

    Args:
        state_path: Path to the state file.

    Returns:
        Dictionary representing the state.
    """
    if not state_path.exists():
        # Ensure parent directory exists
        state_path.parent.mkdir(parents=True, exist_ok=True)
        return {
            "project_id": "PROJ-964-llmxive-follow-up-extending-wan-streamer",
            "last_updated": None,
            "artifacts": {},
            "config": {},
        }

    try:
        with open(state_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    except yaml.YAMLError as e:
        print(f"Error parsing existing state file: {e}", file=sys.stderr)
        return {
            "project_id": "PROJ-964-llmxive-follow-up-extending-wan-streamer",
            "last_updated": None,
            "artifacts": {},
            "config": {},
        }


def update_state_with_artifacts(
    state: Dict[str, Any], artifacts: List[Path], relative_base: Path
) -> None:
    """
    Update the state dictionary with artifact metadata.

    Args:
        state: The state dictionary to update.
        artifacts: List of artifact paths.
        relative_base: Base path to compute relative paths.
    """
    if "artifacts" not in state:
        state["artifacts"] = {}

    for artifact_path in artifacts:
        if not artifact_path.exists():
            continue

        try:
            rel_path = artifact_path.relative_to(relative_base)
            file_hash = compute_file_hash(artifact_path)
            file_size = get_file_size_mb(artifact_path)
            m_time = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(artifact_path.stat().st_mtime))

            state["artifacts"][str(rel_path)] = {
                "hash": file_hash,
                "size_mb": round(file_size, 4),
                "last_modified": m_time,
                "type": "file",
            }
        except Exception as e:
            print(f"Warning: Could not process {artifact_path}: {e}", file=sys.stderr)


def save_state_yaml(state: Dict[str, Any], state_path: Path) -> None:
    """
    Save the state dictionary to the state file.

    Args:
        state: The state dictionary to save.
        state_path: Path to the state file.
    """
    state["last_updated"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

    # Ensure parent directory exists
    state_path.parent.mkdir(parents=True, exist_ok=True)

    with open(state_path, "w", encoding="utf-8") as f:
        yaml.dump(state, f, default_flow_style=False, sort_keys=False, allow_unicode=True)


def main(args: Optional[argparse.Namespace] = None) -> None:
    """
    Main entry point for updating state.yaml.

    Args:
        args: Optional namespace with command-line arguments.
    """
    parser = argparse.ArgumentParser(
        description="Update state.yaml with artifact hashes and metadata."
    )
    parser.add_argument(
        "--state-path",
        type=str,
        default=str(STATE_FILE_PATH),
        help="Path to the state.yaml file.",
    )
    parser.add_argument(
        "--scan-dirs",
        type=str,
        nargs="+",
        default=ARTIFACT_DIRS,
        help="Directories to scan for artifacts (relative to project root).",
    )
    parser.add_argument(
        "--extensions",
        type=str,
        nargs="+",
        default=list(FILE_EXTENSIONS),
        help="File extensions to include.",
    )
    parser.add_argument(
        "--project-root",
        type=str,
        default=str(PROJECT_ROOT),
        help="Project root directory.",
    )

    parsed_args = parser.parse_args() if args is None else args

    project_root = Path(parsed_args.project_root)
    state_path = Path(parsed_args.state_path)

    print(f"Project Root: {project_root}")
    print(f"State File: {state_path}")
    print(f"Scanning directories: {parsed_args.scan_dirs}")

    # Load existing state
    state = load_state_yaml(state_path)
    state["project_id"] = "PROJ-964-llmxive-follow-up-extending-wan-streamer"

    # Collect artifacts
    all_artifacts = []
    for dir_name in parsed_args.scan_dirs:
        dir_path = project_root / dir_name
        if dir_path.exists():
            print(f"Scanning: {dir_path}")
            artifacts = scan_directories(
                dir_path, set(parsed_args.extensions)
            )
            all_artifacts.extend(artifacts)
        else:
            print(f"Warning: Directory does not exist: {dir_path}")

    print(f"Found {len(all_artifacts)} artifacts.")

    # Update state with artifacts
    update_state_with_artifacts(state, all_artifacts, project_root)

    # Save updated state
    save_state_yaml(state, state_path)
    print(f"State file updated: {state_path}")

    # Print summary
    artifact_count = len(state.get("artifacts", {}))
    print(f"Total artifacts registered in state: {artifact_count}")


if __name__ == "__main__":
    main()