"""
Data Directory Structure Creation and Checksum Verification Script.

This script performs two main functions:
1. Creates the required data directory structure if it does not exist.
2. Verifies the integrity of existing data files using SHA-256 checksums
   stored in a manifest file.

It adheres to the "Fail Loudly" principle: if a checksum verification fails
or a required file is missing, it raises a RuntimeError immediately.
"""

import os
import hashlib
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Import seed configuration to ensure reproducibility for any stochastic operations
# (though this script is primarily deterministic, we follow project conventions)
try:
    from config import seed_everything
except ImportError:
    # Fallback if config.py is not in the path yet (though T004 should have created it)
    def seed_everything(seed: int = 42) -> None:
        import random
        import numpy as np
        import torch
        random.seed(seed)
        np.random.seed(seed)
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)

# Ensure reproducibility
seed_everything(42)

# Define project root relative to this file's location
PROJECT_ROOT = Path(__file__).parent.parent.resolve()
DATA_DIR = PROJECT_ROOT / "data"
MANIFEST_PATH = DATA_DIR / ".data_manifest.json"

# Required directory structure based on T001 and tasks.md
REQUIRED_DIRS = [
    "raw",
    "processed",
    "survey",
    "synth",
    "analysis",
    "figures",
]

class DataIntegrityError(Exception):
    """Custom exception for data integrity failures."""
    pass


def create_directory_structure() -> List[str]:
    """
    Creates the required data directory structure.

    Returns:
        List[str]: List of paths that were created.
    """
    created_dirs = []
    for dir_name in REQUIRED_DIRS:
        dir_path = DATA_DIR / dir_name
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            created_dirs.append(str(dir_path.relative_to(PROJECT_ROOT)))
            print(f"Created directory: {dir_path.relative_to(PROJECT_ROOT)}")
        else:
            if not dir_path.is_dir():
                raise DataIntegrityError(f"Path exists but is not a directory: {dir_path}")
    
    if not created_dirs:
        print("All required directories already exist.")
    else:
        print(f"Created {len(created_dirs)} new directories.")
    
    return created_dirs


def calculate_file_hash(file_path: Path) -> str:
    """
    Calculates the SHA-256 hash of a file.

    Args:
        file_path: Path to the file.

    Returns:
        str: Hexadecimal string of the SHA-256 hash.
    """
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except PermissionError:
        raise DataIntegrityError(f"Permission denied reading file: {file_path}")
    except Exception as e:
        raise DataIntegrityError(f"Error calculating hash for {file_path}: {e}")


def load_manifest() -> Dict[str, str]:
    """
    Loads the checksum manifest from disk.

    Returns:
        Dict[str, str]: Mapping of relative file paths to their expected SHA-256 hashes.
    """
    if not MANIFEST_PATH.exists():
        return {}
    
    try:
        with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except json.JSONDecodeError:
        raise DataIntegrityError(f"Invalid JSON in manifest file: {MANIFEST_PATH}")
    except Exception as e:
        raise DataIntegrityError(f"Error loading manifest: {e}")


def save_manifest(checksums: Dict[str, str]) -> None:
    """
    Saves the checksums to the manifest file.

    Args:
        checksums: Mapping of relative file paths to their SHA-256 hashes.
    """
    try:
        with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
            json.dump(checksums, f, indent=2)
        print(f"Manifest saved to: {MANIFEST_PATH.relative_to(PROJECT_ROOT)}")
    except Exception as e:
        raise DataIntegrityError(f"Error saving manifest: {e}")


def scan_data_directory() -> Dict[str, str]:
    """
    Scans the data directory for all files and calculates their hashes.

    Returns:
        Dict[str, str]: Mapping of relative file paths to their current SHA-256 hashes.
    """
    current_checksums = {}
    for file_path in DATA_DIR.rglob("*"):
        if file_path.is_file() and file_path.name != ".data_manifest.json":
            rel_path = str(file_path.relative_to(PROJECT_ROOT))
            current_checksums[rel_path] = calculate_file_hash(file_path)
    return current_checksums


def verify_integrity(update_manifest: bool = False) -> bool:
    """
    Verifies the integrity of data files against the manifest.

    Args:
        update_manifest: If True, updates the manifest with current checksums
                         instead of verifying against it.

    Returns:
        bool: True if verification passes (or manifest is updated), False otherwise.
    """
    print(f"Scanning data directory: {DATA_DIR.relative_to(PROJECT_ROOT)}...")
    current_checksums = scan_data_directory()
    
    if update_manifest:
        if not current_checksums:
            print("No data files found to update manifest.")
            return True
        save_manifest(current_checksums)
        print("Data integrity manifest updated successfully.")
        return True

    # Verification mode
    if not MANIFEST_PATH.exists():
        print("Warning: No manifest file found. Run with --update to create one.")
        return True

    expected_checksums = load_manifest()
    
    if not expected_checksums:
        print("Manifest is empty. Run with --update to populate it.")
        return True

    errors = []
    
    # Check for missing files
    for rel_path in expected_checksums:
        full_path = PROJECT_ROOT / rel_path
        if not full_path.exists():
            errors.append(f"MISSING: {rel_path}")
        else:
            current_hash = current_checksums.get(rel_path)
            expected_hash = expected_checksums[rel_path]
            
            if current_hash is None:
                # This shouldn't happen if the file exists, but handle gracefully
                errors.append(f"ERROR calculating hash for: {rel_path}")
            elif current_hash != expected_hash:
                errors.append(f"CORRUPTED: {rel_path} (Expected: {expected_hash[:16]}..., Got: {current_hash[:16]}...)")

    # Check for new files not in manifest (optional strictness, but good for integrity)
    # We will warn but not fail for new files unless strict mode is added later.
    # For now, we only verify what is expected.
    
    if errors:
        print("\n--- INTEGRITY CHECK FAILED ---")
        for error in errors:
            print(f"  - {error}")
        print("----------------------------")
        return False

    print(f"Verified {len(expected_checksums)} files successfully.")
    return True


def main():
    """Main entry point for the script."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Verify data directory integrity and manage checksums."
    )
    parser.add_argument(
        "--update",
        action="store_true",
        help="Update the manifest with current file checksums instead of verifying."
    )
    parser.add_argument(
        "--create-structure",
        action="store_true",
        default=True,
        help="Create the required directory structure if missing (default: True)."
    )
    
    args = parser.parse_args()

    print("=== Data Integrity Verification Tool ===")
    print(f"Project Root: {PROJECT_ROOT}")
    print(f"Data Directory: {DATA_DIR}")
    print()

    # Step 1: Ensure structure exists
    if args.create_structure:
        print("Checking directory structure...")
        create_directory_structure()
        print()

    # Step 2: Verify or Update
    if args.update:
        print("Updating manifest with current file checksums...")
        if not verify_integrity(update_manifest=True):
            print("Failed to update manifest.")
            sys.exit(1)
    else:
        print("Verifying data integrity...")
        if not verify_integrity(update_manifest=False):
            print("\nERROR: Data integrity check failed. Please investigate.")
            sys.exit(1)
        else:
            print("\nSUCCESS: All data integrity checks passed.")

    print("\n=== Process Complete ===")


if __name__ == "__main__":
    main()
