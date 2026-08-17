"""
State Manager for PROJ-006-agriculture-optimization.

Handles artifact hashing and maintains a YAML state file tracking content hashes
for data artifacts in data/raw/* and data/processed/*.
"""

import hashlib
import logging
import os
from pathlib import Path
from typing import Dict, Any, List, Optional

import yaml

# Import shared exceptions from io_helpers
from src.utils.io_helpers import FatalError

logger = logging.getLogger(__name__)

# Project-specific paths
PROJECT_ROOT = Path(__file__).resolve().parents[3]
STATE_DIR = PROJECT_ROOT / "state" / "projects"
STATE_FILE = STATE_DIR / "PROJ-006-agriculture-optimization.yaml"
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

# Supported extensions for hashing
HASH_EXTENSIONS = {".csv", ".parquet", ".json", ".yaml", ".yml", ".txt", ".log"}

def compute_file_hash(file_path: Path) -> str:
    """
    Compute SHA-256 hash of a file's contents.

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
        logger.error(f"Failed to read file for hashing: {file_path} - {e}")
        raise FatalError(f"Cannot compute hash for {file_path}: {e}")

def scan_directory_for_artifacts(directory: Path) -> List[Path]:
    """
    Recursively scan a directory for artifacts with supported extensions.

    Args:
        directory: Root directory to scan.

    Returns:
        List of Path objects for found artifacts.
    """
    if not directory.exists():
        logger.warning(f"Directory does not exist, skipping: {directory}")
        return []

    artifacts = []
    for root, _, files in os.walk(directory):
        for file in files:
            file_path = Path(root) / file
            if file_path.suffix.lower() in HASH_EXTENSIONS:
                artifacts.append(file_path)
    return artifacts

def load_state() -> Dict[str, Any]:
    """
    Load the current state file if it exists.

    Returns:
        Dictionary containing state data, or empty dict if file missing.
    """
    if not STATE_FILE.exists():
        logger.info(f"State file not found, initializing new state: {STATE_FILE}")
        return {
            "project_id": "PROJ-006-agriculture-optimization",
            "last_updated": None,
            "artifacts": {}
        }

    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            state = yaml.safe_load(f)
            if state is None:
                return {
                    "project_id": "PROJ-006-agriculture-optimization",
                    "last_updated": None,
                    "artifacts": {}
                }
            return state
    except yaml.YAMLError as e:
        logger.error(f"Failed to parse state file {STATE_FILE}: {e}")
        raise FatalError(f"Corrupted state file: {e}")

def save_state(state: Dict[str, Any]) -> None:
    """
    Save the state dictionary to the YAML file.

    Args:
        state: Dictionary to serialize and save.
    """
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    try:
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            yaml.safe_dump(state, f, default_flow_style=False, sort_keys=False)
        logger.info(f"State file updated: {STATE_FILE}")
    except (IOError, OSError) as e:
        logger.error(f"Failed to write state file: {e}")
        raise FatalError(f"Cannot save state to {STATE_FILE}: {e}")

def update_artifact_hashes() -> Dict[str, Any]:
    """
    Scan data/raw and data/processed directories, compute hashes for all artifacts,
    and update the state file.

    Returns:
        Dictionary mapping relative artifact paths to their hashes.
    """
    logger.info("Starting artifact hash update for data/raw and data/processed...")

    current_state = load_state()
    new_artifacts: Dict[str, str] = {}

    # Scan both directories
    for data_dir in [DATA_RAW_DIR, DATA_PROCESSED_DIR]:
        artifacts = scan_directory_for_artifacts(data_dir)
        for artifact_path in artifacts:
            # Compute relative path from project root
            try:
                rel_path = artifact_path.relative_to(PROJECT_ROOT)
            except ValueError:
                logger.warning(f"Artifact outside project root, skipping: {artifact_path}")
                continue

            file_hash = compute_file_hash(artifact_path)
            new_artifacts[str(rel_path)] = file_hash

    # Update state
    current_state["artifacts"] = new_artifacts
    current_state["last_updated"] = str(Path(__file__).resolve().parents[0]) # Placeholder for timestamp logic if needed
    # Use a simple timestamp for tracking
    import datetime
    current_state["last_updated"] = datetime.datetime.now().isoformat()

    save_state(current_state)
    logger.info(f"Updated {len(new_artifacts)} artifact hashes.")
    return new_artifacts

def verify_artifacts(artifact_paths: Optional[List[str]] = None) -> bool:
    """
    Verify that artifacts in the state file match their current hashes on disk.

    Args:
        artifact_paths: Optional list of specific relative paths to verify.
                       If None, verifies all tracked artifacts.

    Returns:
        True if all verified artifacts match, False otherwise.
    """
    current_state = load_state()
    tracked_artifacts = current_state.get("artifacts", {})

    if artifact_paths:
        tracked_artifacts = {k: v for k, v in tracked_artifacts.items() if k in artifact_paths}

    all_valid = True
    for rel_path, expected_hash in tracked_artifacts.items():
        full_path = PROJECT_ROOT / rel_path
        if not full_path.exists():
            logger.warning(f"Artifact missing from disk: {full_path}")
            all_valid = False
            continue

        try:
            actual_hash = compute_file_hash(full_path)
            if actual_hash != expected_hash:
                logger.error(f"Hash mismatch for {full_path}: expected {expected_hash}, got {actual_hash}")
                all_valid = False
            else:
                logger.debug(f"Hash verified: {full_path}")
        except FatalError:
            all_valid = False

    return all_valid

def main() -> None:
    """
    CLI entry point to update artifact hashes.
    """
    logging.basicConfig(level=logging.INFO)
    logger.info("Running state_manager to update artifact hashes...")
    hashes = update_artifact_hashes()
    logger.info(f"Total artifacts hashed: {len(hashes)}")
    for path, h in hashes.items():
        logger.info(f"  {path}: {h[:16]}...")

if __name__ == "__main__":
    main()
