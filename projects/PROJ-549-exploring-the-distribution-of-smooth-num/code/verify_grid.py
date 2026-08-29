"""
T023b: Verify Grid Generation
Validates the output of T023 (density measurements).
"""
import argparse
import csv
import json
import logging
import os
import sys
from typing import Dict, Any, List

from utils import setup_logging

EXPECTED_COLUMNS = ['x', 'y', 'h', 'start_offset', 'count', 'density', 'ratio', 'source']
SPEC_SOURCE = 'spec'
PLAN_SOURCE = 'plan'
SPEC_FILE = 'data/density_measurements_spec.csv'
PLAN_FILE = 'data/density_measurements_plan.csv'
OUTPUT_FILE = 'data/grid_verification.json'

def verify_file(filepath: str, expected_source: str, logger: logging.Logger) -> Dict[str, Any]:
    """Verify a single CSV file against requirements."""
    result = {
        "exists": False,
        "non_zero_rows": False,
        "source_valid": False,
        "schema_valid": False,
        "error": None
    }

    if not os.path.exists(filepath):
        result["error"] = f"File not found: {filepath}"
        logger.error(result["error"])
        return result

    result["exists"] = True
    logger.info(f"Checking file: {filepath}")

    try:
        with open(filepath, 'r', newline='') as f:
            reader = csv.DictReader(f)
            rows = list(reader)

        if len(rows) == 0:
            result["error"] = "File is empty or has no data rows"
            logger.warning(result["error"])
            return result

        result["non_zero_rows"] = True
        logger.info(f"Found {len(rows)} rows")

        # Check schema
        actual_columns = set(rows[0].keys())
        expected_set = set(EXPECTED_COLUMNS)
        
        if actual_columns != expected_set:
            missing = expected_set - actual_columns
            extra = actual_columns - expected_set
            msg = f"Schema mismatch. Missing: {missing}, Extra: {extra}"
            result["error"] = msg
            logger.error(msg)
            return result

        result["schema_valid"] = True
        logger.info("Schema matches expected columns")

        # Check source column
        sources = set(row['source'] for row in rows)
        if sources != {expected_source}:
            msg = f"Source column contains unexpected values: {sources}"
            result["error"] = msg
            logger.error(msg)
            return result

        result["source_valid"] = True
        logger.info(f"Source column verified as '{expected_source}'")

        return result

    except Exception as e:
        result["error"] = str(e)
        logger.exception("Error reading file")
        return result

def main():
    setup_logging(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    logger.info("Starting Grid Verification (T023b)")

    spec_result = verify_file(SPEC_FILE, SPEC_SOURCE, logger)
    plan_result = verify_file(PLAN_FILE, PLAN_SOURCE, logger)

    spec_valid = (
        spec_result["exists"] and 
        spec_result["non_zero_rows"] and 
        spec_result["source_valid"] and 
        spec_result["schema_valid"]
    )

    plan_valid = (
        plan_result["exists"] and 
        plan_result["non_zero_rows"] and 
        plan_result["source_valid"] and 
        plan_result["schema_valid"]
    )

    output = {
        "spec_valid": spec_valid,
        "plan_valid": plan_valid,
        "spec_details": spec_result,
        "plan_details": plan_result
    }

    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(output, f, indent=2)

    logger.info(f"Verification report written to {OUTPUT_FILE}")

    if spec_valid and plan_valid:
        logger.info("Grid verification PASSED.")
        sys.exit(0)
    else:
        logger.error("Grid verification FAILED.")
        sys.exit(1)

if __name__ == "__main__":
    main()
