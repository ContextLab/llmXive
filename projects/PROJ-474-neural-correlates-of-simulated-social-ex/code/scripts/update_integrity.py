"""
Script to update integrity hashes for all files in data directories.
This is a utility script that can be run manually or as part of a CI/CD process.
"""
import sys
from pathlib import Path

# Add project root to path if not already there
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.integrity import update_hashes, get_logger, IntegrityError, scan_data_directory


def main():
    logger = get_logger("update_integrity")
    logger.info("Starting integrity hash update...")

    # Define data directories to scan
    data_dirs = {
        "raw": project_root / "data" / "raw",
        "processed": project_root / "data" / "processed",
        "results": project_root / "data" / "results"
    }

    files_to_hash = {}

    for prefix, directory in data_dirs.items():
        if directory.exists():
            logger.info(f"Scanning {prefix} directory: {directory}")
            files = scan_data_directory(directory, relative_prefix=prefix)
            files_to_hash.update(files)
        else:
            logger.warning(f"Directory not found, skipping: {directory}")

    if not files_to_hash:
        logger.warning("No files found to hash.")
        return

    logger.info(f"Found {len(files_to_hash)} files to hash.")

    try:
        update_hashes(files_to_hash)
        logger.info("Integrity hashes updated successfully.")
    except IntegrityError as e:
        logger.error(f"Failed to update hashes: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()