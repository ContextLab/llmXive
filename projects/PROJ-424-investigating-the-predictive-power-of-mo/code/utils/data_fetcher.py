"""
Data Fetcher Module for PROJ-424.

This module validates the existence of the curated NIST reference data file.
It strictly enforces the Plan's requirement to use the local curated file
(`data/raw/nist_refs.json`) as the canonical source.

It does NOT attempt network fetches. If the file is missing, it raises a
clear, actionable error directing the user to complete task T006b.
"""

import os
import sys
from pathlib import Path
from typing import Optional

# Define the expected path relative to the project root
# Assuming the script is run from the project root or code/ directory,
# we resolve relative to the project root (parent of 'code')
PROJECT_ROOT = Path(__file__).resolve().parent.parent
NIST_REFS_PATH = PROJECT_ROOT / "data" / "raw" / "nist_refs.json"


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


def main() -> None:
    """
    Entry point for command-line validation.
    Prints success message or exits with error code on failure.
    """
    try:
        path = validate_nist_refs_exists()
        print(f"Success: Curated NIST references found at: {path}")
        sys.exit(0)
    except DataValidationError as e:
        print(f"Validation Failed: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()