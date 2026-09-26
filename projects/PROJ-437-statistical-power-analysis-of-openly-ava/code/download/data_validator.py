"""
Data Validator Module for BIDS fMRI Datasets.

This module verifies the BIDS structure of downloaded datasets,
validates checksums of raw NIfTI files, and manages subject-level
validation. It ensures data integrity before preprocessing.

Key Features:
- BIDS structure validation (required files and directory hierarchy)
- SHA256 checksum verification against manifest
- Subject-level validation with corruption detection
- Minimum subject count enforcement (Edge Case 1)
- Comprehensive logging of validation results
"""

import hashlib
import json
import logging
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Configure module logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    logger.addHandler(handler)

# Constants
BIDS_REQUIRED_FILES = [
    'dataset_description.json',
    'participants.tsv',
]
BIDS_REQUIRED_DIRS = [
    'sub-*/func/',
    'sub-*/anat/',
]
MIN_VALID_SUBJECTS = 5
CHECKSUM_MANIFEST_FILE = 'checksums.json'


class DataValidationError(Exception):
    """Custom exception for data validation failures."""
    pass


def calculate_file_checksum(file_path: Path, algorithm: str = 'sha256') -> str:
    """
    Calculate the checksum of a file.

    Args:
        file_path: Path to the file to hash
        algorithm: Hash algorithm to use (default: sha256)

    Returns:
        Hexadecimal string of the file's checksum

    Raises:
        FileNotFoundError: If the file does not exist
        IOError: If the file cannot be read
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    hash_func = hashlib.new(algorithm)
    try:
        with open(file_path, 'rb') as f:
            # Read in chunks to handle large files efficiently
            for chunk in iter(lambda: f.read(8192), b''):
                hash_func.update(chunk)
        return hash_func.hexdigest()
    except IOError as e:
        raise IOError(f"Failed to read file for checksum: {file_path}") from e


def load_checksum_manifest(dataset_path: Path) -> Dict[str, str]:
    """
    Load the checksum manifest for a dataset.

    Args:
        dataset_path: Path to the dataset root directory

    Returns:
        Dictionary mapping relative file paths to their expected checksums
    """
    manifest_path = dataset_path / CHECKSUM_MANIFEST_FILE
    if not manifest_path.exists():
        logger.warning(f"Checksum manifest not found at {manifest_path}. "
                     "Skipping checksum validation.")
        return {}

    try:
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)
        logger.info(f"Loaded checksum manifest with {len(manifest)} entries")
        return manifest
    except (json.JSONDecodeError, IOError) as e:
        logger.error(f"Failed to load checksum manifest: {e}")
        return {}


def validate_bids_structure(dataset_path: Path) -> Tuple[bool, List[str]]:
    """
    Validate that the dataset follows BIDS structure.

    Args:
        dataset_path: Path to the dataset root directory

    Returns:
        Tuple of (is_valid, list_of_missing_items)
    """
    if not dataset_path.exists():
        logger.error(f"Dataset path does not exist: {dataset_path}")
        return False, [f"Dataset path missing: {dataset_path}"]

    missing_items = []

    # Check required files
    for req_file in BIDS_REQUIRED_FILES:
        file_path = dataset_path / req_file
        if not file_path.exists():
            missing_items.append(f"Missing required file: {req_file}")
            logger.warning(f"Missing required BIDS file: {req_file}")

    # Check required directory patterns
    # We check for at least one subject directory with func/anat
    subject_dirs = list(dataset_path.glob('sub-*'))
    if not subject_dirs:
        missing_items.append("No subject directories found (sub-*)")
        logger.warning("No subject directories found in dataset")
    else:
        # Check that subjects have functional or anatomical data
        subjects_with_data = 0
        for sub_dir in subject_dirs:
            has_func = (sub_dir / 'func').exists()
            has_anat = (sub_dir / 'anat').exists()
            if has_func or has_anat:
                subjects_with_data += 1

        if subjects_with_data == 0:
            missing_items.append("No subjects with functional or anatomical data")
            logger.warning("No subjects contain func/ or anat/ directories")

    is_valid = len(missing_items) == 0
    return is_valid, missing_items


def validate_subject_files(dataset_path: Path, 
                         manifest: Dict[str, str]) -> Dict[str, bool]:
    """
    Validate all subject files against checksums.

    Args:
        dataset_path: Path to the dataset root directory
        manifest: Dictionary of expected checksums

    Returns:
        Dictionary mapping subject IDs to validation status
    """
    subject_results = {}
    subject_dirs = list(dataset_path.glob('sub-*'))

    for sub_dir in subject_dirs:
        subject_id = sub_dir.name
        is_valid = True
        errors = []

        # Find all NIfTI files for this subject
        nifti_files = list(sub_dir.rglob('*.nii')) + list(sub_dir.rglob('*.nii.gz'))

        for nifti_file in nifti_files:
            # Get relative path from dataset root
            rel_path = str(nifti_file.relative_to(dataset_path))

            if rel_path in manifest:
                expected_checksum = manifest[rel_path]
                try:
                    actual_checksum = calculate_file_checksum(nifti_file)
                    if actual_checksum != expected_checksum:
                        is_valid = False
                        errors.append(f"Checksum mismatch: {rel_path}")
                        logger.warning(f"Checksum mismatch for {rel_path}: "
                                     f"expected {expected_checksum[:16]}..., "
                                     f"got {actual_checksum[:16]}...")
                except (FileNotFoundError, IOError) as e:
                    is_valid = False
                    errors.append(f"Cannot read file {rel_path}: {e}")
                    logger.error(f"Cannot read file for checksum validation: {rel_path}")
            else:
                # File not in manifest - log but don't fail
                logger.debug(f"File not in manifest: {rel_path}")

        subject_results[subject_id] = is_valid
        if not is_valid:
            logger.warning(f"Subject {subject_id} has validation errors: "
                         f"{', '.join(errors)}")

    return subject_results


def get_valid_subjects_list(dataset_path: Path, 
                          manifest: Dict[str, str]) -> List[str]:
    """
    Get list of subjects that passed validation.

    Args:
        dataset_path: Path to the dataset root directory
        manifest: Dictionary of expected checksums

    Returns:
        List of valid subject IDs
    """
    subject_results = validate_subject_files(dataset_path, manifest)
    valid_subjects = [sub_id for sub_id, is_valid in subject_results.items() 
                    if is_valid]
    
    logger.info(f"Valid subjects: {len(valid_subjects)} / {len(subject_results)}")
    return valid_subjects


def validate_dataset(dataset_path: Path) -> Dict[str, Any]:
    """
    Perform complete validation of a dataset.

    Args:
        dataset_path: Path to the dataset root directory

    Returns:
        Dictionary with validation results including:
        - is_valid: Overall validation status
        - bids_valid: BIDS structure validation status
        - missing_bids_items: List of missing BIDS items
        - total_subjects: Total number of subjects found
        - valid_subjects: List of valid subject IDs
        - invalid_subjects: List of invalid subject IDs
        - checksum_manifest_loaded: Whether manifest was loaded

    Raises:
        DataValidationError: If validation fails critically (e.g., insufficient data)
    """
    logger.info(f"Starting validation for dataset: {dataset_path}")
    
    # Load checksum manifest
    manifest = load_checksum_manifest(dataset_path)
    checksum_manifest_loaded = len(manifest) > 0

    # Validate BIDS structure
    bids_valid, missing_bids_items = validate_bids_structure(dataset_path)

    # Validate subject files
    valid_subjects = get_valid_subjects_list(dataset_path, manifest)
    
    # Get all subjects for count
    all_subjects = [d.name for d in dataset_path.glob('sub-*') if d.is_dir()]
    total_subjects = len(all_subjects)
    invalid_subjects = [s for s in all_subjects if s not in valid_subjects]

    # Check minimum subject count (Edge Case 1)
    if len(valid_subjects) < MIN_VALID_SUBJECTS:
        error_msg = (f"Insufficient Data: Only {len(valid_subjects)} valid subjects "
                    f"found (minimum required: {MIN_VALID_SUBJECTS}). "
                    f"Valid subjects: {valid_subjects}")
        logger.error(error_msg)
        raise DataValidationError(error_msg)

    overall_valid = (bids_valid and len(valid_subjects) >= MIN_VALID_SUBJECTS)

    result = {
        'is_valid': overall_valid,
        'bids_valid': bids_valid,
        'missing_bids_items': missing_bids_items,
        'total_subjects': total_subjects,
        'valid_subjects': valid_subjects,
        'invalid_subjects': invalid_subjects,
        'checksum_manifest_loaded': checksum_manifest_loaded,
        'valid_subject_count': len(valid_subjects)
    }

    logger.info(f"Validation complete: {overall_valid}")
    logger.info(f"Subjects: {len(valid_subjects)} valid, {len(invalid_subjects)} invalid")
    
    return result


def save_validation_report(validation_result: Dict[str, Any], 
                         output_path: Path) -> None:
    """
    Save validation results to a JSON file.

    Args:
        validation_result: Dictionary with validation results
        output_path: Path to save the report
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(validation_result, f, indent=2)
    
    logger.info(f"Validation report saved to: {output_path}")


def main():
    """
    Command-line interface for data validation.
    
    Usage:
        python -m download.data_validator --dataset /path/to/dataset
        python -m download.data_validator --dataset /path/to/dataset --output results/validation_report.json
    """
    import argparse

    parser = argparse.ArgumentParser(
        description='Validate BIDS dataset structure and integrity'
    )
    parser.add_argument(
        '--dataset', '-d',
        type=Path,
        required=True,
        help='Path to the dataset root directory'
    )
    parser.add_argument(
        '--output', '-o',
        type=Path,
        default=None,
        help='Path to save validation report (optional)'
    )
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    try:
        result = validate_dataset(args.dataset)
        
        if args.output:
            save_validation_report(result, args.output)
        
        # Exit with appropriate code
        if not result['is_valid']:
            logger.error("Validation failed")
            sys.exit(1)
        else:
            logger.info("Validation successful")
            sys.exit(0)
            
    except DataValidationError as e:
        logger.error(f"Validation error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during validation: {e}")
        sys.exit(2)


if __name__ == '__main__':
    main()