"""
State Manager for Artifact Hashing and Project State Persistence.

This module handles:
- Computing SHA-256 hashes for artifact files.
- Scanning directories for data artifacts.
- Loading, saving, and updating the project state YAML file.
- Verifying artifact integrity against stored hashes.
"""

import hashlib
import logging
import os
from pathlib import Path
from typing import Dict, Any, List, Optional

import yaml

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
STATE_DIR = PROJECT_ROOT / "state" / "projects"
STATE_FILE = STATE_DIR / "PROJ-006-agriculture-optimization.yaml"
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"


def compute_file_hash(file_path: Path) -> str:
    """
    Compute the SHA-256 hash of a file.

    Args:
        file_path: Path to the file to hash.

    Returns:
        Hexadecimal string of the SHA-256 hash.

    Raises:
        FileNotFoundError: If the file does not exist.
        IOError: If the file cannot be read.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    except IOError as e:
        raise IOError(f"Error reading file {file_path}: {e}")


def scan_directory_for_artifacts(directory: Path) -> List[Path]:
    """
    Recursively scan a directory for data artifacts (files).

    Args:
        directory: Path to the directory to scan.

    Returns:
        List of Path objects for all files found.
    """
    if not directory.exists():
        logger.warning(f"Directory does not exist, skipping: {directory}")
        return []

    artifacts = []
    for root, _, files in os.walk(directory):
        for file in files:
            # Skip hidden files or common non-data files
            if file.startswith('.'):
                continue
            artifacts.append(Path(root) / file)

    return artifacts


def load_state() -> Dict[str, Any]:
    """
    Load the project state from the YAML file.

    Returns:
        Dictionary containing the project state.
        Returns an empty dict if the file does not exist.
    """
    if not STATE_FILE.exists():
        logger.info(f"State file not found, initializing new state: {STATE_FILE}")
        return {
            "project_id": "PROJ-006-agriculture-optimization",
            "last_updated": None,
            "artifacts": {}
        }

    try:
        with open(STATE_FILE, "r") as f:
            state = yaml.safe_load(f)
            if state is None:
                return {
                    "project_id": "PROJ-006-agriculture-optimization",
                    "last_updated": None,
                    "artifacts": {}
                }
            return state
    except yaml.YAMLError as e:
        logger.error(f"Error parsing state file {STATE_FILE}: {e}")
        return {
            "project_id": "PROJ-006-agriculture-optimization",
            "last_updated": None,
            "artifacts": {}
        }


def save_state(state: Dict[str, Any]) -> None:
    """
    Save the project state to the YAML file.

    Args:
        state: Dictionary containing the project state.
    """
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(STATE_FILE, "w") as f:
            yaml.dump(state, f, default_flow_style=False, sort_keys=False)
        logger.info(f"State saved to {STATE_FILE}")
    except IOError as e:
        logger.error(f"Error saving state file {STATE_FILE}: {e}")
        raise


def update_artifact_hashes() -> Dict[str, str]:
    """
    Scan data directories, compute hashes, and update the state file.

    Returns:
        Dictionary of relative paths to their new hashes.
    """
    state = load_state()
    new_hashes = {}

    # Define directories to scan
    scan_dirs = [DATA_RAW_DIR, DATA_PROCESSED_DIR]

    for scan_dir in scan_dirs:
        if not scan_dir.exists():
            logger.warning(f"Skipping non-existent directory: {scan_dir}")
            continue

        artifacts = scan_directory_for_artifacts(scan_dir)
        for artifact_path in artifacts:
            try:
                file_hash = compute_file_hash(artifact_path)
                relative_path = str(artifact_path.relative_to(PROJECT_ROOT))
                new_hashes[relative_path] = file_hash
                logger.debug(f"Hashed: {relative_path} -> {file_hash[:16]}...")
            except (FileNotFoundError, IOError) as e:
                logger.error(f"Skipping artifact {artifact_path} due to error: {e}")

    # Update state
    state["artifacts"] = new_hashes
    state["last_updated"] = str(Path().cwd()) # Or use datetime if desired
    save_state(state)

    logger.info(f"Updated hashes for {len(new_hashes)} artifacts.")
    return new_hashes


def verify_artifacts() -> bool:
    """
    Verify that current artifact hashes match the stored state.

    Returns:
        True if all artifacts match, False otherwise.
    """
    state = load_state()
    stored_hashes = state.get("artifacts", {})

    if not stored_hashes:
        logger.warning("No stored hashes found. Nothing to verify.")
        return False

    all_valid = True
    for relative_path, expected_hash in stored_hashes.items():
        full_path = PROJECT_ROOT / relative_path

        if not full_path.exists():
            logger.error(f"Artifact missing: {relative_path}")
            all_valid = False
            continue

        try:
            current_hash = compute_file_hash(full_path)
            if current_hash != expected_hash:
                logger.error(f"Hash mismatch for {relative_path}")
                logger.error(f"  Expected: {expected_hash}")
                logger.error(f"  Found:    {current_hash}")
                all_valid = False
            else:
                logger.debug(f"Verified: {relative_path}")
        except Exception as e:
            logger.error(f"Error verifying {relative_path}: {e}")
            all_valid = False

    return all_valid


def main() -> None:
    """
    CLI entry point for the state manager.
    """
    import argparse

    parser = argparse.ArgumentParser(description="Manage project artifact state and hashes.")
    parser.add_argument(
        "command",
        choices=["update", "verify", "dry-run"],
        help="Command to execute: update (scan & save), verify (check against saved), or dry-run (scan only)"
    )
    args = parser.parse_args()

    if args.command == "update":
        logger.info("Running update command...")
        update_artifact_hashes()
    elif args.command == "verify":
        logger.info("Running verify command...")
        if verify_artifacts():
            logger.info("Verification successful: All artifacts match.")
        else:
            logger.error("Verification failed: Mismatches or missing files detected.")
    elif args.command == "dry-run":
        logger.info("Running dry-run (scanning only, not saving)...")
        # Simulate update logic without saving to state file
        scan_dirs = [DATA_RAW_DIR, DATA_PROCESSED_DIR]
        total_files = 0
        for scan_dir in scan_dirs:
            if scan_dir.exists():
                artifacts = scan_directory_for_artifacts(scan_dir)
                for artifact_path in artifacts:
                    try:
                        file_hash = compute_file_hash(artifact_path)
                        logger.info(f"DRY-RUN: {artifact_path.relative_to(PROJECT_ROOT)} -> {file_hash[:16]}...")
                        total_files += 1
                    except Exception as e:
                        logger.error(f"Error hashing {artifact_path}: {e}")
        logger.info(f"Dry-run complete. Scanned {total_files} files.")

if __name__ == "__main__":
    main()
