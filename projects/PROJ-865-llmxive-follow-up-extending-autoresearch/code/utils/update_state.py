"""
update_state.py

Calculates SHA-256 hashes of pipeline artifacts and updates the state.yaml file.
This script scans specific directories for artifacts, computes their checksums,
and maintains a manifest of the project state.
"""

import hashlib
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional

import yaml

# Add project root to path if running as script
if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

from utils.logging import get_logger

# Initialize logger
logger = get_logger(__name__)

# Directories to scan for artifacts
ARTIFACT_DIRS = [
    "data/derived",
    "data/artifacts",
    "code/03_execution",
    "code/04_analysis",
]

# File extensions to include
FILE_EXTENSIONS = {".json", ".csv", ".yaml", ".yml", ".md", ".txt", ".py"}

STATE_FILE = "state.yaml"


def calculate_sha256(file_path: Path) -> str:
    """
    Calculate the SHA-256 hash of a file.

    Args:
        file_path: Path to the file to hash.

    Returns:
        Hexadecimal string of the SHA-256 hash.
    """
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except (IOError, OSError) as e:
        logger.error(f"Error reading file {file_path} for hashing: {e}")
        raise


def scan_artifacts(base_dir: Path) -> List[Dict[str, Any]]:
    """
    Scan a directory recursively for artifacts and return their metadata.

    Args:
        base_dir: Root directory to scan.

    Returns:
        List of dictionaries containing file path, hash, size, and timestamp.
    """
    artifacts = []

    if not base_dir.exists():
        logger.warning(f"Directory does not exist, skipping: {base_dir}")
        return artifacts

    for root, _, files in os.walk(base_dir):
        for file_name in files:
            if any(file_name.endswith(ext) for ext in FILE_EXTENSIONS):
                file_path = Path(root) / file_name
                try:
                    stat_info = file_path.stat()
                    file_hash = calculate_sha256(file_path)
                    artifacts.append({
                        "path": str(file_path.relative_to(Path.cwd())),
                        "sha256": file_hash,
                        "size_bytes": stat_info.st_size,
                        "modified_at": datetime.fromtimestamp(
                            stat_info.st_mtime, tz=timezone.utc
                        ).isoformat(),
                    })
                except Exception as e:
                    logger.error(f"Error processing file {file_path}: {e}")

    return artifacts


def load_current_state(state_path: Path) -> Dict[str, Any]:
    """
    Load the existing state.yaml if it exists.

    Args:
        state_path: Path to the state.yaml file.

    Returns:
        Dictionary containing the current state or an empty structure.
    """
    if state_path.exists():
        try:
            with open(state_path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            logger.warning(f"Could not load existing state file: {e}. Starting fresh.")
    return {}


def update_state_file(
    artifacts: List[Dict[str, Any]],
    state_path: Path,
    pipeline_version: Optional[str] = None,
) -> None:
    """
    Write the updated state to state.yaml.

    Args:
        artifacts: List of artifact metadata dictionaries.
        state_path: Path to the output state.yaml file.
        pipeline_version: Optional version string to record.
    """
    current_state = load_current_state(state_path)

    # Update metadata
    current_state["last_updated"] = datetime.now(timezone.utc).isoformat()
    current_state["artifact_count"] = len(artifacts)
    if pipeline_version:
        current_state["pipeline_version"] = pipeline_version

    # Update artifacts list
    current_state["artifacts"] = artifacts

    # Write back to file
    try:
        with open(state_path, "w", encoding="utf-8") as f:
            yaml.dump(current_state, f, default_flow_style=False, sort_keys=False)
        logger.info(f"State file updated successfully: {state_path}")
    except Exception as e:
        logger.error(f"Failed to write state file: {e}")
        raise


def main(pipeline_version: Optional[str] = None) -> int:
    """
    Main entry point to scan artifacts and update state.yaml.

    Args:
        pipeline_version: Optional version string to record in state.

    Returns:
        Exit code (0 for success, 1 for failure).
    """
    logger.info("Starting artifact state update...")

    project_root = Path.cwd()
    state_path = project_root / STATE_FILE

    all_artifacts: List[Dict[str, Any]] = []

    for dir_name in ARTIFACT_DIRS:
        dir_path = project_root / dir_name
        logger.info(f"Scanning directory: {dir_path}")
        artifacts = scan_artifacts(dir_path)
        all_artifacts.extend(artifacts)
        logger.info(f"Found {len(artifacts)} artifacts in {dir_name}")

    if not all_artifacts:
        logger.warning("No artifacts found to hash. State file may be empty or minimal.")

    try:
        update_state_file(all_artifacts, state_path, pipeline_version)
        logger.info("State update completed successfully.")
        return 0
    except Exception as e:
        logger.error(f"State update failed: {e}")
        return 1


if __name__ == "__main__":
    # Allow passing version via command line argument
    version = sys.argv[1] if len(sys.argv) > 1 else None
    sys.exit(main(pipeline_version=version))
