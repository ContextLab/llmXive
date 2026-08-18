"""
Validation utilities for the research pipeline.
Provides functions to validate effect sizes, study rows, file sizes,
and generated plots.
"""
import logging
import math
import os
import sys
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Import from project utils
from utils.logger import get_logger, log_error_context
from utils.config import get_project_root

logger = get_logger(__name__)

# Constants for validation
MAX_PLOT_SIZE_MB = 5.0
PLOT_EXTENSIONS = ['.png', '.jpg', '.jpeg', '.pdf', '.svg']


def validate_effect_size(r_value: float) -> bool:
    """
    Validate that an effect size (r) is within the valid range [-1, 1].

    Args:
        r_value: The correlation coefficient to validate.

    Returns:
        True if valid, False otherwise.
    """
    if not isinstance(r_value, (int, float)):
        return False
    return -1.0 <= r_value <= 1.0


def validate_study_row(row: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate a study row for required fields and data types.

    Args:
        row: A dictionary representing a study record.

    Returns:
        A tuple of (is_valid, list_of_errors).
    """
    errors = []
    required_fields = ['author', 'year', 'tract']

    # Check required fields
    for field in required_fields:
        if field not in row or not row[field]:
            errors.append(f"Missing or empty required field: {field}")

    # Check numeric fields if present
    if 'r' in row and row['r'] is not None:
        try:
            r_val = float(row['r'])
            if not validate_effect_size(r_val):
                errors.append(f"Invalid r value: {row['r']} (must be between -1 and 1)")
        except (ValueError, TypeError):
            errors.append(f"Non-numeric r value: {row['r']}")

    if 'n' in row and row['n'] is not None:
        try:
            n_val = int(row['n'])
            if n_val <= 0:
                errors.append(f"Invalid n value: {row['n']} (must be positive)")
        except (ValueError, TypeError):
            errors.append(f"Non-numeric n value: {row['n']}")

    return len(errors) == 0, errors


def filter_valid_studies(studies: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Filter a list of studies, keeping only those that pass validation.

    Args:
        studies: List of study dictionaries.

    Returns:
        List of valid study dictionaries.
    """
    valid_studies = []
    for study in studies:
        is_valid, _ = validate_study_row(study)
        if is_valid:
            valid_studies.append(study)
        else:
            logger.warning(f"Filtered out invalid study: {study.get('author', 'Unknown')}")
    return valid_studies


def validate_file_size(file_path: Path, max_size_mb: float = MAX_PLOT_SIZE_MB) -> Tuple[bool, float]:
    """
    Validate that a file size is below the specified threshold.

    Args:
        file_path: Path to the file to check.
        max_size_mb: Maximum allowed file size in megabytes.

    Returns:
        A tuple of (is_valid, actual_size_mb).
    """
    if not file_path.exists():
        return False, 0.0

    size_bytes = file_path.stat().st_size
    size_mb = size_bytes / (1024 * 1024)
    return size_mb <= max_size_mb, size_mb


def validate_generated_plots(plot_paths: List[Path]) -> Dict[str, Any]:
    """
    Validate a list of generated plot files.

    Checks:
    1. File existence
    2. File size < 5MB
    3. Valid extension

    Args:
        plot_paths: List of paths to plot files.

    Returns:
        A dictionary with validation results.
    """
    results = {
        'overall_status': 'pass',
        'failed_plots': [],
        'details': []
    }

    for plot_path in plot_paths:
        detail = {
            'path': str(plot_path),
            'exists': plot_path.exists(),
            'size_mb': 0.0,
            'valid_size': False,
            'valid_extension': False
        }

        # Check extension
        ext = plot_path.suffix.lower()
        detail['valid_extension'] = ext in PLOT_EXTENSIONS

        # Check existence and size
        if plot_path.exists():
            valid_size, size_mb = validate_file_size(plot_path)
            detail['size_mb'] = round(size_mb, 2)
            detail['valid_size'] = valid_size

            if not valid_size:
                results['overall_status'] = 'fail'
                results['failed_plots'].append(str(plot_path))
                logger.error(f"Plot file too large: {plot_path} ({size_mb:.2f} MB)")
        else:
            results['overall_status'] = 'fail'
            results['failed_plots'].append(str(plot_path))
            logger.error(f"Plot file missing: {plot_path}")

        results['details'].append(detail)

    return results


def run_validation_and_report(plot_paths: List[Path], output_path: Optional[Path] = None) -> int:
    """
    Run validation on generated plots and write a report.

    Args:
        plot_paths: List of paths to validate.
        output_path: Path to write the validation report. If None, uses default location.

    Returns:
        Exit code: 0 if all pass, 2 if any fail (non-fatal for retry logic).
    """
    project_root = get_project_root()
    if output_path is None:
        output_path = project_root / 'data' / 'derived' / 'validation_report.json'

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Validate plots
    validation_result = validate_generated_plots(plot_paths)

    # Write report
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(validation_result, f, indent=2)

    logger.info(f"Validation report written to: {output_path}")
    logger.info(f"Overall status: {validation_result['overall_status']}")

    # Return exit code based on status
    if validation_result['overall_status'] == 'fail':
        logger.warning("Validation failed. Returning exit code 2 for retry logic.")
        return 2
    else:
        logger.info("Validation passed.")
        return 0


def main():
    """
    Main entry point for running validation from command line.
    Expects plot paths as arguments.
    """
    if len(sys.argv) < 2:
        print("Usage: python -m utils.validator <plot_path_1> [plot_path_2] ...")
        sys.exit(1)

    plot_paths = [Path(p) for p in sys.argv[1:]]
    exit_code = run_validation_and_report(plot_paths)
    sys.exit(exit_code)


if __name__ == '__main__':
    main()