#!/usr/bin/env python3
"""
generate_state_checksums.py

Automates state file updates when artifacts change per Constitution Principle III.

This script:
1. Scans the project for artifacts that need checksums
2. Computes SHA256 checksums for each artifact
3. Updates the state file at state/projects/PROJ-024-bayesian-nonparametrics-for-anomaly-dete.yaml
4. Reports any errors or missing files

Usage:
    python generate_state_checksums.py
"""

import os
import sys
import hashlib
import yaml
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple

# Project configuration
PROJECT_ID = "PROJ-024-bayesian-nonparametrics-for-anomaly-dete"
STATE_FILE_RELATIVE = f"state/projects/{PROJECT_ID}.yaml"

# Directories to scan for artifacts
SCAN_DIRECTORIES = [
    "data/raw/",
    "data/processed/",
    "data/processed/results/",
    "code/src/",
    "code/models/",
    "code/baselines/",
    "code/evaluation/",
    "code/scripts/",
    "code/tests/",
    "specs/contracts/",
]

# File patterns to include
INCLUDE_PATTERNS = [
    "*.csv",
    "*.json",
    "*.yaml",
    "*.yml",
    "*.pkl",
    "*.pt",
    "*.pth",
    "*.npy",
    "*.png",
    "*.md",
    "*.txt",
    "*.py",
]

# File patterns to exclude
EXCLUDE_PATTERNS = [
    "__pycache__/",
    "*.pyc",
    "*.pyo",
    ".git/",
    ".pytest_cache/",
    "__init__.pyc",
    "*.log",
    ".venv/",
    "venv/",
    "node_modules/",
]

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def compute_file_checksum_sha256(file_path: Path) -> Optional[str]:
    """
    Compute SHA256 checksum for a file.

    Args:
        file_path: Path to the file

    Returns:
        SHA256 hex digest string, or None if file cannot be read
    """
    try:
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    except Exception as e:
        logger.error(f"Failed to compute checksum for {file_path}: {e}")
        return None


def get_file_size(file_path: Path) -> int:
    """Get file size in bytes."""
    try:
        return file_path.stat().st_size
    except Exception as e:
        logger.error(f"Failed to get size for {file_path}: {e}")
        return 0


def get_file_modified_time(file_path: Path) -> str:
    """Get file modification time as ISO string."""
    try:
        return datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
    except Exception as e:
        logger.error(f"Failed to get mtime for {file_path}: {e}")
        return datetime.now().isoformat()


def should_include_file(file_path: Path) -> bool:
    """
    Check if a file should be included in checksum generation.

    Args:
        file_path: Path to the file

    Returns:
        True if file should be included, False otherwise
    """
    # Check if file exists
    if not file_path.exists():
        return False

    # Check if file is a file (not directory)
    if not file_path.is_file():
        return False

    # Check exclusion patterns
    file_str = str(file_path)
    for pattern in EXCLUDE_PATTERNS:
        if pattern in file_str:
            return False

    # Check inclusion patterns
    file_suffix = file_path.suffix.lower()
    for pattern in INCLUDE_PATTERNS:
        if pattern.startswith("*.") and file_suffix == pattern[1:]:
            return True

    return False


def scan_directory_for_files(directory: Path) -> List[Path]:
    """
    Scan a directory for files matching our criteria.

    Args:
        directory: Directory to scan

    Returns:
        List of file paths that should be included
    """
    if not directory.exists():
        logger.warning(f"Directory does not exist: {directory}")
        return []

    files = []
    for file_path in directory.rglob("*"):
        if should_include_file(file_path):
            files.append(file_path)

    return files


def load_state_file(state_path: Path) -> Dict[str, Any]:
    """
    Load the state file.

    Args:
        state_path: Path to the state file

    Returns:
        State dictionary, or empty dict if file doesn't exist
    """
    if not state_path.exists():
        logger.info(f"State file does not exist, creating new one: {state_path}")
        return {
            "project_id": PROJECT_ID,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "artifacts": {}
        }

    try:
        with open(state_path, "r") as f:
            state = yaml.safe_load(f)
            if state is None:
                state = {}
            return state
    except Exception as e:
        logger.error(f"Failed to load state file: {e}")
        return {
            "project_id": PROJECT_ID,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "artifacts": {}
        }


def save_state_file(state_path: Path, state: Dict[str, Any]) -> bool:
    """
    Save the state file.

    Args:
        state_path: Path to the state file
        state: State dictionary to save

    Returns:
        True if save succeeded, False otherwise
    """
    try:
        # Ensure parent directory exists
        state_path.parent.mkdir(parents=True, exist_ok=True)

        with open(state_path, "w") as f:
            yaml.dump(state, f, default_flow_style=False, sort_keys=False)

        logger.info(f"State file saved: {state_path}")
        return True
    except Exception as e:
        logger.error(f"Failed to save state file: {e}")
        return False


