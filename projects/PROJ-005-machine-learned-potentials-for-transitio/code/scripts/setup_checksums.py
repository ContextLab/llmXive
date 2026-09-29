"""
Script to initialize the data/raw directory and setup checksum verification.
This script ensures the directory structure exists and generates the initial
checksum manifest for any files present in data/raw.
"""
import json
import logging
import sys
from pathlib import Path

# Add project root to path to allow imports
current_dir = Path(__file__).resolve().parent
project_root = current_dir.parent
sys.path.insert(0, str(project_root))

from src.data.checksum_manager import get_project_root, compute_file_checksum, save_checksum_manifest

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def main():
    """
    Main entry point for setup_checksums.
    1. Ensures code/data/raw/ directory exists.
    2. Scans for existing files and generates .checksums.json manifest.
    """
    root = get_project_root()
    raw_dir = root / "data" / "raw"
    manifest_path = raw_dir / ".checksums.json"

    # 1. Ensure directory exists
    if not raw_dir.exists():
        logger.info(f"Creating directory: {raw_dir}")
        raw_dir.mkdir(parents=True, exist_ok=True)
    else:
        logger.info(f"Directory exists: {raw_dir}")

    # 2. Initialize or update manifest
    logger.info("Scanning data/raw for files to generate checksum manifest...")
    files = {}
    found_files = False

    for file_path in raw_dir.rglob("*"):
        if file_path.is_file() and not file_path.name.startswith("."):
            found_files = True
            rel_path = str(file_path.relative_to(root))
            try:
                checksum = compute_file_checksum(file_path)
                files[rel_path] = {
                    "checksum": checksum,
                    "algorithm": "sha256",
                    "size_bytes": file_path.stat().st_size
                }
                logger.info(f"  Checked: {rel_path} -> {checksum[:16]}...")
            except Exception as e:
                logger.error(f"Failed to compute checksum for {file_path}: {e}")

    if found_files:
        manifest = {
            "files": files,
            "metadata": {
                "created": "setup_checksums.py",
                "version": "1.0"
            }
        }
        save_checksum_manifest(manifest_path, manifest)
        logger.info(f"Checksum manifest created/updated at: {manifest_path}")
    else:
        # Create empty manifest if no files found
        manifest = {
            "files": {},
            "metadata": {
                "created": "setup_checksums.py",
                "version": "1.0",
                "note": "No files found in data/raw"
            }
        }
        save_checksum_manifest(manifest_path, manifest)
        logger.info(f"Empty checksum manifest created at: {manifest_path}")

    logger.info("Setup checksums completed successfully.")

if __name__ == "__main__":
    main()