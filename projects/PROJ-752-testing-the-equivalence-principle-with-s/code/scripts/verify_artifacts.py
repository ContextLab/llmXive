"""
Script to verify all artifacts have content hashes and versioning discipline applied.
This implements task T047.
"""
import os
import sys
import json
import logging
from pathlib import Path
from typing import List, Dict, Any

# Add code directory to path
code_dir = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, os.path.abspath(code_dir))

from utils.hashing import (
    compute_sha256,
    hash_artifact,
    update_state_file,
    scan_and_hash_artifacts,
    verify_artifact_integrity,
)
from utils.logging import init_logging

# Initialize logging
init_logging(level=logging.INFO)
logger = logging.getLogger(__name__)

# Project root (relative to this script)
PROJECT_ROOT = os.path.join(os.path.dirname(code_dir), "..")
STATE_FILE = os.path.join(PROJECT_ROOT, "state", "projects", "PROJ-752-testing-the-equivalence-principle-with-s.yaml")
# Convert to JSON for easier handling if needed
STATE_FILE_JSON = STATE_FILE.replace(".yaml", ".json")

# Artifact patterns to scan
ARTIFACT_PATTERNS = [
    "*.csv",
    "*.json",
    "*.yaml",
    "*.yml",
    "*.png",
    "*.pdf",
    "*.txt",
    "*.log",
]

# Directories to scan
SCAN_DIRS = [
    "data/processed",
    "data/results",
    "data/raw",
    "figures",
    "docs",
    "contracts",
]


def ensure_state_file_exists() -> str:
    """Ensure the state file exists and is valid."""
    state_path = STATE_FILE_JSON
    if not os.path.exists(state_path):
        # Create directory if needed
        os.makedirs(os.path.dirname(state_path), exist_ok=True)
        # Initialize empty state
        with open(state_path, "w") as f:
            json.dump({"artifact_hashes": {}, "versions": {}, "last_verified": None}, f)
        logger.info(f"Created new state file: {state_path}")
    return state_path


def verify_existing_artifacts(state_path: str) -> bool:
    """Verify that all previously recorded artifacts still exist and match their hashes."""
    with open(state_path, "r") as f:
        state = json.load(f)

    artifact_hashes = state.get("artifact_hashes", {})
    all_valid = True

    for rel_path, expected_hash in artifact_hashes.items():
        full_path = os.path.join(PROJECT_ROOT, rel_path)
        if not os.path.exists(full_path):
            logger.warning(f"Artifact missing: {rel_path}")
            all_valid = False
        else:
            if not verify_artifact_integrity(full_path, expected_hash, rel_path):
                all_valid = False

    return all_valid


def hash_new_artifacts(state_path: str) -> Dict[str, Dict[str, Any]]:
    """Scan for new artifacts and hash them."""
    all_artifacts = {}

    for scan_dir in SCAN_DIRS:
        full_scan_dir = os.path.join(PROJECT_ROOT, scan_dir)
        if os.path.exists(full_scan_dir):
            logger.info(f"Scanning directory: {full_scan_dir}")
            artifacts = scan_and_hash_artifacts(full_scan_dir, ARTIFACT_PATTERNS, state_path)
            all_artifacts.update(artifacts)
        else:
            logger.warning(f"Scan directory not found: {full_scan_dir}")

    return all_artifacts


def main() -> int:
    """Main entry point for artifact verification."""
    logger.info("Starting artifact verification (T047)...")

    # Ensure state file exists
    state_path = ensure_state_file_exists()

    # Verify existing artifacts
    logger.info("Verifying existing artifacts...")
    existing_valid = verify_existing_artifacts(state_path)

    # Hash new artifacts
    logger.info("Scanning for new artifacts...")
    new_artifacts = hash_new_artifacts(state_path)

    # Update state file with verification timestamp
    with open(state_path, "r") as f:
        state = json.load(f)
    state["last_verified"] = __import__("datetime").datetime.now().isoformat()
    with open(state_path, "w") as f:
        json.dump(state, f, indent=2)

    # Summary
    logger.info("=" * 50)
    logger.info("ARTIFACT VERIFICATION SUMMARY")
    logger.info("=" * 50)
    logger.info(f"Existing artifacts valid: {existing_valid}")
    logger.info(f"New artifacts hashed: {len(new_artifacts)}")
    logger.info(f"Total artifacts in state: {len(state.get('artifact_hashes', {}))}")

    if not existing_valid:
        logger.error("Some existing artifacts are missing or have invalid hashes.")
        return 1

    logger.info("All artifacts verified successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
