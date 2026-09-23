"""
Data Validator Module for OpenNeuro BIDS datasets.

This module verifies the BIDS structure of downloaded datasets and validates
the integrity of raw NIfTI files via checksums. It handles corrupted subjects
by skipping them and logging warnings, ensuring only valid data proceeds
to the analysis pipeline.

Critical Constraint: If the number of valid subjects is less than 5, the
pipeline must raise a ValueError with exit code 1 and log "Insufficient Data".
"""

import hashlib
import json
import logging
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional

# Import seed manager for reproducibility if needed, though validation is deterministic
from utils.seed_manager import set_global_seed

logger = logging.getLogger(__name__)

# Constants
MIN_VALID_SUBJECTS = 5
BIDS_REQUIRED_FILES = ["dataset_description.json", "README"]
NIFTI_EXTENSIONS = [".nii", ".nii.gz"]

def calculate_file_checksum(file_path: Path, algorithm: str = "md5") -> str:
    """
    Calculate the checksum of a file to verify integrity.

    Args:
        file_path: Path to the file.
        algorithm: Hash algorithm to use (default: md5).

    Returns:
        Hexadecimal string of the checksum.

    Raises:
        FileNotFoundError: If the file does not exist.
        IOError: If the file cannot be read.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found for checksum: {file_path}")

    hash_obj = hashlib.new(algorithm)
    try:
        with open(file_path, "rb") as f:
            # Read in chunks to handle large NIfTI files without memory issues
            for chunk in iter(lambda: f.read(65536), b""):
                hash_obj.update(chunk)
        return hash_obj.hexdigest()
    except IOError as e:
        logger.error(f"IOError reading file for checksum {file_path}: {e}")
        raise

def validate_bids_structure(dataset_root: Path) -> Tuple[bool, List[str]]:
    """
    Validate the basic BIDS structure of a dataset directory.

    Checks for required top-level files and expected directory structure.

    Args:
        dataset_root: Path to the root of the BIDS dataset.

    Returns:
        Tuple of (is_valid, list_of_missing_or_invalid_items).
    """
    issues = []

    if not dataset_root.exists():
        return False, [f"Dataset root does not exist: {dataset_root}"]

    # Check required BIDS files
    for req_file in BIDS_REQUIRED_FILES:
        file_path = dataset_root / req_file
        if not file_path.exists():
            issues.append(f"Missing required BIDS file: {req_file}")

    # Check for subject directories (sub-*)
    subject_dirs = [d for d in dataset_root.iterdir() if d.is_dir() and d.name.startswith("sub-")]
    if not subject_dirs:
        issues.append("No subject directories (sub-*) found in dataset root.")

    if issues:
        return False, issues
    return True, []

def validate_subject_files(subject_dir: Path) -> Tuple[bool, List[str]]:
    """
    Validate that a subject directory contains expected NIfTI files.

    Args:
        subject_dir: Path to the subject directory (e.g., sub-01).

    Returns:
        Tuple of (is_valid, list_of_issues).
    """
    issues = []
    has_nifti = False

    # Recursively look for NIfTI files
    nifti_files = list(subject_dir.rglob("*"))
    nifti_files = [f for f in nifti_files if any(f.suffix == ext for ext in NIFTI_EXTENSIONS)]

    if not nifti_files:
        issues.append(f"No NIfTI files found in {subject_dir}")
        return False, issues

    for nifti_file in nifti_files:
        if not nifti_file.is_file():
            issues.append(f"Invalid file entry: {nifti_file}")
        else:
            # Check if file is readable and non-empty
            try:
                size = nifti_file.stat().st_size
                if size == 0:
                    issues.append(f"Empty NIfTI file detected: {nifti_file}")
                else:
                    has_nifti = True
            except OSError as e:
                issues.append(f"Cannot stat file {nifti_file}: {e}")

    if not has_nifti:
        issues.append(f"No valid NIfTI files in {subject_dir}")
        return False, issues

    return True, []

def validate_checksums(
    subject_dir: Path, checksum_map: Optional[Dict[str, str]] = None
) -> Tuple[bool, List[str]]:
    """
    Validate checksums of NIfTI files against a provided map.

    If checksum_map is None, this function currently only checks for file
    existence and readability, acting as a placeholder for future checksum
    verification against a manifest.

    Args:
        subject_dir: Path to the subject directory.
        checksum_map: Optional dictionary mapping filenames to expected checksums.

    Returns:
        Tuple of (is_valid, list_of_issues).
    """
    issues = []
    nifti_files = list(subject_dir.rglob("*"))
    nifti_files = [f for f in nifti_files if any(f.suffix == ext for ext in NIFTI_EXTENSIONS)]

    for nifti_file in nifti_files:
        try:
            current_checksum = calculate_file_checksum(nifti_file)
            logger.debug(f"Calculated checksum for {nifti_file}: {current_checksum}")

            if checksum_map:
                filename = nifti_file.name
                if filename in checksum_map:
                    expected = checksum_map[filename]
                    if current_checksum != expected:
                        issues.append(
                            f"Checksum mismatch for {filename}: "
                            f"expected {expected}, got {current_checksum}"
                        )
                else:
                    logger.warning(f"No checksum entry for {filename} in provided map.")
        except Exception as e:
            issues.append(f"Failed to calculate checksum for {nifti_file}: {e}")

    if issues:
        return False, issues
    return True, []

def get_valid_subjects_list(
    dataset_root: Path, checksum_map: Optional[Dict[str, str]] = None
) -> List[Dict[str, Any]]:
    """
    Iterate through all subject directories and return a list of valid subjects.

    This function performs the full validation pipeline:
    1. Checks BIDS structure at root.
    2. Iterates through sub-* directories.
    3. Validates file structure and checksums.
    4. Skips corrupted subjects and logs warnings.

    Args:
        dataset_root: Path to the BIDS dataset root.
        checksum_map: Optional map of expected checksums.

    Returns:
        List of dictionaries containing valid subject info:
        [
          {"subject_id": "sub-01", "path": Path(...), "nifti_files": [...], "status": "valid"},
          ...
        ]

    Raises:
        ValueError: If the number of valid subjects is less than MIN_VALID_SUBJECTS.
    """
    # Step 1: Validate root BIDS structure
    is_valid, issues = validate_bids_structure(dataset_root)
    if not is_valid:
        logger.warning(f"BIDS structure validation failed at root: {issues}")
        # We proceed to check subjects anyway, but log the structural issues

    valid_subjects = []
    skipped_subjects = []

    # Find all subject directories
    subject_dirs = [d for d in dataset_root.iterdir() if d.is_dir() and d.name.startswith("sub-")]

    if not subject_dirs:
        logger.error("No subject directories found in dataset root.")
        raise ValueError("Insufficient Data: No subject directories found.")

    for subject_dir in sorted(subject_dirs):
        subject_id = subject_dir.name
        logger.info(f"Validating subject: {subject_id}")

        # Validate subject file structure
        struct_valid, struct_issues = validate_subject_files(subject_dir)
        if not struct_valid:
            warning_msg = f"Skipping {subject_id} due to structural issues: {struct_issues}"
            logger.warning(warning_msg)
            skipped_subjects.append({"id": subject_id, "reason": "structure", "details": struct_issues})
            continue

        # Validate checksums
        checksum_valid, checksum_issues = validate_checksums(subject_dir, checksum_map)
        if not checksum_valid:
            warning_msg = f"Skipping {subject_id} due to checksum issues: {checksum_issues}"
            logger.warning(warning_msg)
            skipped_subjects.append({"id": subject_id, "reason": "checksum", "details": checksum_issues})
            continue

        # If we reach here, the subject is valid
        nifti_files = [str(f) for f in subject_dir.rglob("*") if any(f.suffix == ext for ext in NIFTI_EXTENSIONS)]
        valid_subjects.append({
            "subject_id": subject_id,
            "path": str(subject_dir),
            "nifti_files": nifti_files,
            "status": "valid"
        })
        logger.info(f"Subject {subject_id} validated successfully.")

    # Log summary
    logger.info(f"Validation complete. Valid subjects: {len(valid_subjects)}, Skipped: {len(skipped_subjects)}")
    for skipped in skipped_subjects:
        logger.warning(f"Skipped {skipped['id']}: {skipped['reason']} - {skipped['details']}")

    # CRITICAL CHECK: Edge Case 1 - Insufficient Data
    if len(valid_subjects) < MIN_VALID_SUBJECTS:
        error_msg = f"Insufficient Data: Found {len(valid_subjects)} valid subjects, but minimum required is {MIN_VALID_SUBJECTS}."
        logger.error(error_msg)
        # Raise error with code 1 equivalent by raising ValueError
        raise ValueError(error_msg)

    return valid_subjects

def main():
    """
    Main entry point for the data validator.
    Expects a dataset root path as a command-line argument.
    """
    parser = __import__('argparse').ArgumentParser(
        description="Validate BIDS dataset structure and file integrity."
    )
    parser.add_argument(
        "dataset_root",
        type=str,
        help="Path to the root directory of the BIDS dataset."
    )
    parser.add_argument(
        "--checksum-map",
        type=str,
        default=None,
        help="Optional path to a JSON file containing expected checksums."
    )
    parser.add_argument(
        "--log-file",
        type=str,
        default="validation_report.log",
        help="Path to the log file."
    )

    args = parser.parse_args()

    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(args.log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )

    dataset_path = Path(args.dataset_root)

    if not dataset_path.exists():
        logger.error(f"Dataset root does not exist: {dataset_path}")
        sys.exit(1)

    checksum_map = None
    if args.checksum_map:
        try:
            with open(args.checksum_map, "r") as f:
                checksum_map = json.load(f)
            logger.info(f"Loaded checksum map from {args.checksum_map}")
        except Exception as e:
            logger.warning(f"Could not load checksum map: {e}")
            checksum_map = None

    try:
        valid_subjects = get_valid_subjects_list(dataset_path, checksum_map)
        logger.info(f"SUCCESS: {len(valid_subjects)} valid subjects found.")
        
        # Write summary to a JSON file for downstream tasks
        summary_path = dataset_path.parent / "validation_summary.json"
        with open(summary_path, "w") as f:
            json.dump({
                "dataset_root": str(dataset_path),
                "valid_count": len(valid_subjects),
                "subjects": valid_subjects
            }, f, indent=2)
        logger.info(f"Validation summary written to {summary_path}")
        
        sys.exit(0)
    except ValueError as e:
        logger.error(f"VALIDATION FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during validation: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
