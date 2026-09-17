import hashlib
import os
import logging
from pathlib import Path
from typing import Dict, Optional, Tuple, List
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def compute_checksum(file_path: Path, algorithm: str = 'sha256') -> str:
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
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    hasher = hashlib.new(algorithm)
    
    try:
        with open(file_path, 'rb') as f:
            # Read in chunks to handle large files efficiently
            for chunk in iter(lambda: f.read(8192), b''):
                hasher.update(chunk)
        return hasher.hexdigest()
    except Exception as e:
        logger.error(f"Error computing checksum for {file_path}: {e}")
        raise

def generate_checksums(data_root: Path, output_path: Path) -> Dict[str, str]:
    """
    Generate SHA256 checksums for all files in the data directory.

    Args:
        data_root: Root directory containing data files.
        output_path: Path where the checksums.txt file will be written.

    Returns:
        Dictionary mapping relative file paths to their checksums.
    """
    if not data_root.exists():
        logger.warning(f"Data root does not exist: {data_root}. Creating directory.")
        data_root.mkdir(parents=True, exist_ok=True)

    checksums: Dict[str, str] = {}
    
    logger.info(f"Scanning directory: {data_root}")
    
    # Walk through all files recursively
    for root, _, files in os.walk(data_root):
        for filename in files:
            # Skip the checksum file itself if it exists in the data folder
            if filename == 'checksums.txt' and Path(root) == data_root:
                continue
            
            file_path = Path(root) / filename
            rel_path = file_path.relative_to(data_root)
            
            try:
                checksum = compute_checksum(file_path)
                checksums[str(rel_path)] = checksum
                logger.info(f"Checksum generated for {rel_path}: {checksum[:16]}...")
            except Exception as e:
                logger.error(f"Failed to checksum {rel_path}: {e}")
                # Fail loudly as per constraints
                raise

    # Write checksums to file
    with open(output_path, 'w') as f:
        for rel_path, checksum in sorted(checksums.items()):
            f.write(f"{checksum}  {rel_path}\n")
    
    logger.info(f"Checksums written to {output_path}")
    return checksums

def verify_checksums(data_root: Path, checksum_file: Path) -> Tuple[bool, List[str]]:
    """
    Verify file checksums against a stored checksum file.

    Args:
        data_root: Root directory containing data files.
        checksum_file: Path to the checksums.txt file.

    Returns:
        Tuple of (all_valid, list_of_failed_files).
    """
    if not checksum_file.exists():
        logger.error(f"Checksum file not found: {checksum_file}")
        return False, ["Checksum file missing"]

    if not data_root.exists():
        logger.error(f"Data root not found: {data_root}")
        return False, ["Data root missing"]

    failed_files: List[str] = []
    
    with open(checksum_file, 'r') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            
            parts = line.split('  ', 1)
            if len(parts) != 2:
                logger.warning(f"Malformed checksum line: {line}")
                continue
            
            expected_checksum, rel_path = parts
            file_path = data_root / rel_path

            if not file_path.exists():
                logger.error(f"File missing during verification: {rel_path}")
                failed_files.append(rel_path)
                continue

            try:
                actual_checksum = compute_checksum(file_path)
                if actual_checksum != expected_checksum:
                    logger.error(f"Checksum mismatch for {rel_path}")
                    logger.error(f"  Expected: {expected_checksum}")
                    logger.error(f"  Actual:   {actual_checksum}")
                    failed_files.append(rel_path)
                else:
                    logger.info(f"Verified {rel_path}")
            except Exception as e:
                logger.error(f"Error verifying {rel_path}: {e}")
                failed_files.append(rel_path)

    all_valid = len(failed_files) == 0
    if all_valid:
        logger.info("All checksums verified successfully.")
    else:
        logger.error(f"Verification failed for {len(failed_files)} files.")
    
    return all_valid, failed_files

def update_checksum_for_file(file_path: Path, checksum_file: Path) -> None:
    """
    Update the checksum for a specific file in the checksum file.
    If the file doesn't exist in the list, it is added.

    Args:
        file_path: Path to the file to update.
        checksum_file: Path to the checksums.txt file.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    # Load existing checksums
    existing_checksums: Dict[str, str] = {}
    if checksum_file.exists():
        with open(checksum_file, 'r') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                parts = line.split('  ', 1)
                if len(parts) == 2:
                    existing_checksums[parts[1]] = parts[0]

    # Compute new checksum
    new_checksum = compute_checksum(file_path)
    rel_path = str(file_path) # Store full relative path from root if needed, or relative to data
    
    # Update dictionary
    existing_checksums[rel_path] = new_checksum

    # Write back
    with open(checksum_file, 'w') as f:
        for path, checksum in sorted(existing_checksums.items()):
            f.write(f"{checksum}  {path}\n")

    logger.info(f"Updated checksum for {rel_path}")

def main() -> int:
    """
    Main entry point for running the checksum utility.
    Generates checksums for all files in data/ and writes to artifacts/checksums.txt.
    """
    project_root = Path(__file__).resolve().parent.parent
    data_root = project_root / 'data'
    checksum_output = project_root / 'artifacts' / 'checksums.txt'

    # Ensure artifacts directory exists
    checksum_output.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Project root: {project_root}")
    logger.info(f"Data root: {data_root}")
    logger.info(f"Output path: {checksum_output}")

    try:
        generate_checksums(data_root, checksum_output)
        return 0
    except Exception as e:
        logger.error(f"Checksum generation failed: {e}")
        return 1

if __name__ == '__main__':
    import sys
    sys.exit(main())