def update_artifact_checksum(state: Dict[str, Any], file_path: Path, relative_path: str) -> bool:
    """
    Update the checksum for a single artifact in the state.

    Args:
        state: State dictionary to update
        file_path: Absolute path to the file
        relative_path: Relative path for the artifact key

    Returns:
        True if update succeeded, False otherwise
    """
    checksum = compute_file_checksum_sha256(file_path)
    if checksum is None:
        return False

    size = get_file_size(file_path)
    mtime = get_file_modified_time(file_path)

    if "artifacts" not in state:
        state["artifacts"] = {}

    state["artifacts"][relative_path] = {
        "checksum": checksum,
        "size_bytes": size,
        "modified_at": mtime,
        "updated_at": datetime.now().isoformat()
    }

    logger.info(f"Updated checksum for {relative_path}: {checksum[:16]}...")
    return True


def generate_checksums_for_directory(state: Dict[str, Any], directory: Path, base_path: Path) -> int:
    """
    Generate checksums for all files in a directory.

    Args:
        state: State dictionary to update
        directory: Directory to scan
        base_path: Base path for computing relative paths

    Returns:
        Number of artifacts updated
    """
    files = scan_directory_for_files(directory)
    count = 0

    for file_path in files:
        try:
            relative_path = str(file_path.relative_to(base_path))
            if update_artifact_checksum(state, file_path, relative_path):
                count += 1
        except Exception as e:
            logger.error(f"Failed to process {file_path}: {e}")

    return count


def verify_checksums(state: Dict[str, Any], base_path: Path) -> List[Tuple[str, bool, str]]:
    """
    Verify checksums for all artifacts in the state.

    Args:
        state: State dictionary with artifacts
        base_path: Base path for computing relative paths

    Returns:
        List of (relative_path, passed, message) tuples
    """
    results = []

    if "artifacts" not in state:
        return results

    for relative_path, artifact_info in state["artifacts"].items():
        file_path = base_path / relative_path

        if not file_path.exists():
            results.append((relative_path, False, "File does not exist"))
            continue

        current_checksum = compute_file_checksum_sha256(file_path)
        if current_checksum is None:
            results.append((relative_path, False, "Failed to compute checksum"))
            continue

        expected_checksum = artifact_info.get("checksum", "")
        if current_checksum == expected_checksum:
            results.append((relative_path, True, "Checksum matches"))
        else:
            results.append((relative_path, False, f"Checksum mismatch: expected {expected_checksum[:16]}..., got {current_checksum[:16]}..."))

    return results


def main():
    """Main entry point for the script."""
    logger.info("=" * 60)
    logger.info("Starting state checksum generation")
    logger.info("=" * 60)

    # Get project root
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent

    # State file path
    state_file_path = project_root / STATE_FILE_RELATIVE

    # Load existing state
    state = load_state_file(state_file_path)
    state["project_id"] = PROJECT_ID
    state["updated_at"] = datetime.now().isoformat()

    # Scan all directories and generate checksums
    total_artifacts = 0
    for directory_name in SCAN_DIRECTORIES:
        directory_path = project_root / directory_name
        if directory_path.exists():
            logger.info(f"Scanning directory: {directory_name}")
            count = generate_checksums_for_directory(state, directory_path, project_root)
            total_artifacts += count
            logger.info(f"  Updated {count} artifacts")

    # Update state metadata
    state["last_scan_at"] = datetime.now().isoformat()
    state["total_artifacts"] = total_artifacts

    # Save state file
    if save_state_file(state_file_path, state):
        logger.info("=" * 60)
        logger.info(f"State checksum generation complete")
        logger.info(f"Total artifacts updated: {total_artifacts}")
        logger.info(f"State file: {state_file_path}")
        logger.info("=" * 60)

        # Verify checksums (optional verification)
        logger.info("Verifying checksums...")
        verification_results = verify_checksums(state, project_root)
        passed = sum(1 for _, passed, _ in verification_results if passed)
        failed = len(verification_results) - passed

        logger.info(f"Verification: {passed} passed, {failed} failed")

        if failed > 0:
            logger.warning("Some checksums failed verification:")
            for rel_path, passed, msg in verification_results:
                if not passed:
                    logger.warning(f"  {rel_path}: {msg}")

        return 0
    else:
        logger.error("Failed to save state file")
        return 1


if __name__ == "__main__":
    sys.exit(main())
