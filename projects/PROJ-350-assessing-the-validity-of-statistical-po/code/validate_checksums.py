"""
Script to validate data checksums and ensure file integrity.
Used in CI/CD pipelines to verify data consistency.
"""
import os
import sys
import json
from pathlib import Path
from typing import Dict, List, Optional

# Import from local utils
from code.utils.data_hygiene import compute_sha256, validate_file_exists, create_checksum_manifest, verify_checksums


def main() -> int:
    """
    Main entry point for checksum validation.

    Returns:
        int: Exit code (0 for success, 1 for failure).
    """
    project_root = Path(__file__).parent.parent
    data_dir = project_root / "data"
    manifest_path = data_dir / "checksums.json"

    print(f"Validating data checksums in: {data_dir}")

    # Check if manifest exists
    if not manifest_path.exists():
        print("No checksum manifest found. Creating initial manifest...")
        try:
            create_checksum_manifest(data_dir, manifest_path)
            print(f"Created new manifest: {manifest_path}")
            return 0
        except Exception as e:
            print(f"Error creating manifest: {e}")
            return 1

    # Verify existing manifest
    try:
        is_valid = verify_checksums(data_dir, manifest_path)
        if is_valid:
            print("All data checksums verified successfully.")
            return 0
        else:
            print("WARNING: Some data files have changed or are missing.")
            print("Please update the checksum manifest if these changes are expected.")
            return 1
    except Exception as e:
        print(f"Error during verification: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())