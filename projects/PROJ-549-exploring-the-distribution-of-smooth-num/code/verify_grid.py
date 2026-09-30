"""
Verify Grid Generation (T023b)

Validates the output of T023 (density measurements generation).
Checks existence, row counts, source column values, and schema compliance
for both Spec and Plan grid output files.
"""

import argparse
import csv
import json
import logging
import os
import sys
from typing import Dict, Any, List, Set

# Expected columns for density measurement files
EXPECTED_COLUMNS: Set[str] = {'x', 'y', 'h', 'start_offset', 'count', 'density', 'ratio'}

# File paths relative to project root
SPEC_FILE_PATH: str = 'data/density_measurements_spec.csv'
PLAN_FILE_PATH: str = 'data/density_measurements_plan.csv'
OUTPUT_REPORT_PATH: str = 'data/grid_verification.json'

logger = logging.getLogger(__name__)


def verify_file(
    file_path: str,
    expected_source: str,
    required_columns: Set[str]
) -> Dict[str, Any]:
    """
    Verify a single density measurement CSV file.

    Args:
        file_path: Path to the CSV file.
        expected_source: Expected value in the 'source' column.
        required_columns: Set of required column names.

    Returns:
        Dictionary with verification results.
    """
    result: Dict[str, Any] = {
        'exists': False,
        'non_zero_rows': False,
        'source_column_valid': False,
        'schema_valid': False,
        'row_count': 0,
        'errors': []
    }

    # Check existence
    if not os.path.exists(file_path):
        result['errors'].append(f"File does not exist: {file_path}")
        logger.error(f"File does not exist: {file_path}")
        return result

    result['exists'] = True
    logger.info(f"File exists: {file_path}")

    try:
        with open(file_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)

            # Check schema (columns)
            if reader.fieldnames is None:
                result['errors'].append("CSV file is empty or has no header.")
                logger.error("CSV file is empty or has no header.")
                return result

            actual_columns = set(reader.fieldnames)
            if not required_columns.issubset(actual_columns):
                missing = required_columns - actual_columns
                result['errors'].append(f"Missing required columns: {missing}")
                logger.error(f"Missing required columns: {missing}")
                return result

            result['schema_valid'] = True
            logger.info(f"Schema valid for {file_path}")

            # Check rows and source column
            row_count = 0
            source_values: Set[str] = set()
            for row in reader:
                row_count += 1
                if 'source' in row:
                    source_values.add(row['source'])

            result['row_count'] = row_count

            if row_count == 0:
                result['errors'].append("File has zero data rows.")
                logger.warning(f"File has zero data rows: {file_path}")
            else:
                result['non_zero_rows'] = True
                logger.info(f"Row count: {row_count}")

            # Verify source column values
            if expected_source in source_values:
                # Ensure ONLY the expected source is present (or at least the expected one is dominant)
                # The task says "contains exactly 'spec' and 'plan' values respectively"
                # This implies the file should only contain that specific source value.
                if source_values == {expected_source}:
                    result['source_column_valid'] = True
                    logger.info(f"Source column valid for {file_path} (only '{expected_source}')")
                else:
                    # If other values exist, it might be invalid depending on strictness
                    # The requirement says "contains exactly 'spec' and 'plan' values respectively"
                    # This implies the set of values in the column should be exactly {expected_source}
                    result['errors'].append(f"Source column contains unexpected values: {source_values - {expected_source}}")
                    logger.warning(f"Source column contains unexpected values: {source_values - {expected_source}}")
            else:
                result['errors'].append(f"Source column does not contain expected value '{expected_source}'. Found: {source_values}")
                logger.error(f"Source column does not contain expected value '{expected_source}'. Found: {source_values}")

    except Exception as e:
        result['errors'].append(f"Error reading file: {str(e)}")
        logger.error(f"Error reading file {file_path}: {str(e)}")
        return result

    return result


def main() -> int:
    """
    Main entry point for grid verification.
    """
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )

    logger.info("Starting grid verification (T023b)...")

    # Verify Spec file
    spec_result = verify_file(
        SPEC_FILE_PATH,
        'spec',
        EXPECTED_COLUMNS
    )

    # Verify Plan file
    plan_result = verify_file(
        PLAN_FILE_PATH,
        'plan',
        EXPECTED_COLUMNS
    )

    # Determine overall validity
    spec_valid = (
        spec_result['exists'] and
        spec_result['non_zero_rows'] and
        spec_result['source_column_valid'] and
        spec_result['schema_valid']
    )

    plan_valid = (
        plan_result['exists'] and
        plan_result['non_zero_rows'] and
        plan_result['source_column_valid'] and
        plan_result['schema_valid']
    )

    # Prepare output report
    report: Dict[str, Any] = {
        'spec_valid': spec_valid,
        'plan_valid': plan_valid,
        'spec_details': spec_result,
        'plan_details': plan_result,
        'timestamp': __import__('datetime').datetime.now().isoformat()
    }

    # Write report
    os.makedirs(os.path.dirname(OUTPUT_REPORT_PATH), exist_ok=True)
    with open(OUTPUT_REPORT_PATH, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)

    logger.info(f"Verification report written to {OUTPUT_REPORT_PATH}")

    if spec_valid and plan_valid:
        logger.info("Grid verification PASSED.")
        return 0
    else:
        logger.error("Grid verification FAILED.")
        if not spec_valid:
            logger.error(f"Spec grid issues: {spec_result['errors']}")
        if not plan_valid:
            logger.error(f"Plan grid issues: {plan_result['errors']}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
