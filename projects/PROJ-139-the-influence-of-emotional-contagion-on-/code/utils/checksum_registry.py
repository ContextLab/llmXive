"""
Checksum Registry for llmXive Project PROJ-139.

This module records artifact checksums in a state YAML file to ensure
reproducibility and integrity tracking of the research pipeline outputs.
"""

import hashlib
import os
import logging
import yaml
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Project specific constants
PROJECT_ID = "PROJ-139-the-influence-of-emotional-contagion-on-"
STATE_DIR = Path("state/projects")
CHECKSUM_FILE_NAME = f"{PROJECT_ID}.yaml"
CHECKSUM_FILE_PATH = STATE_DIR / CHECKSUM_FILE_NAME

# Directories to scan for artifacts
ARTIFACT_DIRS = [
    Path("data/processed"),
    Path("data/raw"),
    Path("code"),
    Path("state"),
    Path("docs"),
    Path("figures")
]

# File extensions to include
INCLUDE_EXTENSIONS = {'.csv', '.json', '.yaml', '.yml', '.py', '.md', '.png', '.txt', '.log'}


def compute_file_hash(file_path: Path) -> str:
    """
    Compute SHA-256 hash of a file.

    Args:
        file_path: Path to the file.

    Returns:
        Hexadecimal string of the SHA-256 hash.
    """
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except Exception as e:
        logger.error(f"Error computing hash for {file_path}: {e}")
        raise


def find_artifacts(base_dirs: List[Path], extensions: Optional[set] = None) -> List[Path]:
    """
    Recursively find all files with specified extensions in given directories.

    Args:
        base_dirs: List of base directories to scan.
        extensions: Set of extensions to include (default: INCLUDE_EXTENSIONS).

    Returns:
        List of Path objects for matching files.
    """
    if extensions is None:
        extensions = INCLUDE_EXTENSIONS

    artifacts = []
    for base_dir in base_dirs:
        if not base_dir.exists():
            logger.warning(f"Directory not found, skipping: {base_dir}")
            continue

        for file_path in base_dir.rglob("*"):
            if file_path.is_file() and file_path.suffix.lower() in extensions:
                # Exclude temporary files or caches if necessary
                if "__pycache__" not in str(file_path) and file_path.suffix != '.pyc':
                    artifacts.append(file_path)

    return sorted(artifacts)


def load_previous_checksums(file_path: Path) -> Dict[str, Any]:
    """
    Load previous checksums from the state file if it exists.

    Args:
        file_path: Path to the YAML checksum file.

    Returns:
        Dictionary containing previous checksum data or empty structure.
    """
    if not file_path.exists():
        return {
            "project_id": PROJECT_ID,
            "last_updated": None,
            "artifact_hashes": {}
        }

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
            if data is None:
                return {
                    "project_id": PROJECT_ID,
                    "last_updated": None,
                    "artifact_hashes": {}
                }
            return data
    except Exception as e:
        logger.error(f"Error loading previous checksums from {file_path}: {e}")
        # Return empty structure if load fails to allow regeneration
        return {
            "project_id": PROJECT_ID,
            "last_updated": None,
            "artifact_hashes": {}
        }


def record_checksums(
    artifacts: List[Path],
    output_path: Path,
    previous_data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Compute hashes for artifacts and record them in the state file.

    Args:
        artifacts: List of file paths to hash.
        output_path: Path to the output YAML file.
        previous_data: Optional previous data to merge with (preserves metadata).

    Returns:
        The updated data dictionary.
    """
    current_hashes = {}
    for artifact in artifacts:
        try:
            # Use relative path from project root for cleaner storage
            rel_path = str(artifact.relative_to(Path.cwd()))
            file_hash = compute_file_hash(artifact)
            current_hashes[rel_path] = file_hash
            logger.info(f"Hashed: {rel_path}")
        except Exception as e:
            logger.error(f"Failed to hash {artifact}: {e}")
            continue

    # Prepare final data structure
    final_data = {
        "project_id": PROJECT_ID,
        "last_updated": datetime.now().isoformat(),
        "artifact_hashes": current_hashes
    }

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write to file
    with open(output_path, "w", encoding="utf-8") as f:
        yaml.dump(final_data, f, default_flow_style=False, sort_keys=False)

    logger.info(f"Checksums recorded in {output_path}")
    return final_data


def main():
    """
    Main entry point to record artifact checksums.
    """
    logger.info(f"Starting checksum registry for project {PROJECT_ID}")

    # Ensure state directory exists
    STATE_DIR.mkdir(parents=True, exist_ok=True)

    # Find all relevant artifacts
    artifacts = find_artifacts(ARTIFACT_DIRS)
    logger.info(f"Found {len(artifacts)} artifacts to hash.")

    if not artifacts:
        logger.warning("No artifacts found to hash. Check artifact directories.")
        # Still create the file to indicate a run occurred
        record_checksums([], CHECKSUM_FILE_PATH)
        return

    # Load previous data if needed (optional, for merging metadata)
    previous_data = load_previous_checksums(CHECKSUM_FILE_PATH)

    # Record new checksums
    record_checksums(artifacts, CHECKSUM_FILE_PATH, previous_data)

    logger.info("Checksum registration completed successfully.")


if __name__ == "__main__":
    main()
