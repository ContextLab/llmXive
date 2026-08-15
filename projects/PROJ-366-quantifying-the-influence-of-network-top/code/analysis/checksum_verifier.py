"""
Checksum verification module for the llmXive pipeline.

This module provides functionality to verify the integrity of generated artifacts
by comparing their calculated checksums against a stored manifest.
"""
import json
import hashlib
import logging
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

# Configure logging
logger = logging.getLogger(__name__)

def calculate_file_checksum(file_path: Path, algorithm: str = 'sha256') -> str:
    """
    Calculate the checksum of a file.
    
    Args:
        file_path: Path to the file to checksum
        algorithm: Hash algorithm to use (default: sha256)
        
    Returns:
        Hexadecimal string of the checksum
        
    Raises:
        FileNotFoundError: If the file does not exist
        ValueError: If the algorithm is not supported
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    hash_func = hashlib.new(algorithm)
    
    try:
        with open(file_path, 'rb') as f:
            # Read in chunks to handle large files
            for chunk in iter(lambda: f.read(8192), b''):
                hash_func.update(chunk)
        return hash_func.hexdigest()
    except IOError as e:
        logger.error(f"Error reading file {file_path}: {e}")
        raise

def load_checksum_manifest(manifest_path: Path) -> Dict[str, str]:
    """
    Load the checksum manifest from a JSON file.
    
    Args:
        manifest_path: Path to the checksum manifest JSON file
        
    Returns:
        Dictionary mapping file paths to their expected checksums
        
    Raises:
        FileNotFoundError: If the manifest does not exist
        json.JSONDecodeError: If the manifest is not valid JSON
    """
    if not manifest_path.exists():
        raise FileNotFoundError(f"Checksum manifest not found: {manifest_path}")
    
    try:
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)
            return manifest.get('checksums', {})
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in manifest {manifest_path}: {e}")
        raise

def verify_checksums(manifest_path: Path, base_dir: Optional[Path] = None) -> Tuple[bool, List[Dict[str, Any]]]:
    """
    Verify all checksums in the manifest against the actual files.
    
    Args:
        manifest_path: Path to the checksum manifest JSON file
        base_dir: Base directory for resolving relative file paths (default: manifest's directory)
        
    Returns:
        Tuple of (all_passed, list of verification results)
        where each result is a dict with 'file', 'expected', 'actual', 'passed'
    """
    if base_dir is None:
        base_dir = manifest_path.parent
    
    expected_checksums = load_checksum_manifest(manifest_path)
    results = []
    all_passed = True
    
    for relative_path, expected_checksum in expected_checksums.items():
        file_path = base_dir / relative_path
        
        if not file_path.exists():
            results.append({
                'file': str(file_path),
                'expected': expected_checksum,
                'actual': None,
                'passed': False,
                'error': 'File not found'
            })
            all_passed = False
            logger.error(f"File not found: {file_path}")
            continue
        
        try:
            actual_checksum = calculate_file_checksum(file_path)
            passed = actual_checksum == expected_checksum
            
            results.append({
                'file': str(file_path),
                'expected': expected_checksum,
                'actual': actual_checksum,
                'passed': passed
            })
            
            if not passed:
                all_passed = False
                logger.error(f"Checksum mismatch for {file_path}: expected {expected_checksum}, got {actual_checksum}")
            else:
                logger.info(f"Checksum verified: {file_path}")
                
        except Exception as e:
            results.append({
                'file': str(file_path),
                'expected': expected_checksum,
                'actual': None,
                'passed': False,
                'error': str(e)
            })
            all_passed = False
            logger.error(f"Error verifying {file_path}: {e}")
    
    return all_passed, results

def main():
    """
    Main entry point for checksum verification.
    
    Reads the manifest from data/checksums.json and verifies all files.
    Exits with code 0 if all checksums match, 1 otherwise.
    """
    # Determine paths
    project_root = Path(__file__).parent.parent.parent
    manifest_path = project_root / 'data' / 'checksums.json'
    
    if not manifest_path.exists():
        logger.error(f"Checksum manifest not found at {manifest_path}")
        print(f"Error: Checksum manifest not found at {manifest_path}")
        sys.exit(1)
    
    logger.info(f"Verifying checksums from {manifest_path}")
    
    all_passed, results = verify_checksums(manifest_path, project_root)
    
    # Print summary
    print("\n" + "="*60)
    print("CHECKSUM VERIFICATION SUMMARY")
    print("="*60)
    
    passed_count = sum(1 for r in results if r['passed'])
    failed_count = len(results) - passed_count
    
    print(f"Total files: {len(results)}")
    print(f"Passed: {passed_count}")
    print(f"Failed: {failed_count}")
    
    if not all_passed:
        print("\nFailed files:")
        for r in results:
            if not r['passed']:
                print(f"  - {r['file']}: {r.get('error', 'Checksum mismatch')}")
        print("\n" + "="*60)
        print("VERIFICATION FAILED")
        print("="*60)
        sys.exit(1)
    else:
        print("\n" + "="*60)
        print("ALL CHECKSUMS VERIFIED SUCCESSFULLY")
        print("="*60)
        sys.exit(0)

if __name__ == '__main__':
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    main()
