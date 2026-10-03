"""
Dependency Order Verification Script.

This script verifies that the preprocessing step (00_preprocess.py) has
successfully generated the required clean data file and that the data
integrity checksums match before allowing downstream analysis (ANOVA) to run.

It acts as a gatekeeper for Phase 5 (Analysis) execution.
"""

import os
import sys
import json
import argparse
from pathlib import Path
import hashlib

# Add project root to path for imports if running as script
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from utils.helpers import get_project_root, get_submissions_csv_path, get_checksum_store_path
from utils.checksums import compute_sha256, load_checksums, FileChecksumError


def get_cleaned_csv_path():
    """Returns the absolute path to the cleaned data CSV."""
    return PROJECT_ROOT / "data" / "processed" / "clean_data.csv"


def verify_dependencies(args=None):
    """
    Verifies that dependencies for the ANOVA script are met.

    Checks:
    1. Raw submissions file exists.
    2. Clean data file exists.
    3. Checksum file exists.
    4. Clean data file checksum matches the recorded checksum for the raw file
       (indicating the clean data was derived from the current raw data).

    Raises:
        FileNotFoundError: If required files are missing.
        FileChecksumError: If checksums do not match.
        SystemExit: If verification fails.
    """
    if args is None:
        parser = argparse.ArgumentParser(description="Verify analysis dependencies.")
        parser.add_argument("--verbose", action="store_true", help="Print detailed verification steps.")
        args = parser.parse_args()

    project_root = get_project_root()
    submissions_path = get_submissions_csv_path()
    checksum_path = get_checksum_store_path()
    clean_data_path = get_cleaned_csv_path()

    if args.verbose:
        print(f"Project Root: {project_root}")
        print(f"Submissions Path: {submissions_path}")
        print(f"Checksum Path: {checksum_path}")
        print(f"Clean Data Path: {clean_data_path}")

    # 1. Verify Raw Submissions File
    if not submissions_path.exists():
        error_msg = f"CRITICAL: Raw submissions file not found at {submissions_path}. " \
                    "Data collection has not occurred or the file is missing."
        print(error_msg)
        raise FileNotFoundError(error_msg)

    if args.verbose:
        print(f"[OK] Raw submissions file found: {submissions_path}")

    # 2. Verify Checksum Store
    if not checksum_path.exists():
        error_msg = f"CRITICAL: Checksum store not found at {checksum_path}. " \
                    "Data integrity cannot be verified. Run preprocessing or backup creation first."
        print(error_msg)
        raise FileNotFoundError(error_msg)

    if args.verbose:
        print(f"[OK] Checksum store found: {checksum_path}")

    # 3. Verify Clean Data File
    if not clean_data_path.exists():
        error_msg = f"CRITICAL: Clean data file not found at {clean_data_path}. " \
                    "Preprocessing (00_preprocess.py) has not been run successfully. " \
                    "ANOVA cannot proceed without clean data."
        print(error_msg)
        raise FileNotFoundError(error_msg)

    if args.verbose:
        print(f"[OK] Clean data file found: {clean_data_path}")

    # 4. Verify Checksum Consistency
    # Load recorded checksums
    try:
        recorded_checksums = load_checksums(checksum_path)
    except json.JSONDecodeError as e:
        error_msg = f"CRITICAL: Checksum store at {checksum_path} is corrupted (invalid JSON). {e}"
        print(error_msg)
        raise RuntimeError(error_msg)

    # We need to verify that the clean_data.csv was generated from the CURRENT submissions.csv.
    # The checksum store typically holds the hash of the raw file at the time of backup/preprocessing.
    # We compute the current hash of the raw file and compare it to the stored hash.
    current_submissions_hash = compute_sha256(submissions_path)

    stored_submissions_hash = recorded_checksums.get("submissions.csv")

    if stored_submissions_hash is None:
        error_msg = f"CRITICAL: No checksum recorded for 'submissions.csv' in {checksum_path}. " \
                    "Cannot verify data freshness."
        print(error_msg)
        raise FileChecksumError(error_msg)

    if current_submissions_hash != stored_submissions_hash:
        error_msg = (
            f"CRITICAL: Data Staleness Detected.\n"
            f"  The raw data file '{submissions_path}' has changed since the last preprocessing run.\n"
            f"  Current Hash:  {current_submissions_hash}\n"
            f"  Stored Hash:   {stored_submissions_hash}\n"
            f"  The clean data '{clean_data_path}' is STALE.\n"
            f"  ACTION: Re-run preprocessing (code/analysis/00_preprocess.py) to update clean_data.csv."
        )
        print(error_msg)
        raise FileChecksumError(error_msg)

    if args.verbose:
        print(f"[OK] Checksum verified. Data is fresh.")
        print(f"     Current Hash: {current_submissions_hash}")

    print("SUCCESS: All dependencies verified. Ready to run analysis.")
    return True


def main():
    """Main entry point for the script."""
    try:
        verify_dependencies()
        sys.exit(0)
    except (FileNotFoundError, FileChecksumError, RuntimeError) as e:
        print(f"DEPENDENCY CHECK FAILED: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"UNEXPECTED ERROR: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()