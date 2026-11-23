"""
Checksum utilities for data integrity verification.
Provides functions for computing and verifying file/directory checksums.
"""
import sys
import argparse
from pathlib import Path
import json
from config import compute_file_checksum, compute_directory_checksum, save_checksums, load_checksums, verify_checksums
from utils import setup_logger, PipelineError

def compute_checksums_for_directory(directory_path: Path) -> dict:
    """
    Compute checksums for all files in a directory.
    
    Args:
        directory_path: Path to the directory to checksum
        
    Returns:
        Dictionary mapping relative file paths to their SHA-256 checksums
    """
    logger = setup_logger("checksum_utils")
    logger.info(f"Computing checksums for {directory_path}")
    
    if not directory_path.exists():
        raise PipelineError(f"Directory does not exist: {directory_path}")
    
    checksums = {}
    for root, dirs, files in os.walk(directory_path):
        dirs[:] = [d for d in dirs if not d.startswith('.')]
        for filename in files:
            if filename == ".gitkeep":
                continue
            filepath = Path(root) / filename
            try:
                checksum = compute_file_checksum(filepath)
                rel_path = filepath.relative_to(directory_path)
                checksums[str(rel_path)] = checksum
            except Exception as e:
                logger.warning(f"Failed to checksum {filepath}: {e}")
    
    return checksums

def verify_all_checksums(directory_path: Path, checksum_file: Path) -> bool:
    """
    Verify all files in a directory against stored checksums.
    
    Args:
        directory_path: Path to the directory to verify
        checksum_file: Path to the checksums file
        
    Returns:
        True if all checksums verify, False otherwise
    """
    logger = setup_logger("checksum_utils")
    
    if not checksum_file.exists():
        logger.error(f"Checksum file not found: {checksum_file}")
        return False
    
    logger.info(f"Verifying checksums for {directory_path}")
    return verify_checksums(checksum_file, directory_path)

def main():
    """
    Command-line interface for checksum operations.
    
    Usage:
      python checksum_utils.py compute <directory>
      python checksum_utils.py verify <directory> <checksum_file>
    """
    parser = argparse.ArgumentParser(description="Checksum utilities")
    parser.add_argument("action", choices=["compute", "verify"], help="Action to perform")
    parser.add_argument("directory", type=Path, help="Target directory")
    parser.add_argument("--checksum-file", type=Path, help="Checksum file (required for verify)")
    
    args = parser.parse_args()
    
    logger = setup_logger("checksum_utils")
    
    if args.action == "compute":
        checksums = compute_checksums_for_directory(args.directory)
        checksum_file = args.directory / "checksums.json"
        save_checksums(checksums, checksum_file)
        logger.info(f"Checksums saved to {checksum_file}")
        print(json.dumps(checksums, indent=2))
        
    elif args.action == "verify":
        if not args.checksum_file:
            logger.error("Checksum file required for verify action")
            sys.exit(1)
        
        success = verify_all_checksums(args.directory, args.checksum_file)
        if success:
            logger.info("All checksums verified successfully")
            sys.exit(0)
        else:
            logger.error("Checksum verification failed")
            sys.exit(1)

if __name__ == "__main__":
    main()
