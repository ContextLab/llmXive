import hashlib
import logging
import sys
from pathlib import Path

from config import DATA_RAW, setup_logging, EXPECTED_AFLOW_CHECKSUM


def compute_file_checksum(file_path: Path, algorithm: str = "sha256") -> str:
    """Compute the SHA256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except FileNotFoundError:
        raise FileNotFoundError(f"File not found: {file_path}")
    except Exception as e:
        raise RuntimeError(f"Error computing checksum for {file_path}: {e}")


def main():
    """Main entry point for checksum verification."""
    logger = setup_logging()
    logger.info("Starting checksum verification for T017b.")

    data_path = DATA_RAW / "aflow_raw.parquet"

    if not data_path.exists():
        logger.error(f"Raw data file not found at: {data_path}")
        logger.error("T017a (Download Raw Data) must be completed successfully before running this task.")
        sys.exit(1)

    logger.info(f"Computing checksum for: {data_path}")
    try:
        computed_checksum = compute_file_checksum(data_path)
        logger.info(f"Computed checksum: {computed_checksum}")
    except Exception as e:
        logger.error(f"Failed to compute checksum: {e}")
        sys.exit(1)

    logger.info(f"Expected checksum from config: {EXPECTED_AFLOW_CHECKSUM}")

    if EXPECTED_AFLOW_CHECKSUM == "":
        logger.warning("EXPECTED_AFLOW_CHECKSUM is empty in config. Cannot verify integrity.")
        logger.warning("Please update code/config.py with the correct SHA256 hash from the dataset metadata.")
        sys.exit(1)

    if computed_checksum == EXPECTED_AFLOW_CHECKSUM:
        logger.info("SUCCESS: Computed checksum matches expected checksum.")
        logger.info("Data integrity verified.")
        sys.exit(0)
    else:
        logger.error("FAILURE: Computed checksum does NOT match expected checksum.")
        logger.error("Data integrity check failed. The file may be corrupted or from a different source.")
        sys.exit(1)


if __name__ == "__main__":
    main()