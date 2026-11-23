"""
Checksum computation and verification utilities.
"""
import os
import sys
import hashlib
import logging
import json
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


def compute_file_checksum(file_path: Path, algorithm: str = "sha256") -> str:
    """
    Compute the checksum of a file.
    
    Args:
        file_path: Path to the file.
        algorithm: Hash algorithm to use.
        
    Returns:
        str: The hexadecimal digest of the checksum.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        IOError: If the file cannot be read.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
        
    hash_func = hashlib.new(algorithm)
    
    try:
        with open(file_path, "rb") as f:
            # Read in chunks to handle large files
            for chunk in iter(lambda: f.read(4096), b""):
                hash_func.update(chunk)
    except IOError as e:
        logger.error(f"Failed to read file {file_path}: {e}")
        raise
        
    return hash_func.hexdigest()


def save_checksum(file_path: Path, checksum: str, checksum_file: Optional[Path] = None) -> None:
    """
    Save a checksum to a JSON file.
    
    Args:
        file_path: Path to the file whose checksum is saved.
        checksum: The checksum string.
        checksum_file: Optional path for the checksum file. Defaults to <filename>.sha256.json.
    """
    if checksum_file is None:
        checksum_file = file_path.with_suffix(file_path.suffix + ".sha256.json")
        
    data = {
        "file": str(file_path),
        "checksum": checksum,
        "algorithm": "sha256"
    }
    
    try:
        with open(checksum_file, "w") as f:
            json.dump(data, f, indent=2)
        logger.info(f"Checksum saved to {checksum_file}")
    except IOError as e:
        logger.error(f"Failed to save checksum to {checksum_file}: {e}")
        raise


def verify_checksum(file_path: Path, checksum_file: Optional[Path] = None) -> bool:
    """
    Verify a file's checksum against a stored checksum.
    
    Args:
        file_path: Path to the file to verify.
        checksum_file: Optional path to the checksum file.
        
    Returns:
        bool: True if checksum matches, False otherwise.
        
    Raises:
        FileNotFoundError: If the file or checksum file is missing.
    """
    if checksum_file is None:
        checksum_file = file_path.with_suffix(file_path.suffix + ".sha256.json")
        
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
        
    if not checksum_file.exists():
        raise FileNotFoundError(f"Checksum file not found: {checksum_file}")
        
    try:
        with open(checksum_file, "r") as f:
            data = json.load(f)
            
        stored_checksum = data["checksum"]
        stored_algorithm = data.get("algorithm", "sha256")
        
        computed_checksum = compute_file_checksum(file_path, stored_algorithm)
        
        if computed_checksum == stored_checksum:
            logger.info(f"Checksum verification passed for {file_path}")
            return True
        else:
            logger.error(
                f"Checksum mismatch for {file_path}. "
                f"Expected: {stored_checksum}, Got: {computed_checksum}"
            )
            return False
            
    except (IOError, json.JSONDecodeError, KeyError) as e:
        logger.error(f"Failed to verify checksum for {file_path}: {e}")
        raise


def initialize_data_directories() -> None:
    """
    Initialize data directories and their checksum files if needed.
    This is a wrapper around setup_dirs.initialize_directories.
    """
    from utils.setup_dirs import initialize_directories
    initialize_directories()


def main():
    """
    Main entry point for checksum utilities (for testing).
    """
    import argparse
    parser = argparse.ArgumentParser(description="Checksum utilities")
    parser.add_argument("command", choices=["compute", "verify"], help="Command to run")
    parser.add_argument("file", help="Path to the file")
    parser.add_argument("--checksum-file", help="Path to checksum file (for verify)")
    
    args = parser.parse_args()
    file_path = Path(args.file)
    
    if args.command == "compute":
        checksum = compute_file_checksum(file_path)
        print(f"Checksum: {checksum}")
        save_checksum(file_path, checksum)
    elif args.command == "verify":
        checksum_file = Path(args.checksum_file) if args.checksum_file else None
        if verify_checksum(file_path, checksum_file):
            print("Verification passed")
            sys.exit(0)
        else:
            print("Verification failed")
            sys.exit(1)


if __name__ == "__main__":
    main()