import os
import sys
import logging
from pathlib import Path
from typing import List, Dict, Tuple

from config import get_dataset_paths, get_required_files, DatasetNotFoundError

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def validate_dataset_structure(dataset_name: str, expected_files: List[str], base_path: Path) -> Tuple[bool, List[str]]:
    """
    Validates that all expected files for a given dataset exist in the base path.

    Args:
        dataset_name: Name of the dataset (e.g., 'NarrLV', 'VBench')
        expected_files: List of relative file paths expected for this dataset
        base_path: Root directory where dataset files should reside

    Returns:
        Tuple of (is_valid, list_of_missing_files)
    """
    missing_files = []
    logger.info(f"Validating dataset structure for '{dataset_name}' at {base_path}")

    for file_rel_path in expected_files:
        full_path = base_path / file_rel_path
        if not full_path.exists():
            missing_files.append(str(full_path))
            logger.warning(f"Missing file: {full_path}")
        else:
            logger.debug(f"Found file: {full_path}")

    is_valid = len(missing_files) == 0
    if not is_valid:
        logger.error(f"Dataset '{dataset_name}' validation failed. Missing {len(missing_files)} files.")
    else:
        logger.info(f"Dataset '{dataset_name}' validation passed.")

    return is_valid, missing_files


def validate_all_datasets() -> Dict[str, Tuple[bool, List[str]]]:
    """
    Validates the structure of all required datasets (NarrLV and VBench).

    Returns:
        Dictionary mapping dataset names to (is_valid, missing_files) tuples.
    """
    results = {}
    dataset_paths = get_dataset_paths()

    # NarrLV validation
    if 'narrlv' in dataset_paths:
        narrlv_path = Path(dataset_paths['narrlv'])
        narrlv_required = get_required_files('narrlv')
        results['NarrLV'] = validate_dataset_structure('NarrLV', narrlv_required, narrlv_path)
    else:
        logger.warning("NarrLV dataset path not configured in config.py.")

    # VBench validation
    if 'vbench' in dataset_paths:
        vbench_path = Path(dataset_paths['vbench'])
        vbench_required = get_required_files('vbench')
        results['VBench'] = validate_dataset_structure('VBench', vbench_required, vbench_path)
    else:
        logger.warning("VBench dataset path not configured in config.py.")

    return results


def run_validation_check() -> bool:
    """
    Runs the full validation check for all datasets.

    Returns:
        True if all datasets are valid, False otherwise.
    """
    logger.info("Starting dataset validation check...")
    results = validate_all_datasets()

    all_valid = True
    for dataset_name, (is_valid, missing_files) in results.items():
        if not is_valid:
            all_valid = False
            logger.error(f"Validation failed for {dataset_name}. Missing files: {missing_files}")
        else:
            logger.info(f"Validation succeeded for {dataset_name}.")

    if all_valid:
        logger.info("All dataset validations passed.")
    else:
        logger.error("One or more dataset validations failed.")

    return all_valid


def main():
    """
    CLI entry point for dataset validation.
    """
    parser = argparse.ArgumentParser(description="Validate that all required dataset files are present.")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    success = run_validation_check()

    if not success:
        logger.error("Aborting: Required dataset files are missing. Please run download.py first.")
        sys.exit(1)
    else:
        logger.info("Validation successful. All required files are present.")
        sys.exit(0)


if __name__ == "__main__":
    main()