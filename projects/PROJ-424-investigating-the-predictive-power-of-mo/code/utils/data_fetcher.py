"""
Data Fetcher Module for PROJ-424.

This module validates the existence and checksum of the curated NIST reference data file.
It strictly enforces the Plan's requirement to use the local curated file
(`data/raw/nist_refs.json`) as the canonical source.

It does NOT attempt network fetches. If the file is missing or checksum mismatch,
it raises a clear, actionable error directing the user to complete task T006b.
"""

import os
import sys
from pathlib import Path
from typing import Optional

# Import the checksum utility from sibling module (T007b)
from utils.checksums import calculate_sha256

# Define the expected path relative to the project root
# Assuming the script is run from the project root or code/ directory,
# we resolve relative to the project root (parent of 'code')
PROJECT_ROOT = Path(__file__).resolve().parent.parent
NIST_REFS_PATH = PROJECT_ROOT / "data" / "raw" / "nist_refs.json"
MANIFEST_PATH = PROJECT_ROOT / "data" / "raw" / "manifest.json"


class DataValidationError(RuntimeError):
    """Custom exception for data validation failures."""
    pass


def validate_nist_refs_exists() -> Optional[Path]:
    """
    Validates the existence of the curated NIST references file.

    Returns:
        Path: The absolute path to the file if it exists.

    Raises:
        DataValidationError: If the file is missing, with instructions to run T006b.
    """
    if not NIST_REFS_PATH.exists():
        error_msg = (
            f"Critical Error: Curated NIST reference file not found at {NIST_REFS_PATH}.\n"
            "This file is required to proceed with the analysis.\n\n"
            "Action Required:\n"
            "Please complete task T006b to generate or manually populate "
            "'data/raw/nist_refs.json' with the curated experimental diffusion "
            "coefficients for water, ethanol, and acetone.\n\n"
            "Do not attempt to run the pipeline without this file."
        )
        raise DataValidationError(error_msg)

    return NIST_REFS_PATH


def validate_nist_refs_checksum() -> bool:
    """
    Validates the SHA256 checksum of the NIST references file against the manifest.

    Returns:
        bool: True if checksum matches.

    Raises:
        DataValidationError: If checksum mismatch or manifest missing.
    """
    if not MANIFEST_PATH.exists():
        error_msg = (
            f"Critical Error: Checksum manifest not found at {MANIFEST_PATH}.\n"
            "This file is required to verify data integrity.\n\n"
            "Action Required:\n"
            "Please ensure task T006b has completed successfully and generated "
            "the manifest file with the correct checksum."
        )
        raise DataValidationError(error_msg)

    import json

    try:
        with open(MANIFEST_PATH, 'r') as f:
            manifest = json.load(f)
    except json.JSONDecodeError as e:
        raise DataValidationError(f"Critical Error: Manifest file {MANIFEST_PATH} is not valid JSON. {e}")

    expected_checksum = manifest.get("nist_refs_sha256")
    if not expected_checksum:
        raise DataValidationError(
            f"Critical Error: 'nist_refs_sha256' key missing in {MANIFEST_PATH}."
        )

    actual_checksum = calculate_sha256(NIST_REFS_PATH)

    if actual_checksum != expected_checksum:
        error_msg = (
            f"Critical Error: Checksum mismatch for {NIST_REFS_PATH}.\n"
            f"Expected: {expected_checksum}\n"
            f"Actual:   {actual_checksum}\n\n"
            "Action Required:\n"
            "The data file has been modified or corrupted since T006b ran.\n"
            "Please re-run task T006b to regenerate the file and manifest, "
            "or restore the original file if you have a backup."
        )
        raise DataValidationError(error_msg)

    return True


def validate_nist_refs() -> Path:
    """
    Full validation: existence and checksum.

    Returns:
        Path: The absolute path to the file if valid.

    Raises:
        DataValidationError: If any validation step fails.
    """
    # 1. Check existence
    path = validate_nist_refs_exists()

    # 2. Check checksum
    validate_nist_refs_checksum()

    return path


def main() -> None:
    """
    Entry point for command-line validation.
    Prints success message or exits with error code on failure.
    """
    try:
        path = validate_nist_refs()
        print(f"Success: Curated NIST references validated at: {path}")
        sys.exit(0)
    except DataValidationError as e:
        print(f"Validation Failed: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()