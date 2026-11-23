"""
Checksum Verification Module for PROJ-366.

This module provides functionality to verify that all generated artifacts
in the data pipeline match their recorded checksums in data/checksums.json.
"""

import json
import hashlib
import logging
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def calculate_file_checksum(file_path: Path, algorithm: str = 'sha256') -> str:
    """
    Calculate the checksum of a file.

    Args:
        file_path: Path to the file to checksum.
        algorithm: Hash algorithm to use (default: sha256).

    Returns:
        Hex digest of the file checksum.

    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the algorithm is not supported.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    hasher = hashlib.new(algorithm)
    with open(file_path, 'rb') as f:
        # Read in chunks to handle large files
        for chunk in iter(lambda: f.read(8192), b''):
            hasher.update(chunk)

    return hasher.hexdigest()

def load_checksum_manifest(manifest_path: Path) -> Dict[str, Any]:
    """
    Load the checksum manifest from a JSON file.

    Args:
        manifest_path: Path to the checksums.json file.

    Returns:
        Dictionary containing the manifest data.

    Raises:
        FileNotFoundError: If the manifest file does not exist.
        json.JSONDecodeError: If the manifest is not valid JSON.
    """
    if not manifest_path.exists():
        raise FileNotFoundError(f"Checksum manifest not found: {manifest_path}")

    with open(manifest_path, 'r') as f:
        return json.load(f)

def verify_checksums(manifest_path: Path, base_data_dir: Optional[Path] = None) -> Tuple[bool, List[Dict[str, Any]]]:
    """
    Verify all checksums in the manifest against the actual files.

    Args:
        manifest_path: Path to the checksums.json file.
        base_data_dir: Base directory for data files (defaults to parent of manifest).

    Returns:
        Tuple of (all_passed, list_of_results).
        Each result dict contains: {'path': str, 'status': 'pass' | 'fail' | 'missing', 'expected': str, 'actual': str | None}

    Raises:
        FileNotFoundError: If the manifest file does not exist.
    """
    if base_data_dir is None:
        base_data_dir = manifest_path.parent.parent  # Go up from data/checksums.json to project root or data root

    manifest = load_checksum_manifest(manifest_path)
    checksums = manifest.get('checksums', {})
    algorithm = manifest.get('algorithm', 'sha256')

    results = []
    all_passed = True

    for relative_path, expected_checksum in checksums.items():
        # Resolve the full path
        # Handle both absolute and relative paths in the manifest
        if Path(relative_path).is_absolute():
            file_path = Path(relative_path)
        else:
            # Try relative to base_data_dir
            file_path = base_data_dir / relative_path

        result = {
            'path': str(relative_path),
            'expected': expected_checksum,
            'status': 'unknown',
            'actual': None
        }

        if not file_path.exists():
            result['status'] = 'missing'
            result['actual'] = None
            logger.warning(f"File missing: {file_path}")
            all_passed = False
        else:
            try:
                actual_checksum = calculate_file_checksum(file_path, algorithm)
                result['actual'] = actual_checksum

                if actual_checksum == expected_checksum:
                    result['status'] = 'pass'
                    logger.info(f"Checksum verified: {relative_path}")
                else:
                    result['status'] = 'fail'
                    logger.error(f"Checksum mismatch: {relative_path}")
                    logger.error(f"  Expected: {expected_checksum}")
                    logger.error(f"  Actual:   {actual_checksum}")
                    all_passed = False
            except Exception as e:
                result['status'] = 'error'
                result['actual'] = str(e)
                logger.error(f"Error calculating checksum for {relative_path}: {e}")
                all_passed = False

        results.append(result)

    return all_passed, results

def main():
    """
    Main entry point for the checksum verification script.

    Reads data/checksums.json and verifies all listed files.
    Exits with code 0 if all checksums match, 1 otherwise.
    """
    # Default paths relative to project root
    project_root = Path(__file__).parent.parent.parent
    manifest_path = project_root / 'data' / 'checksums.json'

    if len(sys.argv) > 1:
        manifest_path = Path(sys.argv[1])

    if not manifest_path.exists():
        logger.error(f"Manifest file not found: {manifest_path}")
        sys.exit(1)

    logger.info(f"Verifying checksums from: {manifest_path}")

    try:
        all_passed, results = verify_checksums(manifest_path)

        # Summary
        total = len(results)
        passed = sum(1 for r in results if r['status'] == 'pass')
        failed = sum(1 for r in results if r['status'] == 'fail')
        missing = sum(1 for r in results if r['status'] == 'missing')
        errors = sum(1 for r in results if r['status'] == 'error')

        logger.info(f"Verification Summary:")
        logger.info(f"  Total files: {total}")
        logger.info(f"  Passed:      {passed}")
        logger.info(f"  Failed:      {failed}")
        logger.info(f"  Missing:     {missing}")
        logger.info(f"  Errors:      {errors}")

        if all_passed and total > 0:
            logger.info("SUCCESS: All checksums verified.")
            sys.exit(0)
        elif total == 0:
            logger.warning("WARNING: No checksums found in manifest.")
            sys.exit(1)
        else:
            logger.error("FAILURE: One or more checksums did not verify.")
            sys.exit(1)

    except Exception as e:
        logger.error(f"Verification failed with exception: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()