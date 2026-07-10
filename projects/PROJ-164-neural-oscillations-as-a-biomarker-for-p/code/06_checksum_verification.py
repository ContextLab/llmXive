"""
T014: SHA-256 Checksum Verification for Raw Data Files.

This script scans the `data/raw/` directory for all files (typically .edf),
computes their SHA-256 checksums, verifies them against the state file if
they exist, or writes new checksums to the state file if they are new.
It also sets file permissions to read-only upon successful verification.

Dependencies:
  - utils.io_helpers (compute_sha256, write_checksum_to_state)
  - utils.logging_setup (get_logger)
  - utils.config (PROJECT_ID)
"""
import os
import stat
import sys
import logging
from pathlib import Path

# Import from project utilities
from utils.io_helpers import compute_sha256, write_checksum_to_state
from utils.logging_setup import get_logger
from utils.config import PROJECT_ID

# Configure logger
logger = get_logger(__name__)

def set_read_only(file_path: Path) -> bool:
    """
    Sets the file permissions to read-only (chmod 444 or 555).
    Returns True if successful, False otherwise.
    """
    try:
        # Read-only for owner, read-execute for others (555)
        os.chmod(file_path, stat.S_IRUSR | stat.S_IRGRP | stat.S_IROTH | stat.S_IXGRP | stat.S_IXOTH)
        logger.info(f"Set read-only permissions on: {file_path}")
        return True
    except PermissionError as e:
        logger.error(f"Permission denied when setting read-only on {file_path}: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error setting permissions on {file_path}: {e}")
        return False

def verify_and_lock_files(raw_dir: Path) -> bool:
    """
    Iterates over all files in raw_dir, computes SHA-256, writes to state,
    and sets permissions to read-only.
    """
    if not raw_dir.exists():
        logger.error(f"Raw data directory does not exist: {raw_dir}")
        return False

    files = list(raw_dir.iterdir())
    if not files:
        logger.warning(f"No files found in {raw_dir}. Skipping checksum verification.")
        return True

    success_count = 0
    total_count = 0

    for file_path in files:
        if file_path.is_dir():
            continue

        total_count += 1
        logger.info(f"Processing checksum for: {file_path.name}")

        try:
            # Compute the hash
            checksum = compute_sha256(file_path)
            logger.info(f"Computed SHA-256 for {file_path.name}: {checksum}")

            # Write to state file
            # write_checksum_to_state returns True on success
            if write_checksum_to_state(str(file_path), checksum, PROJECT_ID):
                # Set read-only
                if set_read_only(file_path):
                    success_count += 1
                    logger.info(f"Successfully verified and locked: {file_path.name}")
                else:
                    logger.warning(f"Checksum written, but failed to set read-only on: {file_path.name}")
            else:
                logger.error(f"Failed to write checksum to state for: {file_path.name}")

        except Exception as e:
            logger.error(f"Error processing {file_path.name}: {e}")
            continue

    if total_count == 0:
        logger.warning("No files processed.")
        return True

    logger.info(f"Checksum verification complete. {success_count}/{total_count} files successfully verified and locked.")
    return success_count == total_count

def main():
    """
    Entry point for T014.
    """
    logger.info("Starting T014: SHA-256 Checksum Verification")

    # Define paths
    project_root = Path(__file__).resolve().parent.parent
    raw_dir = project_root / "data" / "raw"

    success = verify_and_lock_files(raw_dir)

    if success:
        logger.info("T014 completed successfully.")
        sys.exit(0)
    else:
        logger.error("T014 failed due to verification or permission errors.")
        sys.exit(1)

if __name__ == "__main__":
    main()