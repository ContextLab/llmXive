"""
Archive Pipeline for Bird Migration Data.

This module handles the archiving of raw data (eBird and Climate) for CI provenance.
It copies files from the raw data directories to an archive directory and generates
a manifest for integrity verification.
"""
import logging
import sys
import shutil
import json
from pathlib import Path
from typing import Optional, Dict, Any, List

from src.data.archive_utils import compute_sha256, archive_data, verify_archive_integrity, generate_checksum_manifest
from src.config import setup_logging

# Configure logging
logger = setup_logging("archive_pipeline")

# Define paths relative to project root
PROJECT_ROOT = Path(__file__).resolve().parents[2]
RAW_EBIRD_DIR = PROJECT_ROOT / "data" / "raw" / "ebird_sample"
RAW_NOAA_DIR = PROJECT_ROOT / "data" / "raw" / "noaa_prism"
RAW_DAYMET_DIR = PROJECT_ROOT / "data" / "raw" / "daymet"
ARCHIVE_DIR = PROJECT_ROOT / "data" / "raw" / "archive"
MANIFEST_PATH = ARCHIVE_DIR / "archive_manifest.json"

def determine_active_climate_source() -> Optional[Path]:
    """
    Determines which climate data source was successfully downloaded.
    Prioritizes NOAA/PRISM, falls back to Daymet if NOAA is missing.
    Returns the path to the active climate directory or None if neither exists.
    """
    if RAW_NOAA_DIR.exists() and any(RAW_NOAA_DIR.iterdir()):
        logger.info(f"Active climate source found: {RAW_NOAA_DIR}")
        return RAW_NOAA_DIR
    elif RAW_DAYMET_DIR.exists() and any(RAW_DAYMET_DIR.iterdir()):
        logger.warning(f"NOAA/PRISM not found. Using fallback: {RAW_DAYMET_DIR}")
        return RAW_DAYMET_DIR
    else:
        logger.error("No climate data source found (neither NOAA nor Daymet).")
        return None

def run_archive_pipeline() -> Dict[str, Any]:
    """
    Executes the full archiving process:
    1. Ensures archive directory exists.
    2. Archives eBird sample.
    3. Archives active climate source (NOAA or Daymet).
    4. Generates checksum manifest.
    5. Verifies archive integrity.

    Returns:
        Dict containing status and paths.
    """
    logger.info("Starting archive pipeline...")
    
    # Ensure archive directory exists
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)
    logger.info(f"Archive directory ready: {ARCHIVE_DIR}")

    # Archive eBird data
    if RAW_EBIRD_DIR.exists() and any(RAW_EBIRD_DIR.iterdir()):
        ebird_archive_path = ARCHIVE_DIR / "ebird_sample"
        logger.info(f"Archiving eBird data to {ebird_archive_path}...")
        archive_data(RAW_EBIRD_DIR, ebird_archive_path)
    else:
        raise FileNotFoundError(f"eBird sample directory not found: {RAW_EBIRD_DIR}")

    # Archive climate data
    climate_source = determine_active_climate_source()
    if climate_source:
        climate_name = climate_source.name
        climate_archive_path = ARCHIVE_DIR / climate_name
        logger.info(f"Archiving climate data ({climate_name}) to {climate_archive_path}...")
        archive_data(climate_source, climate_archive_path)
    else:
        raise RuntimeError("Failed to archive climate data: no valid source found.")

    # Generate checksum manifest
    logger.info("Generating checksum manifest...")
    manifest = generate_checksum_manifest(ARCHIVE_DIR)
    with open(MANIFEST_PATH, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2)
    logger.info(f"Manifest written to {MANIFEST_PATH}")

    # Verify integrity
    logger.info("Verifying archive integrity...")
    is_valid = verify_archive_integrity(ARCHIVE_DIR, manifest)
    
    if not is_valid:
        raise RuntimeError("Archive integrity verification failed.")

    logger.info("Archive pipeline completed successfully.")
    
    return {
        "status": "success",
        "archive_path": str(ARCHIVE_DIR),
        "manifest_path": str(MANIFEST_PATH),
        "files_archived": len(manifest.get("files", []))
    }

def main():
    """Entry point for the archive pipeline."""
    try:
        result = run_archive_pipeline()
        print(json.dumps(result, indent=2))
        sys.exit(0)
    except Exception as e:
        logger.exception("Pipeline failed with error")
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
