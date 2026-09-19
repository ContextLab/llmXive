#!/usr/bin/env python
"""
Verify existence and checksums of pre-fetched raw datasets (ImageNet-1K, LAION-400M).
Does not download data. Fails loudly if files are missing or checksums mismatch.
"""
import argparse
import json
import hashlib
import sys
from pathlib import Path
import logging

from utils.config import get_config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def calculate_sha256(file_path: Path) -> str:
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def validate_checksums(data_dir: Path, checksums_file: Path) -> bool:
    if not checksums_file.exists():
        logger.error(f"Checksums file not found: {checksums_file}")
        return False

    with open(checksums_file, "r") as f:
        expected_checksums = json.load(f)

    all_valid = True
    for filename, expected_hash in expected_checksums.items():
        file_path = data_dir / filename
        if not file_path.exists():
            logger.error(f"Missing file: {file_path}")
            all_valid = False
            continue

        actual_hash = calculate_sha256(file_path)
        if actual_hash != expected_hash:
            logger.error(f"Checksum mismatch for {filename}: expected {expected_hash}, got {actual_hash}")
            all_valid = False
        else:
            logger.info(f"Verified {filename}: {actual_hash}")

    return all_valid

def main():
    config = get_config()
    data_dir = Path(config.get_path("RAW_DATA_DIR"))
    checksums_file = data_dir / "checksums.json"
    validation_report = Path(config.get_path("RESULTS_DIR")) / "data_fetch_validation.json"

    # Ensure report directory exists
    validation_report.parent.mkdir(parents=True, exist_ok=True)

    is_valid = validate_checksums(data_dir, checksums_file)
    status = "verified" if is_valid else "failed"

    report = {
        "status": status,
        "data_dir": str(data_dir),
        "checksums_file": str(checksums_file),
        "timestamp": "2023-10-27T00:00:00Z"  # Placeholder for real timestamp
    }

    with open(validation_report, "w") as f:
        json.dump(report, f, indent=2)

    logger.info(f"Validation report written to {validation_report}")

    if not is_valid:
        logger.error("Data verification failed. Exiting with code 1.")
        sys.exit(1)

    logger.info("Data verification successful.")
    sys.exit(0)

if __name__ == "__main__":
    main()
