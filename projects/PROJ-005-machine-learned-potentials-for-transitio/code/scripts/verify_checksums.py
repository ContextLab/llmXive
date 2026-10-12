"""
Script to verify SHA256 checksums of files in ``code/data/raw/`` against the
manifest stored in ``code/data/raw/checksums.json``.

If the manifest does not exist it will be created (empty). If files are
present but not recorded in the manifest, their checksums will be computed
and added. If a recorded checksum does not match the current file, the
script exits with a non‑zero status code.

The script is intended to be run from the repository root (or with the
repository root on ``PYTHONPATH``) as:

    python code/scripts/verify_checksums.py

It uses the utilities defined in ``src/data/checksum_manager.py``.
"""

import sys
import json
import logging
from pathlib import Path

from src.data.checksum_manager import (
    get_project_root,
    compute_file_checksum,
    load_checksum_manifest,
    save_checksum_manifest,
)

# Configure a simple logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def ensure_manifest_exists(manifest_path: Path) -> dict:
    """
    Load the checksum manifest if it exists, otherwise create an empty one.

    Returns the manifest dictionary.
    """
    if not manifest_path.exists():
        logger.info(f"Checksum manifest not found at {manifest_path}. Creating empty manifest.")
        empty_manifest = {}
        save_checksum_manifest(empty_manifest, manifest_path)
        return empty_manifest
    try:
        manifest = load_checksum_manifest(manifest_path)
        if not isinstance(manifest, dict):
            raise ValueError("Manifest content is not a mapping.")
        return manifest
    except Exception as e:
        logger.error(f"Failed to load checksum manifest: {e}")
        logger.info("Re‑initialising manifest to empty.")
        empty_manifest = {}
        save_checksum_manifest(empty_manifest, manifest_path)
        return empty_manifest


def verify_checksums():
    """
    Core verification routine.

    * Ensures the ``data/raw`` directory exists.
    * Loads or creates the checksum manifest.
    * Computes SHA256 checksums for all files in the directory (excluding the manifest itself).
    * Compares computed hashes with the stored values.
    * Updates the manifest with any newly‑discovered files.
    * Exits with status 0 if all existing files match their recorded checksums,
      otherwise exits with status 1.
    """
    project_root = get_project_root()
    raw_dir = project_root / "data" / "raw"
    manifest_path = raw_dir / "checksums.json"

    # Ensure the raw data directory exists
    if not raw_dir.exists():
        logger.warning(f"Raw data directory {raw_dir} does not exist. Creating it.")
        raw_dir.mkdir(parents=True, exist_ok=True)

    # Load (or initialise) the manifest
    manifest = ensure_manifest_exists(manifest_path)

    # Gather all files in the raw directory, ignoring the manifest itself
    raw_files = [
        f for f in raw_dir.iterdir()
        if f.is_file() and f.name != "checksums.json"
    ]

    if not raw_files:
        logger.info("No data files found in data/raw/. Manifest is empty.")
        # Nothing to verify – success.
        sys.exit(0)

    all_valid = True
    manifest_updated = False

    # Verify each file
    for file_path in raw_files:
        # Store the path relative to the project root (consistent with existing utilities)
        rel_path = str(file_path.relative_to(project_root))
        computed_hash = compute_file_checksum(file_path)

        if rel_path not in manifest:
            # New file – add to manifest
            logger.info(f"New file detected: {rel_path}. Adding checksum to manifest.")
            manifest[rel_path] = computed_hash
            manifest_updated = True
            continue  # No need to compare – just recorded.

        expected_hash = manifest[rel_path]
        if expected_hash != computed_hash:
            logger.error(f"Checksum mismatch for {rel_path}:")
            logger.error(f"  Expected: {expected_hash}")
            logger.error(f"  Actual:   {computed_hash}")
            all_valid = False
        else:
            logger.info(f"OK: {rel_path}")

    # Detect entries in the manifest that no longer have a corresponding file
    for recorded_path in list(manifest.keys()):
        full_path = project_root / recorded_path
        if not full_path.exists():
            logger.warning(f"Manifest entry {recorded_path} has no corresponding file on disk.")
            # Optionally, we could remove stale entries; here we just warn.

    # Persist any updates to the manifest
    if manifest_updated:
        logger.info(f"Saving updated checksum manifest to {manifest_path}")
        save_checksum_manifest(manifest, manifest_path)

    if all_valid:
        logger.info("All checksums verified successfully.")
        sys.exit(0)
    else:
        logger.error("One or more checksum mismatches detected.")
        sys.exit(1)


if __name__ == "__main__":
    verify_checksums()