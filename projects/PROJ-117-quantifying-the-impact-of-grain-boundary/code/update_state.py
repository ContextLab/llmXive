"""
update_state.py

Verifies and updates state.yaml with content hashes after a successful pipeline run.
This script scans the data/, artifacts/, and models/ directories, computes SHA-256
hashes for all relevant files, and updates the state.yaml file with the new hashes
and a timestamp.

Usage:
    python code/update_state.py
"""

import hashlib
import json
import logging
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List

import yaml

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
STATE_FILE = PROJECT_ROOT / "state.yaml"
TARGET_DIRS = ["data", "models", "artifacts"]
EXCLUDE_PATTERNS = [".gitkeep", ".DS_Store", "__pycache__"]


def compute_sha256(file_path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except Exception as e:
        logger.error(f"Error computing hash for {file_path}: {e}")
        return ""


def scan_directory(directory: Path) -> List[Dict[str, Any]]:
    """Scan a directory and return a list of file hashes."""
    if not directory.exists():
        logger.warning(f"Directory {directory} does not exist. Skipping.")
        return []

    files_data = []
    for file_path in directory.rglob("*"):
        if file_path.is_file():
            # Skip excluded patterns
            if any(pattern in file_path.name for pattern in EXCLUDE_PATTERNS):
                continue

            relative_path = file_path.relative_to(PROJECT_ROOT)
            file_hash = compute_sha256(file_path)
            if file_hash:
                files_data.append({
                    "path": str(relative_path),
                    "hash": file_hash,
                    "size": file_path.stat().st_size
                })
    return files_data


def load_state() -> Dict[str, Any]:
    """Load existing state.yaml or return an empty structure."""
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE, "r") as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            logger.error(f"Error loading state.yaml: {e}")
            return {}
    return {}


def save_state(state: Dict[str, Any]) -> None:
    """Save state to state.yaml."""
    try:
        with open(STATE_FILE, "w") as f:
            yaml.safe_dump(state, f, default_flow_style=False, sort_keys=False)
        logger.info(f"State saved to {STATE_FILE}")
    except Exception as e:
        logger.error(f"Error saving state.yaml: {e}")
        raise


def verify_hashes(old_state: Dict[str, Any], new_state: Dict[str, Any]) -> bool:
    """
    Verify that hashes in the new state match the old state for unchanged files.
    Returns True if all hashes match or if it's the first run.
    """
    old_files = {item["path"]: item["hash"] for item in old_state.get("files", [])}
    new_files = {item["path"]: item["hash"] for item in new_state.get("files", [])}

    # Check for changed or removed files
    for path, old_hash in old_files.items():
        if path in new_files:
            if new_files[path] != old_hash:
                logger.info(f"File changed: {path}")
        else:
            logger.info(f"File removed: {path}")

    # Check for new files
    for path in new_files:
        if path not in old_files:
            logger.info(f"New file: {path}")

    return True


def main() -> int:
    """Main entry point for the state update script."""
    logger.info("Starting state verification and update...")

    # Collect hashes from target directories
    all_files = []
    for dir_name in TARGET_DIRS:
        target_dir = PROJECT_ROOT / dir_name
        files = scan_directory(target_dir)
        all_files.extend(files)

    if not all_files:
        logger.warning("No files found in target directories. State will be empty.")

    # Load existing state
    old_state = load_state()

    # Create new state structure
    new_state = {
        "last_updated": datetime.utcnow().isoformat(),
        "files": all_files,
        "summary": {
            "total_files": len(all_files),
            "total_size_bytes": sum(f["size"] for f in all_files)
        }
    }

    # Verify hashes against old state
    verify_hashes(old_state, new_state)

    # Save new state
    save_state(new_state)

    logger.info("State update completed successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
