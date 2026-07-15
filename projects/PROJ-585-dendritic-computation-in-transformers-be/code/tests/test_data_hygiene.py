"""
Test suite for data hygiene and integrity verification.

This script verifies that all required datasets and artifacts have valid checksums
as defined in the project's data hygiene manifest. It ensures that the data used
for experiments has not been corrupted or tampered with.

Usage:
    python code/tests/test_data_hygiene.py
"""
import os
import sys
import hashlib
import argparse
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def calculate_file_hash(file_path: str, algorithm: str = 'sha256') -> str:
    """
    Calculate the hash of a file using the specified algorithm.
    
    Args:
        file_path: Path to the file to hash
        algorithm: Hash algorithm to use (default: sha256)
        
    Returns:
        Hexadecimal hash string
        
    Raises:
        FileNotFoundError: If the file does not exist
        IOError: If the file cannot be read
    """
    hash_func = hashlib.new(algorithm)
    with open(file_path, 'rb') as f:
        # Read in chunks to handle large files
        for chunk in iter(lambda: f.read(8192), b''):
            hash_func.update(chunk)
    return hash_func.hexdigest()

def load_checksum_manifest(manifest_path: str) -> dict:
    """
    Load the checksum manifest file.
    
    Args:
        manifest_path: Path to the manifest file
        
    Returns:
        Dictionary mapping file paths to expected checksums
    """
    manifest = {}
    if not os.path.exists(manifest_path):
        logger.warning(f"Manifest file not found: {manifest_path}")
        return manifest
    
    with open(manifest_path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            # Format: hash  relative_path
            parts = line.split()
            if len(parts) >= 2:
                expected_hash = parts[0]
                file_path = parts[1]
                manifest[file_path] = expected_hash
    
    return manifest

def verify_data_hygiene(project_root: str, manifest_path: str = None) -> bool:
    """
    Verify data hygiene by checking file checksums against the manifest.
    
    Args:
        project_root: Root directory of the project
        manifest_path: Optional path to the manifest file (defaults to data/checksums.manifest)
        
    Returns:
        True if all verifications pass, False otherwise
    """
    if manifest_path is None:
        manifest_path = os.path.join(project_root, 'data', 'checksums.manifest')
    
    logger.info(f"Loading checksum manifest from: {manifest_path}")
    manifest = load_checksum_manifest(manifest_path)
    
    if not manifest:
        logger.warning("No checksums found in manifest. Skipping verification.")
        return True
    
    all_passed = True
    verified_count = 0
    failed_count = 0
    missing_count = 0
    
    for relative_path, expected_hash in manifest.items():
        full_path = os.path.join(project_root, relative_path)
        
        if not os.path.exists(full_path):
            logger.error(f"MISSING: {relative_path}")
            missing_count += 1
            all_passed = False
            continue
        
        try:
            actual_hash = calculate_file_hash(full_path)
            
            if actual_hash == expected_hash:
                logger.info(f"VERIFIED: {relative_path}")
                verified_count += 1
            else:
                logger.error(f"CHECKSUM MISMATCH: {relative_path}")
                logger.error(f"  Expected: {expected_hash}")
                logger.error(f"  Actual:   {actual_hash}")
                failed_count += 1
                all_passed = False
        except Exception as e:
            logger.error(f"ERROR reading {relative_path}: {str(e)}")
            failed_count += 1
            all_passed = False
    
    logger.info(f"\nVerification Summary:")
    logger.info(f"  Verified: {verified_count}")
    logger.info(f"  Failed:   {failed_count}")
    logger.info(f"  Missing:  {missing_count}")
    logger.info(f"  Total:    {len(manifest)}")
    
    if all_passed:
        logger.info("✓ All data hygiene checks PASSED")
    else:
        logger.error("✗ Data hygiene checks FAILED")
    
    return all_passed

def main():
    """Main entry point for the data hygiene test."""
    parser = argparse.ArgumentParser(
        description='Verify data hygiene by checking file checksums'
    )
    parser.add_argument(
        '--project-root',
        type=str,
        default=os.getcwd(),
        help='Project root directory (default: current directory)'
    )
    parser.add_argument(
        '--manifest',
        type=str,
        default=None,
        help='Path to checksum manifest file'
    )
    
    args = parser.parse_args()
    
    logger.info(f"Starting data hygiene verification for project: {args.project_root}")
    
    success = verify_data_hygiene(args.project_root, args.manifest)
    
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()