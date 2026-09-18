import os
import sys
from pathlib import Path
from typing import Optional
from utils.checksums import calculate_sha256
from config import NIST_REFS_PATH, MANIFEST_PATH
import json
import logging

logger = logging.getLogger(__name__)

class DataValidationError(Exception):
    """Raised when data validation fails."""
    pass

def validate_nist_refs_exists() -> bool:
    """Check if the NIST refs file exists."""
    path = Path(NIST_REFS_PATH)
    if not path.exists():
        raise DataValidationError(
            f"NIST references file not found at {NIST_REFS_PATH}. "
            "Please run `python code/data/raw/generate_nist_refs.py` first (Task T006b)."
        )
    return True

def validate_nist_refs_checksum() -> bool:
    """Validate the checksum of nist_refs.json against manifest.json."""
    nist_path = Path(NIST_REFS_PATH)
    manifest_path = Path(MANIFEST_PATH)

    if not manifest_path.exists():
        logger.warning("Manifest file not found. Skipping checksum validation.")
        return True

    try:
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)
        
        expected_hash = manifest.get("sha256")
        if not expected_hash:
            raise DataValidationError("Manifest exists but contains no SHA256 hash.")

        actual_hash = calculate_sha256(str(nist_path))

        if actual_hash != expected_hash:
            raise DataValidationError(
                f"Checksum mismatch for {NIST_REFS_PATH}. "
                f"Expected: {expected_hash}, Got: {actual_hash}. "
                "Data may be corrupted or modified. Re-run generation script."
            )
        return True
    except json.JSONDecodeError:
        raise DataValidationError("Manifest file is not valid JSON.")

def validate_nist_refs() -> bool:
    """Run all validations for NIST references."""
    validate_nist_refs_exists()
    validate_nist_refs_checksum()
    logger.info("NIST references validated successfully.")
    return True

def main():
    """CLI entry point for validation."""
    try:
        validate_nist_refs()
        print("Validation successful.")
    except DataValidationError as e:
        print(f"Validation failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
