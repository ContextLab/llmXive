import json
import logging
import sys
from pathlib import Path

from config import get_data_dir, get_raw_data_dir
from logging_config import setup_logging, get_logger
from code_05_compute_checksums import compute_sha256

def verify_checksums(checksums_path: Path, logger: logging.Logger) -> bool:
    """Verify all checksums in the JSON file match their corresponding files."""
    if not checksums_path.exists():
        logger.error(f"Checksums file not found: {checksums_path}")
        return False

    with open(checksums_path, "r") as f:
        checksums = json.load(f)

    if not checksums:
        logger.warning("Checksums file is empty")
        return True

    all_valid = True
    for relative_path, expected_checksum in checksums.items():
        file_path = Path(relative_path)
        if not file_path.exists():
            logger.error(f"File not found for checksum: {relative_path}")
            all_valid = False
            continue

        try:
            actual_checksum = compute_sha256(file_path)
            if actual_checksum == expected_checksum:
                logger.info(f"Checksum valid for {relative_path}")
            else:
                logger.error(f"Checksum mismatch for {relative_path}")
                logger.error(f"  Expected: {expected_checksum}")
                logger.error(f"  Actual:   {actual_checksum}")
                all_valid = False
        except Exception as e:
            logger.error(f"Error computing checksum for {relative_path}: {e}")
            all_valid = False

    return all_valid

def main() -> int:
    """Main entry point for verifying checksums."""
    logger = setup_logging()
    logger.info("Starting checksum verification")

    checksums_path = get_data_dir() / "checksums.json"
    is_valid = verify_checksums(checksums_path, logger)

    if is_valid:
        logger.info("All checksums verified successfully")
        print("All checksums verified successfully")
        return 0
    else:
        logger.error("Checksum verification failed")
        print("Checksum verification failed", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())