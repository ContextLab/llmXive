"""
Verify the integrity of the downloaded Guava dataset using checksums.

This script validates the integrity of files in `data/raw/guava/` against
the checksums recorded in `data/raw/guava/checksums.json`.

It is a critical step in the data pipeline to ensure data consistency
before proceeding with transformation or analysis.
"""

import json
import hashlib
import os
import sys
from pathlib import Path
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.exceptions import DatasetUnavailableError
from utils.config import get_path


def calculate_sha256(file_path: Path) -> str:
    """
    Calculate the SHA256 hash of a file.

    Args:
        file_path: Path to the file to hash.

    Returns:
        Hexadecimal string of the SHA256 hash.
    """
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except FileNotFoundError:
        raise DatasetUnavailableError(f"File not found for hashing: {file_path}")
    except PermissionError:
        raise DatasetUnavailableError(f"Permission denied reading file: {file_path}")


def verify_integrity() -> dict:
    """
    Verify the integrity of the Guava dataset against stored checksums.

    This function:
    1. Loads `checksums.json` from `data/raw/guava/`.
    2. Iterates through all expected files.
    3. Computes the SHA256 hash of each file on disk.
    4. Compares computed hashes with stored hashes.
    5. Logs the result to `data/artifacts/integrity_check_{timestamp}.json`.

    Returns:
        A dictionary containing the verification results.

    Raises:
        DatasetUnavailableError: If checksums.json is missing or if the
        dataset directory itself is missing.
        ValueError: If the checksum file is malformed.
    """
    checksums_path = get_path("raw_guava_checksums")
    guava_dir = get_path("raw_guava")
    artifact_dir = get_path("artifacts")

    # Ensure directories exist
    if not guava_dir.exists():
        raise DatasetUnavailableError(
            f"Guava dataset directory does not exist: {guava_dir}. "
            "Run download_guava.py first."
        )

    if not checksums_path.exists():
        raise DatasetUnavailableError(
            f"Checksum file not found: {checksums_path}. "
            "Run download_guava.py to generate checksums."
        )

    # Load expected checksums
    try:
        with open(checksums_path, "r", encoding="utf-8") as f:
            expected_checksums = json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"Malformed JSON in checksums file: {e}")

    results = {
        "timestamp": datetime.now().isoformat(),
        "dataset_directory": str(guava_dir),
        "checksum_file": str(checksums_path),
        "total_files": 0,
        "verified_files": 0,
        "failed_files": 0,
        "missing_files": 0,
        "status": "PASSED",
        "details": []
    }

    # Verify each file
    for file_name, expected_hash in expected_checksums.items():
        results["total_files"] += 1
        file_path = guava_dir / file_name

        if not file_path.exists():
            results["missing_files"] += 1
            results["status"] = "FAILED"
            results["details"].append({
                "file": file_name,
                "status": "MISSING",
                "error": "File not found on disk"
            })
            continue

        try:
            computed_hash = calculate_sha256(file_path)
        except DatasetUnavailableError as e:
            results["failed_files"] += 1
            results["status"] = "FAILED"
            results["details"].append({
                "file": file_name,
                "status": "HASH_ERROR",
                "error": str(e)
            })
            continue

        if computed_hash == expected_hash:
            results["verified_files"] += 1
            results["details"].append({
                "file": file_name,
                "status": "VERIFIED",
                "hash": computed_hash
            })
        else:
            results["failed_files"] += 1
            results["status"] = "FAILED"
            results["details"].append({
                "file": file_name,
                "status": "MISMATCH",
                "expected": expected_hash,
                "computed": computed_hash
            })

    # Write log to artifacts
    log_filename = f"integrity_check_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    log_path = artifact_dir / log_filename

    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    return results


def main():
    """Main entry point for the integrity verification script."""
    print("Starting Guava Dataset Integrity Verification...")
    try:
        results = verify_integrity()
        
        print(f"\nVerification Complete:")
        print(f"  Status: {results['status']}")
        print(f"  Total Files: {results['total_files']}")
        print(f"  Verified: {results['verified_files']}")
        print(f"  Failed: {results['failed_files']}")
        print(f"  Missing: {results['missing_files']}")
        print(f"\nLog written to: {get_path('artifacts') / results['details'][0]['file'] if results['details'] else 'unknown'}")
        
        # Re-read log path for accurate reporting
        log_files = list(get_path("artifacts").glob("integrity_check_*.json"))
        if log_files:
            print(f"  Actual Log File: {log_files[-1]}")

        if results["status"] == "FAILED":
            print("\n⚠️  Integrity check FAILED. Data corruption or missing files detected.")
            sys.exit(1)
        else:
            print("\n✅ Integrity check PASSED. All files are valid.")
            sys.exit(0)

    except DatasetUnavailableError as e:
        print(f"\n❌ Dataset Unavailable: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error during verification: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()