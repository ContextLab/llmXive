"""
Task T015: Integrate with versioning utility to hash raw data in data/raw/

This script scans the data/raw/ directory for all downloaded Planck CMB map files,
calculates their SHA256 hashes using the project's versioning utility, and updates
the artifact_hashes.yaml file in the project state directory.
"""
import os
import sys
import logging
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from utils.versioning import calculate_sha256, find_artifacts, get_project_state_path, update_artifact_hashes
from utils.logging_config import get_logger

# Configure logging
logger = get_logger(__name__)

def main():
    """
    Main entry point for T015.
    Scans data/raw/ for artifacts, calculates hashes, and updates the state file.
    """
    logger.info("Starting T015: Integrating versioning utility to hash raw data.")
    
    # Define the raw data directory relative to project root
    raw_data_dir = project_root / "data" / "raw"
    
    if not raw_data_dir.exists():
        logger.error(f"Raw data directory does not exist: {raw_data_dir}")
        logger.info("No raw data to hash. Ensure data download tasks (T012, T014) have completed.")
        return 1

    logger.info(f"Scanning directory: {raw_data_dir}")
    
    # Use the versioning utility to find artifacts in the raw data directory
    # We specifically look for FITS files (.fits, .fits.gz) which are the Planck maps
    artifacts = find_artifacts(raw_data_dir, extensions=[".fits", ".fits.gz"])
    
    if not artifacts:
        logger.warning(f"No artifacts found in {raw_data_dir} with extensions .fits or .fits.gz")
        logger.info("Skipping hash calculation. Ensure data download tasks have completed.")
        return 0

    logger.info(f"Found {len(artifacts)} artifacts to hash:")
    for artifact in artifacts:
        logger.info(f"  - {artifact}")

    # Calculate hashes for each artifact
    hashes = {}
    for artifact_path in artifacts:
        try:
            file_hash = calculate_sha256(artifact_path)
            # Store relative path from project root for consistency
            relative_path = str(artifact_path.relative_to(project_root))
            hashes[relative_path] = file_hash
            logger.info(f"  Hashed {relative_path}: {file_hash[:16]}...")
        except FileNotFoundError:
            logger.error(f"File not found during hashing: {artifact_path}")
        except Exception as e:
            logger.error(f"Error hashing {artifact_path}: {e}")
            return 1

    if not hashes:
        logger.error("No hashes were calculated successfully.")
        return 1

    # Update the artifact_hashes.yaml file
    state_path = get_project_state_path()
    if not state_path:
        logger.error("Could not determine project state path.")
        return 1

    logger.info(f"Updating artifact hashes in: {state_path}")
    
    try:
        success = update_artifact_hashes(state_path, hashes)
        if success:
            logger.info("Successfully updated artifact_hashes.yaml")
            return 0
        else:
            logger.error("Failed to update artifact_hashes.yaml")
            return 1
    except Exception as e:
        logger.error(f"Error updating artifact hashes: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
