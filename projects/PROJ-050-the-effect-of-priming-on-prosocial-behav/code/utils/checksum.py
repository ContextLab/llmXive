"""
Checksum utility for verifying raw data integrity.

This module provides functions to compute and verify SHA-256 checksums
for raw data files to ensure data integrity throughout the pipeline.
"""
import hashlib
import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any

from code.config import PROJECT_ROOT
from code.utils.logger import setup_logger

# Configure logger for this module
logger = setup_logger(__name__)

CHECKSUM_FILE_NAME = "checksums.json"
CHUNK_SIZE = 8192  # 8KB chunks for reading large files


def compute_file_checksum(file_path: Path) -> str:
    """
    Compute SHA-256 checksum for a given file.

    Args:
        file_path: Path to the file to compute checksum for.

    Returns:
        Hexadecimal string of the SHA-256 hash.

    Raises:
        FileNotFoundError: If the file does not exist.
        PermissionError: If the file cannot be read.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    sha256_hash = hashlib.sha256()
    
    logger.info(f"Computing checksum for: {file_path}")
    
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(CHUNK_SIZE), b""):
                sha256_hash.update(chunk)
    except PermissionError as e:
        logger.error(f"Permission denied reading file: {file_path}")
        raise
    
    checksum = sha256_hash.hexdigest()
    logger.debug(f"Checksum computed: {checksum[:16]}...")
    return checksum


def save_checksums(checksums: Dict[str, str], output_path: Optional[Path] = None) -> Path:
    """
    Save checksums to a JSON file.

    Args:
        checksums: Dictionary mapping file paths (relative to PROJECT_ROOT) to checksums.
        output_path: Optional path to save checksums. Defaults to data/validation/checksums.json.

    Returns:
        Path to the saved checksum file.
    """
    if output_path is None:
        output_path = PROJECT_ROOT / "data" / "validation" / CHECKSUM_FILE_NAME
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    checksum_data = {
        "version": "1.0",
        "algorithm": "sha256",
        "files": checksums
    }
    
    logger.info(f"Saving checksums to: {output_path}")
    
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(checksum_data, f, indent=2)
    
    return output_path


def load_checksums(checksum_path: Optional[Path] = None) -> Dict[str, str]:
    """
    Load checksums from a JSON file.

    Args:
        checksum_path: Optional path to load checksums from. Defaults to data/validation/checksums.json.

    Returns:
        Dictionary mapping file paths to checksums.

    Raises:
        FileNotFoundError: If the checksum file does not exist.
        json.JSONDecodeError: If the checksum file is not valid JSON.
    """
    if checksum_path is None:
        checksum_path = PROJECT_ROOT / "data" / "validation" / CHECKSUM_FILE_NAME
    
    if not checksum_path.exists():
        raise FileNotFoundError(f"Checksum file not found: {checksum_path}")
    
    logger.info(f"Loading checksums from: {checksum_path}")
    
    with open(checksum_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    return data.get("files", {})


def verify_checksum(file_path: Path, expected_checksum: str) -> bool:
    """
    Verify a file's checksum against an expected value.

    Args:
        file_path: Path to the file to verify.
        expected_checksum: Expected SHA-256 checksum.

    Returns:
        True if checksum matches, False otherwise.
    """
    if not file_path.exists():
        logger.error(f"File not found for verification: {file_path}")
        return False

    actual_checksum = compute_file_checksum(file_path)
    
    if actual_checksum == expected_checksum:
        logger.info(f"Checksum verified for: {file_path}")
        return True
    else:
        logger.error(f"Checksum mismatch for: {file_path}")
        logger.error(f"  Expected: {expected_checksum}")
        logger.error(f"  Actual:   {actual_checksum}")
        return False


def verify_all_checksums(checksum_path: Optional[Path] = None) -> Dict[str, bool]:
    """
    Verify all files against their stored checksums.

    Args:
        checksum_path: Optional path to load checksums from.

    Returns:
        Dictionary mapping file paths to verification results (True/False).
    """
    checksums = load_checksums(checksum_path)
    results = {}
    
    logger.info(f"Verifying {len(checksums)} files...")
    
    for rel_path, expected_checksum in checksums.items():
        file_path = PROJECT_ROOT / rel_path
        results[rel_path] = verify_checksum(file_path, expected_checksum)
    
    all_passed = all(results.values())
    
    if all_passed:
        logger.info("All checksums verified successfully.")
    else:
        failed_files = [f for f, passed in results.items() if not passed]
        logger.error(f"Checksum verification failed for {len(failed_files)} files.")
    
    return results


def generate_and_save_checksums(file_paths: list[Path], output_path: Optional[Path] = None) -> Path:
    """
    Generate checksums for a list of files and save them.

    Args:
        file_paths: List of file paths to compute checksums for.
        output_path: Optional path to save checksums.

    Returns:
        Path to the saved checksum file.
    """
    checksums = {}
    
    logger.info(f"Generating checksums for {len(file_paths)} files...")
    
    for file_path in file_paths:
        if file_path.exists():
          # Make path relative to PROJECT_ROOT for storage
          try:
              rel_path = str(file_path.relative_to(PROJECT_ROOT))
          except ValueError:
              # If file is not under PROJECT_ROOT, use absolute path
              rel_path = str(file_path)
          
          checksum = compute_file_checksum(file_path)
          checksums[rel_path] = checksum
          logger.info(f"  {rel_path}: {checksum[:16]}...")
        else:
          logger.warning(f"File not found, skipping: {file_path}")
    
    return save_checksums(checksums, output_path)


def main():
    """
    Main entry point for checksum utility CLI.
    
    Usage:
      python code/utils/checksum.py --generate <file1> <file2> ...
      python code/utils/checksum.py --verify
      python code/utils/checksum.py --verify-single <file_path>
    """
    import argparse

    parser = argparse.ArgumentParser(
        description="Data checksum utility for verifying raw data integrity."
    )
    
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--generate",
        nargs="+",
        metavar="FILE",
        help="Generate checksums for the specified files"
    )
    group.add_argument(
        "--verify",
        action="store_true",
        help="Verify all files against stored checksums"
    )
    group.add_argument(
        "--verify-single",
        metavar="FILE",
        help="Verify a single file against its stored checksum"
    )
    
    args = parser.parse_args()
    
    if args.generate:
        files = [Path(f) for f in args.generate]
        output_path = generate_and_save_checksums(files)
        print(f"Checksums saved to: {output_path}")
        
    elif args.verify:
        results = verify_all_checksums()
        all_passed = all(results.values())
        exit_code = 0 if all_passed else 1
        print(f"Verification complete. Passed: {sum(results.values())}/{len(results)}")
        exit(exit_code)
        
    elif args.verify_single:
        file_path = Path(args.verify_single)
        checksums = load_checksums()
        
        # Find the file in checksums (handle both relative and absolute paths)
        expected_checksum = None
        try:
            rel_path = str(file_path.relative_to(PROJECT_ROOT))
            expected_checksum = checksums.get(rel_path)
        except ValueError:
            pass
        
        if not expected_checksum:
            expected_checksum = checksums.get(str(file_path))
        
        if not expected_checksum:
            print(f"Error: No stored checksum found for: {file_path}")
            print("Run with --generate to create checksums first.")
            exit(1)
        
        if verify_checksum(file_path, expected_checksum):
            print(f"Checksum verified: {file_path}")
            exit(0)
        else:
            print(f"Checksum verification failed: {file_path}")
            exit(1)


if __name__ == "__main__":
    main()
