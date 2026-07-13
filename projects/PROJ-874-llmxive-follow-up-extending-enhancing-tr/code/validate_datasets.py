"""
Dataset Validation Module for llmXive Pipeline.

This module implements FR-001: Validation to ensure all required dataset files
are present before generation begins. It provides functions to check for the
existence of NarrLV and VBench datasets and aborts execution with clear error
messages if any files are missing.

Dependencies:
- code/config.py (for dataset paths and configuration)
- code/download.py (for abort_on_missing_files utility)
"""

import os
import sys
import logging
from pathlib import Path
from typing import List, Dict, Tuple

# Import configuration
from config import get_dataset_paths, get_required_files

# Import abort utility from download module
from download import abort_on_missing_files

logger = logging.getLogger(__name__)

REQUIRED_DATASETS = ["NarrLV", "VBench"]

def validate_dataset_structure(dataset_name: str, base_path: str) -> Tuple[bool, List[str]]:
    """
    Validates that a specific dataset directory exists and contains the expected structure.

    Args:
        dataset_name: Name of the dataset (e.g., 'NarrLV', 'VBench')
        base_path: Base path where datasets are stored

    Returns:
        Tuple of (is_valid, list_of_missing_files)
    """
    missing_files = []
    dataset_path = Path(base_path) / dataset_name

    if not dataset_path.exists():
        logger.error(f"Dataset directory '{dataset_name}' not found at {dataset_path}")
        missing_files.append(str(dataset_path))
        return False, missing_files

    # Get required files for this dataset from config
    required_files = get_required_files(dataset_name)

    for file_pattern in required_files:
        # Handle both direct file paths and glob patterns
        if '*' in file_pattern:
            matches = list(dataset_path.glob(file_pattern))
            if not matches:
                missing_files.append(str(dataset_path / file_pattern))
                logger.warning(f"No files found matching pattern: {file_pattern}")
        else:
            file_path = dataset_path / file_pattern
            if not file_path.exists():
                missing_files.append(str(file_path))
                logger.warning(f"Missing file: {file_path}")

    is_valid = len(missing_files) == 0
    if not is_valid:
        logger.error(f"Validation failed for {dataset_name}: {len(missing_files)} missing files")
    else:
        logger.info(f"Validation passed for {dataset_name}")

    return is_valid, missing_files

def validate_all_datasets() -> Tuple[bool, Dict[str, List[str]]]:
    """
    Validates all required datasets (NarrLV and VBench) are present and complete.

    Returns:
        Tuple of (all_valid, dict_of_missing_files_by_dataset)
    """
    base_path = get_dataset_paths().get("base_path", "data/raw")
    all_valid = True
    all_missing = {}

    for dataset_name in REQUIRED_DATASETS:
        is_valid, missing_files = validate_dataset_structure(dataset_name, base_path)
        if not is_valid:
            all_valid = False
            all_missing[dataset_name] = missing_files

    return all_valid, all_missing

def run_validation_check() -> bool:
    """
    Main entry point for dataset validation. Checks all required datasets and
    aborts execution if any are missing.

    Returns:
        True if all validations pass, False otherwise (but will abort on failure)
    """
    logger.info("Starting dataset validation check (FR-001)...")

    all_valid, missing_by_dataset = validate_all_datasets()

    if not all_valid:
        error_msg = "Dataset validation failed. Missing files:\n"
        for dataset, files in missing_by_dataset.items():
            error_msg += f"\n{dataset}:\n"
            for f in files:
                error_msg += f"  - {f}\n"
        
        error_msg += "\nPlease ensure datasets are downloaded using code/download.py"
        error_msg += " or verify the dataset paths in code/config.py."
        
        logger.error(error_msg)
        
        # Use the abort function from download module to exit cleanly
        abort_on_missing_files(missing_by_dataset)
        return False

    logger.info("All dataset validations passed. Ready for generation.")
    return True

def main():
    """CLI entry point for standalone validation."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    success = run_validation_check()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()