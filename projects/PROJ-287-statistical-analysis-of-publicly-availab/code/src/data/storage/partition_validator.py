"""
Partition Validator Module for Topic Drift Analysis

Validates that the partitioning logic strictly enforces non-overlapping
multi-year boundaries (e.g., 2000–2004, 2005–2009) as defined in the
project specification. Logs any violations to the reproducibility log
in accordance with Constitution Principle VII.

Dependencies:
- src/utils/logging.py
- src/data/storage/saver.py (for expected manifest structure)
"""

import os
import json
import logging
import re
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Set

from src.utils.logging import get_logger

# Define the expected windows based on project specification
EXPECTED_WINDOWS = [
    (2000, 2004),
    (2005, 2009),
    (2010, 2014),
    (2015, 2019),
    (2020, 2024)
]

class PartitionValidationError(Exception):
    """Custom exception for partition validation failures."""
    pass

def get_logger_module():
    """Returns the module-level logger."""
    return get_logger(__name__)

def load_processed_manifest(manifest_path: Path) -> Dict[str, Any]:
    """
    Loads the processed data manifest.
    
    Args:
        manifest_path: Path to the manifest.json file.
        
    Returns:
        Dictionary containing manifest data.
        
    Raises:
        FileNotFoundError: If manifest does not exist.
        json.JSONDecodeError: If manifest is invalid JSON.
    """
    if not manifest_path.exists():
        raise FileNotFoundError(f"Processed manifest not found at {manifest_path}")
    
    with open(manifest_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def extract_year_range_from_filename(filename: str) -> Optional[Tuple[int, int]]:
    """
    Extracts the year range from a partition filename.
    
    Expected format: <source>_processed_<start_year>-<end_year>.csv
    
    Args:
        filename: The filename to parse.
        
    Returns:
        Tuple of (start_year, end_year) or None if pattern not found.
    """
    # Pattern to match start-end years in filename
    pattern = r'(\d{4})-(\d{4})\.csv$'
    match = re.search(pattern, filename)
    
    if match:
        start_year = int(match.group(1))
        end_year = int(match.group(2))
        return (start_year, end_year)
    
    return None

def validate_window_boundaries(
    processed_dir: Path,
    manifest_data: Dict[str, Any]
) -> Tuple[bool, List[Dict[str, Any]]]:
    """
    Validates that all processed files adhere to the expected non-overlapping
    window boundaries.
    
    Args:
        processed_dir: Directory containing processed CSV files.
        manifest_data: Data from the processed manifest.
        
    Returns:
        Tuple of (is_valid, list_of_violations).
        Each violation is a dict with 'file', 'violation_type', 'details'.
    """
    logger = get_logger_module()
    violations = []
    
    # Get list of CSV files in the processed directory
    if not processed_dir.exists():
        logger.warning(f"Processed directory does not exist: {processed_dir}")
        return True, []  # No files to validate
        
    csv_files = list(processed_dir.glob("*.csv"))
    
    if not csv_files:
        logger.warning(f"No CSV files found in {processed_dir}")
        return True, []
    
    # Track found windows
    found_windows: Set[Tuple[int, int]] = set()
    
    for csv_file in csv_files:
        year_range = extract_year_range_from_filename(csv_file.name)
        
        if year_range is None:
            violation = {
                "file": str(csv_file.name),
                "violation_type": "invalid_naming",
                "details": "Filename does not match expected pattern <start>-<end>.csv"
            }
            violations.append(violation)
            logger.error(f"Invalid filename format: {csv_file.name}")
            continue
        
        start_year, end_year = year_range
        
        # Check if this window is in the expected list
        expected_window = None
        for exp_start, exp_end in EXPECTED_WINDOWS:
            if start_year == exp_start and end_year == exp_end:
                expected_window = (start_year, end_year)
                break
        
        if expected_window is None:
            violation = {
                "file": str(csv_file.name),
                "violation_type": "unexpected_window",
                "details": f"Window ({start_year}-{end_year}) not in expected windows: {EXPECTED_WINDOWS}"
            }
            violations.append(violation)
            logger.error(f"Unexpected window in filename: {start_year}-{end_year}")
            continue
        
        # Check for overlapping windows
        if expected_window in found_windows:
            violation = {
                "file": str(csv_file.name),
                "violation_type": "duplicate_window",
                "details": f"Duplicate window detected: {start_year}-{end_year}"
            }
            violations.append(violation)
            logger.error(f"Duplicate window detected: {start_year}-{end_year}")
        else:
            found_windows.add(expected_window)
        
        # Validate that years are sequential and non-overlapping with other windows
        # Check against all other found windows
        for other_window in found_windows:
            if other_window == expected_window:
                continue
            
            other_start, other_end = other_window
            
            # Check for overlap: two intervals [a,b] and [c,d] overlap if a <= d and c <= b
            if start_year <= other_end and other_start <= end_year:
                violation = {
                    "file": str(csv_file.name),
                    "violation_type": "overlapping_window",
                    "details": f"Window {start_year}-{end_year} overlaps with {other_start}-{other_end}"
                }
                violations.append(violation)
                logger.error(f"Overlapping windows detected: {start_year}-{end_year} and {other_start}-{other_end}")
    
    # Check if all expected windows are present
    missing_windows = [w for w in EXPECTED_WINDOWS if w not in found_windows]
    if missing_windows:
        violation = {
            "file": "global",
            "violation_type": "missing_windows",
            "details": f"Missing expected windows: {missing_windows}"
        }
        violations.append(violation)
        logger.warning(f"Missing expected windows: {missing_windows}")
    
    is_valid = len(violations) == 0
    return is_valid, violations

def log_violations_to_manifest(
    violations: List[Dict[str, Any]],
    manifest_path: Path,
    validation_passed: bool
) -> None:
    """
    Logs validation results and any violations to the reproducibility manifest.
    
    Args:
        violations: List of violation dictionaries.
        manifest_path: Path to the manifest file to update.
        validation_passed: Whether the validation passed.
    """
    logger = get_logger_module()
    
    # Load existing manifest if it exists
    if manifest_path.exists():
        with open(manifest_path, 'r', encoding='utf-8') as f:
            manifest = json.load(f)
    else:
        manifest = {
            "partition_validation": {
                "timestamp": None,
                "passed": None,
                "violations": []
            }
        }
    
    # Update manifest with validation results
    from datetime import datetime, timezone
    
    if "partition_validation" not in manifest:
        manifest["partition_validation"] = {}
    
    manifest["partition_validation"]["timestamp"] = datetime.now(timezone.utc).isoformat()
    manifest["partition_validation"]["passed"] = validation_passed
    manifest["partition_validation"]["violations"] = violations
    
    # Save updated manifest
    with open(manifest_path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2)
    
    if validation_passed:
        logger.info("Partition validation PASSED - all windows are non-overlapping and correctly named")
    else:
        logger.warning(f"Partition validation FAILED - {len(violations)} violations found")
        for v in violations:
            logger.warning(f"  - {v['violation_type']}: {v['details']}")

def run_validation(
    processed_dir: Optional[Path] = None,
    manifest_path: Optional[Path] = None
) -> bool:
    """
    Main validation function that orchestrates the partition integrity check.
    
    Args:
        processed_dir: Path to the directory containing processed CSV files.
                       Defaults to data/processed/
        manifest_path: Path to the manifest file to update.
                       Defaults to results/manifest.json
                       
    Returns:
        True if validation passed, False otherwise.
    """
    logger = get_logger_module()
    logger.info("Starting partition integrity validation...")
    
    # Set default paths if not provided
    if processed_dir is None:
        processed_dir = Path("data/processed")
    
    if manifest_path is None:
        manifest_path = Path("results/manifest.json")
    
    try:
        # Load manifest data (if exists)
        manifest_data = {}
        if manifest_path.exists():
            manifest_data = load_processed_manifest(manifest_path)
        
        # Validate window boundaries
        is_valid, violations = validate_window_boundaries(processed_dir, manifest_data)
        
        # Log results to manifest
        log_violations_to_manifest(violations, manifest_path, is_valid)
        
        return is_valid
        
    except Exception as e:
        logger.error(f"Partition validation failed with exception: {str(e)}")
        raise PartitionValidationError(f"Partition validation failed: {str(e)}")

def main():
    """
    Command-line entry point for partition validation.
    """
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Validate partitioning integrity for topic drift analysis"
    )
    parser.add_argument(
        "--processed-dir",
        type=Path,
        default=Path("data/processed"),
        help="Path to directory containing processed CSV files"
    )
    parser.add_argument(
        "--manifest-path",
        type=Path,
        default=Path("results/manifest.json"),
        help="Path to manifest file for logging results"
    )
    
    args = parser.parse_args()
    
    logger = get_logger_module()
    logger.info(f"Validating partitions in: {args.processed_dir}")
    logger.info(f"Logging results to: {args.manifest_path}")
    
    try:
        success = run_validation(args.processed_dir, args.manifest_path)
        
        if success:
            logger.info("✓ Partition validation successful")
            return 0
        else:
            logger.warning("✗ Partition validation failed - check logs for details")
            return 1
            
    except PartitionValidationError as e:
        logger.error(f"Partition validation error: {str(e)}")
        return 2
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return 3

if __name__ == "__main__":
    exit(main())
