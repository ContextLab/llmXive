"""
Pre-flight validation module to ensure all required dataset files are present
before generation begins.

This module implements FR-001 by checking for the existence of all required
dataset files (NarrLV and VBench) before any generation process starts.
"""

import os
import sys
import logging
from pathlib import Path
from typing import List, Dict, Tuple

# Import from existing config module
from config import get_dataset_paths, get_required_files, DatasetNotFoundError, ValidationError

logger = logging.getLogger(__name__)


def validate_dataset_files(dataset_name: str, required_files: List[str], base_path: Path) -> Tuple[bool, List[str]]:
    """
    Validate that all required files for a specific dataset exist.

    Args:
        dataset_name: Name of the dataset (e.g., 'NarrLV', 'VBench')
        required_files: List of required file patterns or names
        base_path: Base directory path for the dataset

    Returns:
        Tuple of (all_present: bool, missing_files: List[str])
    """
    missing_files = []

    logger.info(f"Validating dataset files for {dataset_name}...")

    for file_pattern in required_files:
        # Handle both direct file names and patterns
        if '*' in file_pattern or '?' in file_pattern:
            # Pattern matching
            matched_files = list(base_path.glob(file_pattern))
            if not matched_files:
                missing_files.append(file_pattern)
                logger.warning(f"  Missing pattern: {file_pattern} in {base_path}")
        else:
            # Direct file check
            file_path = base_path / file_pattern
            if not file_path.exists():
                missing_files.append(str(file_path))
                logger.warning(f"  Missing file: {file_path}")

    all_present = len(missing_files) == 0

    if all_present:
        logger.info(f"  ✓ All {len(required_files)} required files found for {dataset_name}")
    else:
        logger.error(f"  ✗ {len(missing_files)} required files missing for {dataset_name}")

    return all_present, missing_files


def validate_all_datasets() -> Tuple[bool, Dict[str, List[str]]]:
    """
    Validate that all required datasets have their necessary files present.

    This function checks both NarrLV and VBench datasets as required by the
    project specification.

    Returns:
        Tuple of (all_datasets_valid: bool, missing_by_dataset: Dict[str, List[str]])
    """
    logger.info("Starting pre-flight validation for all datasets...")

    dataset_paths = get_dataset_paths()
    all_valid = True
    missing_by_dataset = {}

    # Validate each dataset
    for dataset_name, base_path in dataset_paths.items():
        if not base_path.exists():
            logger.error(f"Dataset directory does not exist: {base_path}")
            missing_by_dataset[dataset_name] = [f"Directory not found: {base_path}"]
            all_valid = False
            continue

        required_files = get_required_files(dataset_name)
        is_valid, missing_files = validate_dataset_files(dataset_name, required_files, base_path)

        if not is_valid:
            missing_by_dataset[dataset_name] = missing_files
            all_valid = False
        else:
            logger.info(f"✓ Dataset {dataset_name} validation passed")

    return all_valid, missing_by_dataset


def abort_on_missing_datasets(missing_by_dataset: Dict[str, List[str]]) -> None:
    """
    Abort execution with a clear error message listing all missing files.

    Args:
        missing_by_dataset: Dictionary mapping dataset names to lists of missing files
    """
    error_message = [
        "\n" + "="*60,
        "PRE-FLIGHT VALIDATION FAILED",
        "="*60,
        "The following required dataset files are missing. Generation cannot proceed.",
        ""
    ]

    for dataset_name, missing_files in missing_by_dataset.items():
        error_message.append(f"Dataset: {dataset_name}")
        for missing_file in missing_files:
            error_message.append(f"  - {missing_file}")
        error_message.append("")

    error_message.extend([
        "="*60,
        "Please ensure all datasets are downloaded and properly structured.",
        "Run 'python code/download.py' to fetch missing datasets.",
        "="*60 + "\n"
    ])

    error_text = "\n".join(error_message)
    logger.error(error_text)

    raise DatasetNotFoundError(error_text)


def run_pre_flight_check() -> bool:
    """
    Run the complete pre-flight validation check.

    Returns:
        True if all validations pass, False otherwise.

    Raises:
        DatasetNotFoundError: If any required files are missing
    """
    logger.info("Running pre-flight validation check...")

    try:
        all_valid, missing_by_dataset = validate_all_datasets()

        if not all_valid:
            abort_on_missing_datasets(missing_by_dataset)
            return False

        logger.info("✓ Pre-flight validation PASSED. All required datasets are present.")
        return True

    except Exception as e:
        logger.error(f"Pre-flight validation failed with error: {str(e)}")
        raise


def main():
    """
    Main entry point for standalone execution of pre-flight validation.
    """
    # Setup logging
    from config import setup_logging
    setup_logging()

    logger = logging.getLogger(__name__)
    logger.info("Starting pre-flight validation check...")

    try:
        success = run_pre_flight_check()
        if success:
            logger.info("Validation completed successfully.")
            sys.exit(0)
        else:
            logger.error("Validation failed.")
            sys.exit(1)
    except DatasetNotFoundError as e:
        logger.error(f"Dataset validation failed: {str(e)}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during validation: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()
