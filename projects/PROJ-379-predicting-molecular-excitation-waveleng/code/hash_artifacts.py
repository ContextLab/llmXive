"""
Artifact Hashing Utility for llmXive Pipeline.

Computes SHA-256 hashes for all data and code artifacts and updates
the project state YAML file.
"""

import hashlib
import os
import yaml
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

# Import shared utilities from the project
from utils import get_logger

logger = get_logger(__name__)

# Project specific constants
PROJECT_ID = "PROJ-379-predicting-molecular-excitation-waveleng"
PROJECT_ROOT = Path(__file__).resolve().parent.parent
STATE_DIR = PROJECT_ROOT / "state" / "projects"
STATE_FILE = STATE_DIR / f"{PROJECT_ID}.yaml"

# Directories to hash
TARGET_DIRS = [
    PROJECT_ROOT / "code",
    PROJECT_ROOT / "data",
    PROJECT_ROOT / "tests",
    PROJECT_ROOT / "specs",
]

# File extensions to include
INCLUDE_EXTENSIONS = {".py", ".yaml", ".yml", ".json", ".csv", ".txt", ".md", ".png", ".pt"}
EXCLUDE_DIRS = {".git", "__pycache__", "node_modules", ".venv", "venv"}


def compute_file_hash(file_path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except (IOError, OSError) as e:
        logger.warning(f"Could not read file {file_path} for hashing: {e}")
        return ""


def collect_artifacts() -> Dict[str, str]:
    """
    Recursively find all relevant files in target directories
    and compute their relative paths and hashes.
    """
    artifacts = {}
    
    for target_dir in TARGET_DIRS:
        if not target_dir.exists():
            logger.info(f"Target directory does not exist, skipping: {target_dir}")
            continue

        logger.info(f"Scanning directory: {target_dir}")
        
        for file_path in target_dir.rglob("*"):
            if not file_path.is_file():
                continue
            
            # Check extension
            if file_path.suffix not in INCLUDE_EXTENSIONS:
                continue
            
            # Check excluded directories
            if any(excluded in file_path.parts for excluded in EXCLUDE_DIRS):
                continue

            # Compute relative path from project root
            try:
                rel_path = file_path.relative_to(PROJECT_ROOT)
                file_hash = compute_file_hash(file_path)
                if file_hash:
                    artifacts[str(rel_path)] = file_hash
            except ValueError:
                # File is outside project root (shouldn't happen with rglob)
                continue

    return artifacts


def update_state_file(artifact_hashes: Dict[str, str]) -> None:
    """
    Update the project state YAML file with new artifact hashes.
    Creates the file and directory structure if they don't exist.
    """
    # Ensure state directory exists
    STATE_DIR.mkdir(parents=True, exist_ok=True)

    # Load existing state or create new
    existing_state: Dict[str, Any] = {}
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                existing_state = yaml.safe_load(f) or {}
        except yaml.YAMLError as e:
            logger.warning(f"Could not parse existing state file: {e}. Starting fresh.")
        except IOError as e:
            logger.warning(f"Could not read existing state file: {e}. Starting fresh.")

    # Update state
    existing_state["artifact_hashes"] = artifact_hashes
    existing_state["updated_at"] = datetime.utcnow().isoformat() + "Z"

    # Ensure project ID is in the state
    existing_state["project_id"] = PROJECT_ID

    # Write back to file
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        yaml.dump(existing_state, f, default_flow_style=False, sort_keys=False)

    logger.info(f"State file updated: {STATE_FILE}")


def main() -> int:
    """
    Main entry point for the hashing script.
    Returns 0 on success, 1 on failure.
    """
    logger.info(f"Starting artifact hashing for project: {PROJECT_ID}")
    logger.info(f"Project root: {PROJECT_ROOT}")

    try:
        artifacts = collect_artifacts()
        logger.info(f"Found {len(artifacts)} artifacts to hash.")

        if not artifacts:
            logger.warning("No artifacts found to hash. State file will be updated with empty hashes.")

        update_state_file(artifacts)
        logger.info("Artifact hashing completed successfully.")
        return 0

    except Exception as e:
        logger.error(f"Artifact hashing failed: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
