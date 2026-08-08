import logging
import sys
from pathlib import Path
from typing import Optional
from src.data.archive_utils import archive_data, generate_checksum_manifest
from src.config import setup_logging

def run_archive_pipeline(
    source_dirs: list[str],
    archive_root: str = "data/raw/archive",
    checksum_manifest: str = "data/provenance/checksums.json",
) -> None:
    """
    Orchestrates the archiving of downloaded files and generation of checksums.

    Args:
        source_dirs: List of relative paths to directories containing downloaded data.
        archive_root: Destination directory for the archived data.
        checksum_manifest: Path where the checksum manifest JSON will be written.
    """
    logger = setup_logging()
    logger.info("Starting archive pipeline.")

    archive_path = Path(archive_root)
    manifest_path = Path(checksum_manifest)

    # Ensure archive directory exists
    archive_path.mkdir(parents=True, exist_ok=True)
    logger.info(f"Archive directory ensured at: {archive_path}")

    total_files = 0
    for source_dir in source_dirs:
        src_path = Path(source_dir)
        if not src_path.exists():
            logger.warning(f"Source directory does not exist, skipping: {src_path}")
            continue

        count = archive_data(src_path, archive_path)
        total_files += count
        logger.info(f"Archived {count} files from {src_path} to {archive_path}")

    if total_files == 0:
        logger.warning("No files were archived. Check source directories.")
    else:
        logger.info(f"Total files archived: {total_files}")
        logger.info("Generating checksum manifest...")
        generate_checksum_manifest(archive_path, manifest_path)
        logger.info(f"Checksum manifest written to: {manifest_path}")

    logger.info("Archive pipeline completed.")

def main() -> None:
    """Entry point for the archive pipeline script."""
    logger = setup_logging()
    try:
        # Define source directories based on previous tasks (T005b, T005c2)
        # These correspond to the eBird sample and Daymet climate data locations.
        source_dirs = [
            "data/raw/ebird_sample",  # Expected location from T005b
            "data/raw/climate",       # Expected location from T005c2
        ]

        run_archive_pipeline(
            source_dirs=source_dirs,
            archive_root="data/raw/archive",
            checksum_manifest="data/provenance/checksums.json",
        )
    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
