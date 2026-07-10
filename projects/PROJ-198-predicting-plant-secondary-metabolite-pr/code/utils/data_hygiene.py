"""
Data Hygiene Utilities.

Provides functions to manage the project data directory structure
and maintain a checksums.txt file for data integrity verification.
"""
import os
import hashlib
from pathlib import Path
from typing import Optional

# Project root relative to this file (assuming code/utils/data_hygiene.py)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
FIGURES_DIR = PROJECT_ROOT / "figures"
CHECKSUMS_FILE = DATA_DIR / "checksums.txt"


def ensure_directory_structure() -> None:
    """
    Creates the required directory structure for the project if it doesn't exist.
    
    Creates:
    - data/raw
    - data/processed
    - figures
    """
    dirs = [DATA_DIR, RAW_DIR, PROCESSED_DIR, FIGURES_DIR]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)


def calculate_file_checksum(filepath: Path) -> str:
    """
    Calculates the SHA-256 checksum of a file.
    
    Args:
        filepath: Path to the file.
        
    Returns:
        Hexadecimal string of the SHA-256 hash.
        
    Raises:
        FileNotFoundError: If the file does not exist.
    """
    if not filepath.exists():
        raise FileNotFoundError(f"File not found: {filepath}")
    
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        # Read in chunks to handle large files
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()


def update_checksums_file() -> None:
    """
    Scans the data/raw and data/processed directories for all files,
    calculates their checksums, and writes them to data/checksums.txt.
    
    Format: <checksum>  <relative_path>
    """
    ensure_directory_structure()
    
    files_to_check = []
    for directory in [RAW_DIR, PROCESSED_DIR]:
        if directory.exists():
            for file_path in directory.rglob("*"):
                if file_path.is_file():
                    files_to_check.append(file_path)
    
    # Sort for deterministic output
    files_to_check.sort()
    
    checksums = []
    for file_path in files_to_check:
        try:
            checksum = calculate_file_checksum(file_path)
            # Store relative path from project root for portability
            rel_path = file_path.relative_to(PROJECT_ROOT)
            checksums.append(f"{checksum}  {rel_path}")
        except FileNotFoundError:
            # Should not happen if we just found it, but safe to skip
            continue
    
    with open(CHECKSUMS_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(checksums))
        if checksums:
            f.write("\n")


def verify_checksums() -> bool:
    """
    Verifies the integrity of all files listed in checksums.txt.
    
    Returns:
        True if all files match their stored checksums, False otherwise.
    """
    if not CHECKSUMS_FILE.exists():
        print("No checksums.txt file found. Run update_checksums_file() first.")
        return False
    
    with open(CHECKSUMS_FILE, "r", encoding="utf-8") as f:
        lines = f.readlines()
    
    all_valid = True
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        parts = line.split("  ", 1)
        if len(parts) != 2:
            print(f"Invalid checksum line format: {line}")
            all_valid = False
            continue
        
        stored_checksum, rel_path = parts
        file_path = PROJECT_ROOT / rel_path
        
        if not file_path.exists():
            print(f"MISSING: {rel_path}")
            all_valid = False
            continue
        
        try:
            current_checksum = calculate_file_checksum(file_path)
            if current_checksum != stored_checksum:
                print(f"MODIFIED: {rel_path} (Expected: {stored_checksum}, Got: {current_checksum})")
                all_valid = False
            else:
                print(f"OK: {rel_path}")
        except Exception as e:
            print(f"ERROR verifying {rel_path}: {e}")
            all_valid = False
    
    return all_valid


def main():
    """
    Entry point for the data hygiene script.
    Ensures directories exist and updates the checksums file.
    """
    print("Ensuring directory structure...")
    ensure_directory_structure()
    
    print("Updating checksums...")
    update_checksums_file()
    
    print(f"Checksums written to {CHECKSUMS_FILE}")
    print("Verification complete.")


if __name__ == "__main__":
    main()
