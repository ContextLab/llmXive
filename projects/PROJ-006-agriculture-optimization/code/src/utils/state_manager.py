"""
State Manager Module for llmXive Project PROJ-006-agriculture-optimization.

Handles artifact hashing, state persistence, and verification of data artifacts
in the data/raw and data/processed directories.
"""

import hashlib
import logging
import os
from pathlib import Path
from typing import Dict, Any, List, Optional

import yaml

from src.utils.io_helpers import setup_logging

# Configure logging for this module
logger = setup_logging("state_manager")


def compute_file_hash(file_path: Path) -> str:
    """
    Compute the SHA-256 hash of a file.

    Args:
        file_path: Path to the file to hash.

    Returns:
        Hexadecimal string representation of the file hash.
    """
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except FileNotFoundError:
        logger.error(f"File not found: {file_path}")
        raise
    except PermissionError:
        logger.error(f"Permission denied reading file: {file_path}")
        raise
    except Exception as e:
        logger.error(f"Error hashing file {file_path}: {e}")
        raise


def scan_directory_for_artifacts(
    directory: Path,
    extensions: Optional[List[str]] = None
) -> List[Path]:
    """
    Recursively scan a directory for files matching specific extensions.

    Args:
        directory: Root directory to scan.
        extensions: List of file extensions to include (e.g., ['.csv', '.parquet']).
                   If None, includes all files.

    Returns:
        List of Path objects for matching files.
    """
    artifacts = []
    if not directory.exists():
        logger.warning(f"Directory does not exist: {directory}")
        return artifacts

    if not directory.is_dir():
        logger.warning(f"Path is not a directory: {directory}")
        return artifacts

    for root, _, files in os.walk(directory):
        for file in files:
            file_path = Path(root) / file
            if extensions:
                if file_path.suffix in extensions:
                    artifacts.append(file_path)
            else:
                artifacts.append(file_path)

    return artifacts


def load_state(state_path: Path) -> Dict[str, Any]:
    """
    Load the state YAML file.

    Args:
        state_path: Path to the state YAML file.

    Returns:
        Dictionary containing the state data.
    """
    if not state_path.exists():
        logger.info(f"State file not found, initializing empty state: {state_path}")
        return {
            "project_id": "PROJ-006-agriculture-optimization",
            "artifact_hashes": {},
            "last_updated": None
        }

    try:
        with open(state_path, "r") as f:
            state = yaml.safe_load(f)
            if state is None:
                return {
                    "project_id": "PROJ-006-agriculture-optimization",
                    "artifact_hashes": {},
                    "last_updated": None
                }
            return state
    except yaml.YAMLError as e:
        logger.error(f"Error parsing YAML state file: {e}")
        raise
    except Exception as e:
        logger.error(f"Error loading state file: {e}")
        raise


def save_state(state: Dict[str, Any], state_path: Path) -> None:
    """
    Save the state dictionary to a YAML file.

    Args:
        state: Dictionary to save.
        state_path: Path to the state YAML file.
    """
    try:
        # Ensure directory exists
        state_path.parent.mkdir(parents=True, exist_ok=True)

        with open(state_path, "w") as f:
            yaml.dump(state, f, default_flow_style=False, sort_keys=False)

        logger.info(f"State saved to {state_path}")
    except Exception as e:
        logger.error(f"Error saving state file: {e}")
        raise


def update_artifact_hashes(
    state: Dict[str, Any],
    data_dirs: List[Path],
    extensions: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Scan data directories and update artifact hashes in the state.

    Args:
        state: Current state dictionary.
        data_dirs: List of directory paths to scan.
        extensions: List of file extensions to include.

    Returns:
        Updated state dictionary.
    """
    import datetime

    artifact_hashes = {}

    for data_dir in data_dirs:
        if not data_dir.exists():
            logger.info(f"Skipping non-existent directory: {data_dir}")
            continue

        files = scan_directory_for_artifacts(data_dir, extensions)
        if not files:
            logger.info(f"No artifacts found in {data_dir}")
            continue

        dir_key = str(data_dir.relative_to(Path.cwd()))
        dir_hashes = []

        for file_path in files:
            try:
                file_hash = compute_file_hash(file_path)
                rel_path = str(file_path.relative_to(Path.cwd()))
                dir_hashes.append({
                    "path": rel_path,
                    "hash": file_hash
                })
            except Exception as e:
                logger.warning(f"Skipping file {file_path} due to error: {e}")

        if dir_hashes:
            artifact_hashes[dir_key] = dir_hashes
        else:
            logger.info(f"No valid artifacts to hash in {data_dir}")

    state["artifact_hashes"] = artifact_hashes
    state["last_updated"] = datetime.datetime.now().isoformat()

    return state


def verify_artifacts(state: Dict[str, Any], data_dirs: List[Path]) -> bool:
    """
    Verify that artifacts in the state still exist and have matching hashes.

    Args:
        state: State dictionary containing artifact hashes.
        data_dirs: List of directory paths to verify against.

    Returns:
        True if all artifacts are valid, False otherwise.
    """
    all_valid = True

    for dir_key, artifacts in state.get("artifact_hashes", {}).items():
        dir_path = Path.cwd() / dir_key

        if not dir_path.exists():
            logger.warning(f"Directory missing for state entry: {dir_key}")
            all_valid = False
            continue

        for artifact in artifacts:
            file_path = Path.cwd() / artifact["path"]

            if not file_path.exists():
                logger.warning(f"Artifact missing: {artifact['path']}")
                all_valid = False
                continue

            try:
                current_hash = compute_file_hash(file_path)
                if current_hash != artifact["hash"]:
                    logger.warning(f"Hash mismatch for {artifact['path']}")
                    all_valid = False
            except Exception as e:
                logger.warning(f"Error verifying artifact {artifact['path']}: {e}")
                all_valid = False

    return all_valid


def main() -> int:
    """
    Main entry point for the state manager CLI.

    Returns:
        Exit code (0 for success, 1 for failure).
    """
    import argparse

    parser = argparse.ArgumentParser(
        description="Manage artifact state and hashes for the project."
    )
    parser.add_argument(
        "--state-file",
        type=str,
        default="state/projects/PROJ-006-agriculture-optimization.yaml",
        help="Path to the state YAML file."
    )
    parser.add_argument(
        "--data-dirs",
        type=str,
        nargs="+",
        default=["data/raw", "data/processed"],
        help="Data directories to scan for artifacts."
    )
    parser.add_argument(
        "--extensions",
        type=str,
        nargs="+",
        default=[".csv", ".parquet", ".json", ".yaml", ".yml", ".txt"],
        help="File extensions to include in the scan."
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="Verify existing artifact hashes instead of updating."
    )

    args = parser.parse_args()

    state_path = Path(args.state_file)
    data_dirs = [Path(d) for d in args.data_dirs]
    extensions = args.extensions

    try:
        state = load_state(state_path)

        if args.verify:
            logger.info("Verifying artifact integrity...")
            if verify_artifacts(state, data_dirs):
                logger.info("All artifacts verified successfully.")
                return 0
            else:
                logger.error("Artifact verification failed.")
                return 1
        else:
            logger.info(f"Scanning directories: {data_dirs}")
            state = update_artifact_hashes(state, data_dirs, extensions)
            save_state(state, state_path)
            logger.info("State updated successfully.")
            return 0

    except Exception as e:
        logger.error(f"State manager execution failed: {e}")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())
