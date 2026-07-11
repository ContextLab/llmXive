import os
import sys
import hashlib
import logging
import json
from pathlib import Path
from typing import Optional, Dict, Any

# Configure logging for this module
logger = logging.getLogger(__name__)

def compute_file_checksum(file_path: str, algorithm: str = "sha256") -> str:
    """
    Compute the checksum of a file using the specified algorithm.

    Args:
        file_path: Path to the file to checksum.
        algorithm: Hash algorithm to use (default: sha256).

    Returns:
        Hexadecimal string of the checksum.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the algorithm is not supported.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    hash_obj = hashlib.new(algorithm)
    try:
        with open(path, "rb") as f:
            # Read in chunks to handle large files
            for chunk in iter(lambda: f.read(4096), b""):
                hash_obj.update(chunk)
        return hash_obj.hexdigest()
    except Exception as e:
        logger.error(f"Error computing checksum for {file_path}: {e}")
        raise

def save_checksum(file_path: str, checksum_path: Optional[str] = None, algorithm: str = "sha256") -> Path:
    """
    Compute the checksum of a file and save it to a .checksum.json file.

    Args:
        file_path: Path to the file to checksum.
        checksum_path: Optional path for the checksum file. If None, creates
                       <file_path>.checksum.json in the same directory.
        algorithm: Hash algorithm to use.

    Returns:
        Path to the created checksum file.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    checksum = compute_file_checksum(str(path), algorithm)

    if checksum_path is None:
        checksum_path = str(path.parent / f"{path.name}.checksum.json")
    
    checksum_file = Path(checksum_path)
    
    checksum_data = {
        "file": str(path.absolute()),
        "algorithm": algorithm,
        "checksum": checksum,
        "status": "verified"
    }

    with open(checksum_file, "w") as f:
        json.dump(checksum_data, f, indent=2)
    
    logger.info(f"Checksum saved to {checksum_file}: {checksum}")
    return checksum_file

def verify_checksum(file_path: str, checksum_path: Optional[str] = None) -> bool:
    """
    Verify the checksum of a file against a saved checksum file.

    Args:
        file_path: Path to the file to verify.
        checksum_path: Optional path to the checksum file. If None, looks for
                       <file_path>.checksum.json in the same directory.

    Returns:
        True if checksums match, False otherwise.
    """
    path = Path(file_path)
    if not path.exists():
        logger.error(f"File not found for verification: {file_path}")
        return False

    if checksum_path is None:
        checksum_path = str(path.parent / f"{path.name}.checksum.json")
    
    checksum_file = Path(checksum_path)
    if not checksum_file.exists():
        logger.warning(f"Checksum file not found: {checksum_file}")
        return False

    try:
        with open(checksum_file, "r") as f:
            data = json.load(f)
        
        saved_checksum = data.get("checksum")
        saved_algorithm = data.get("algorithm", "sha256")
        
        if not saved_checksum:
            logger.error("Checksum file is missing 'checksum' field")
            return False

        current_checksum = compute_file_checksum(str(path), saved_algorithm)
        
        if current_checksum == saved_checksum:
            logger.info(f"Checksum verified for {file_path}")
            return True
        else:
            logger.error(f"Checksum mismatch for {file_path}. Expected: {saved_checksum}, Got: {current_checksum}")
            return False
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in checksum file {checksum_file}: {e}")
        return False
    except Exception as e:
        logger.error(f"Error verifying checksum for {file_path}: {e}")
        return False

def initialize_data_directories(base_dir: Optional[str] = None) -> Dict[str, Path]:
    """
    Create the standard data directory structure for the project.
    
    Creates:
        data/raw/
        data/processed/
        data/interim/ (optional, for intermediate processing steps)
    
    Args:
        base_dir: Base directory for data folder. Defaults to project root 'data/'.

    Returns:
        Dictionary mapping directory names to their Path objects.
    """
    if base_dir is None:
        # Default to 'data' relative to current working directory or project root
        base_dir = "data"
    
    base_path = Path(base_dir)
    
    directories = {
        "raw": base_path / "raw",
        "processed": base_path / "processed",
        "interim": base_path / "interim"
    }
    
    for name, dir_path in directories.items():
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {dir_path}")
        else:
            logger.debug(f"Directory already exists: {dir_path}")
    
    return directories

def main():
    """
    Command-line entry point for checksum utilities.
    
    Usage:
        python code/utils/checksum_utils.py --command <command> --file <path> [--checksum-file <path>]
        
    Commands:
        compute  : Compute checksum for a file
        verify   : Verify checksum for a file
        init     : Initialize data directory structure
    """
    import argparse

    parser = argparse.ArgumentParser(description="Checksum utilities for data integrity")
    parser.add_argument("--command", required=True, choices=["compute", "verify", "init"],
                      help="Command to execute")
    parser.add_argument("--file", help="Path to the file to process")
    parser.add_argument("--checksum-file", help="Path to the checksum file (for verify)")
    parser.add_argument("--base-dir", help="Base directory for data (for init)")
    
    args = parser.parse_args()
    
    if args.command == "init":
        dirs = initialize_data_directories(args.base_dir)
        print("Directories initialized:")
        for name, path in dirs.items():
            print(f"  {name}: {path}")
    elif args.command == "compute":
        if not args.file:
            print("Error: --file is required for compute command")
            sys.exit(1)
        try:
            checksum = compute_file_checksum(args.file)
            print(f"Checksum for {args.file}: {checksum}")
            save_checksum(args.file)
            print(f"Checksum saved to {args.file}.checksum.json")
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)
    elif args.command == "verify":
        if not args.file:
            print("Error: --file is required for verify command")
            sys.exit(1)
        if verify_checksum(args.file, args.checksum_file):
            print(f"Verification passed for {args.file}")
            sys.exit(0)
        else:
            print(f"Verification failed for {args.file}")
            sys.exit(1)

if __name__ == "__main__":
    main()
