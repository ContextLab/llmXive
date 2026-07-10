"""
Checksum verification utilities for data integrity.

This module provides functions to calculate MD5 checksums for files
and verify them against a stored checksums.txt file.
"""
import os
import hashlib
import sys
from pathlib import Path
from typing import List, Tuple, Optional

# Import logging utilities from existing project modules
from code.utils.logging import setup_logger, log_data_gap

# Import path constants from data module if available, otherwise define defaults
try:
    from code.data import CHECKSUMS_FILE, PROCESSED_DIR, RAW_DIR
except ImportError:
    # Fallback defaults if data module constants aren't fully initialized yet
    CHECKSUMS_FILE = "data/checksums.txt"
    PROCESSED_DIR = "data/processed"
    RAW_DIR = "data/raw"

def calculate_md5(file_path: str) -> str:
    """
    Calculate MD5 checksum of a file.
    
    Args:
        file_path: Path to the file to calculate checksum for
    
    Returns:
        Hex digest of the MD5 hash
    
    Raises:
        FileNotFoundError: If the file does not exist
        PermissionError: If the file cannot be read
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    hash_md5 = hashlib.md5()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    return hash_md5.hexdigest()


def verify_checksums(
    checksum_file_path: Optional[str] = None, 
    base_dir: Optional[str] = None
) -> Tuple[bool, List[str], List[str]]:
    """
    Verify file checksums against a checksums.txt file.
    
    Args:
        checksum_file_path: Path to the checksums.txt file. If None, uses default location.
        base_dir: Base directory for relative paths in checksum file. If None, uses parent of checksum file.
    
    Returns:
        Tuple of (all_valid, valid_files, invalid_files)
        - all_valid: True if all checksums match, False otherwise
        - valid_files: List of successfully verified file paths
        - invalid_files: List of files with mismatched or missing checksums
    
    Raises:
        FileNotFoundError: If the checksum file does not exist
    """
    if checksum_file_path is None:
        checksum_file_path = CHECKSUMS_FILE
    
    checksum_path = Path(checksum_file_path)
    if not checksum_path.exists():
        logger = setup_logger()
        logger.warning(f"Checksum file not found: {checksum_file_path}")
        return True, [], []  # No checksums to verify is considered valid
    
    if base_dir is None:
        base_dir = str(checksum_path.parent)
    
    base_path = Path(base_dir)
    all_valid = True
    valid_files = []
    invalid_files = []
    
    logger = setup_logger()
    logger.info(f"Starting checksum verification using: {checksum_file_path}")
    
    with open(checksum_path, "r") as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            
            # Skip empty lines and comments
            if not line or line.startswith("#"):
                continue
            
            # Parse the line: format is "hash relative_path"
            parts = line.split()
            if len(parts) < 2:
                logger.warning(f"Invalid checksum format at line {line_num}: {line}")
                all_valid = False
                invalid_files.append(f"Invalid format at line {line_num}")
                continue
            
            expected_hash = parts[0]
            relative_path = parts[1]
            file_path = base_path / relative_path
            
            # Check if file exists
            if not file_path.exists():
                msg = f"Missing file: {file_path}"
                logger.error(msg)
                log_data_gap(f"Checksum verification failed: {msg}")
                all_valid = False
                invalid_files.append(str(file_path))
                continue
            
            # Calculate and compare checksum
            try:
                actual_hash = calculate_md5(str(file_path))
            except (FileNotFoundError, PermissionError) as e:
                msg = f"Error reading {file_path}: {str(e)}"
                logger.error(msg)
                all_valid = False
                invalid_files.append(str(file_path))
                continue
            
            if actual_hash != expected_hash:
                msg = f"Checksum mismatch for {file_path}\n  Expected: {expected_hash}\n  Actual:   {actual_hash}"
                logger.error(msg)
                all_valid = False
                invalid_files.append(str(file_path))
            else:
                logger.info(f"Verified: {file_path}")
                valid_files.append(str(file_path))
    
    return all_valid, valid_files, invalid_files


def main():
    """
    Command-line entry point for checksum verification.
    
    Usage:
        python -m code.utils.verify_checksums [checksum_file] [base_dir]
    
    Arguments:
        checksum_file: Path to checksums file (default: data/checksums.txt)
        base_dir: Base directory for relative paths (default: parent of checksum file)
    """
    args = sys.argv[1:]
    
    checksum_file = args[0] if len(args) > 0 else None
    base_dir = args[1] if len(args) > 1 else None
    
    logger = setup_logger()
    logger.info("=== Checksum Verification Tool ===")
    
    try:
        all_valid, valid_files, invalid_files = verify_checksums(checksum_file, base_dir)
        
        print("\n" + "=" * 40)
        print("VERIFICATION SUMMARY")
        print("=" * 40)
        print(f"Total files verified: {len(valid_files)}")
        print(f"Files with errors: {len(invalid_files)}")
        
        if all_valid:
            print("\n✅ All checksums verified successfully!")
            sys.exit(0)
        else:
            print("\n❌ Checksum verification FAILED!")
            if invalid_files:
                print("\nFailed files:")
                for f in invalid_files:
                    print(f"  - {f}")
            sys.exit(1)
            
    except FileNotFoundError as e:
        logger.error(f"Fatal error: {str(e)}")
        print(f"\n❌ Error: {str(e)}")
        sys.exit(2)
    except Exception as e:
        logger.error(f"Unexpected error during verification: {str(e)}")
        print(f"\n❌ Unexpected error: {str(e)}")
        sys.exit(3)


if __name__ == "__main__":
    main()