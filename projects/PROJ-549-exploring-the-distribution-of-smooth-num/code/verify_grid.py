"""
Verify Grid Generation (Task T023b)
Validates the output of T023 (density measurements generation).
"""
import argparse
import csv
import json
import logging
import os
import sys
from typing import Dict, Any, List, Optional

# Expected columns based on T023 requirements
EXPECTED_COLUMNS = ['x', 'y', 'h', 'start_offset', 'count', 'density', 'ratio']

def verify_file(file_path: str, expected_source: str) -> Dict[str, Any]:
    """
    Verify a single density measurement file.
    
    Args:
        file_path: Path to the CSV file.
        expected_source: Expected value in the 'source' column ('spec' or 'plan').
    
    Returns:
        Dictionary with verification results.
    """
    result = {
        "exists": False,
        "non_zero_rows": False,
        "source_column_valid": False,
        "schema_valid": False,
        "error": None
    }

    if not os.path.exists(file_path):
        result["error"] = f"File not found: {file_path}"
        return result

    result["exists"] = True

    try:
        with open(file_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            # Check schema
            if reader.fieldnames is None:
                result["error"] = "File is empty or has no header."
                return result
            
            actual_columns = set(reader.fieldnames)
            expected_set = set(EXPECTED_COLUMNS)
            
            # Check if source column is present (it's part of expected columns in T023 description)
            # Note: The task description lists columns: x, y, h, start_offset, count, density, ratio
            # But T023 also says "Save results ... with a `source` column".
            # We must verify the source column exists and has the correct value.
            if 'source' not in actual_columns:
                result["error"] = "Missing 'source' column in schema."
                return result
            
            expected_set.add('source')
            if actual_columns != expected_set:
                # Allow extra columns? No, strict schema check usually.
                # But let's be lenient: must have ALL expected columns.
                missing = expected_set - actual_columns
                if missing:
                    result["error"] = f"Missing required columns: {missing}"
                    return result

            result["schema_valid"] = True

            rows = list(reader)
            row_count = len(rows)

            if row_count == 0:
                result["error"] = "File has no data rows."
                return result
            
            result["non_zero_rows"] = True

            # Verify source column values
            source_values = set(row['source'] for row in rows)
            if source_values != {expected_source}:
                result["error"] = f"Source column contains unexpected values: {source_values}. Expected: {{'{expected_source}'}}"
                return result

            result["source_column_valid"] = True

    except Exception as e:
        result["error"] = f"Error reading file: {str(e)}"
        return result

    return result

def main():
    parser = argparse.ArgumentParser(description="Verify grid generation output (T023b)")
    parser.add_argument("--spec-file", default="data/density_measurements_spec.csv",
                        help="Path to Spec grid CSV")
    parser.add_argument("--plan-file", default="data/density_measurements_plan.csv",
                        help="Path to Plan grid CSV")
    parser.add_argument("--output", default="data/grid_verification.json",
                        help="Path to output JSON report")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    spec_result = verify_file(args.spec_file, "spec")
    plan_result = verify_file(args.plan_file, "plan")

    spec_valid = (
        spec_result["exists"] and
        spec_result["non_zero_rows"] and
        spec_result["source_column_valid"] and
        spec_result["schema_valid"]
    )

    plan_valid = (
        plan_result["exists"] and
        plan_result["non_zero_rows"] and
        plan_result["source_column_valid"] and
        plan_result["schema_valid"]
    )

    report = {
        "spec_valid": spec_valid,
        "plan_valid": plan_valid,
        "spec_details": spec_result,
        "plan_details": plan_result
    }

    # Ensure output directory exists
    os.makedirs(os.path.dirname(args.output) or '.', exist_ok=True)

    with open(args.output, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)

    logging.info(f"Verification complete. Spec valid: {spec_valid}, Plan valid: {plan_valid}")
    logging.info(f"Report saved to {args.output}")

    if spec_valid and plan_valid:
        sys.exit(0)
    else:
        logging.error("One or more files failed verification.")
        sys.exit(1)

if __name__ == "__main__":
    main()