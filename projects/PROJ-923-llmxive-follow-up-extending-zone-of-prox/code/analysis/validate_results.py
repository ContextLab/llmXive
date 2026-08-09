import os
import sys
import json
import yaml
import argparse
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add project root to path if running as script
if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(project_root))

from utils.validation import load_schema, validate_against_schema, validate_file
from utils.logging import get_logger

logger = get_logger(__name__)

# Define the schema path relative to project root
# Assuming contracts/ is at the project root level as per plan.md
PROJECT_ROOT = Path(__file__).resolve().parent.parent
CONTRACTS_DIR = PROJECT_ROOT / "contracts"
SCHEMA_FILE = CONTRACTS_DIR / "aggregated_metrics.schema.yaml"

# Expected output files from T032/T033
EXPECTED_OUTPUTS = [
    PROJECT_ROOT / "data" / "metrics" / "baseline_results.csv",
    PROJECT_ROOT / "data" / "metrics" / "cap_results.csv",
    PROJECT_ROOT / "data" / "metrics" / "comparison_report.json",
]

def validate_single_result_file(file_path: Path, schema: Dict[str, Any]) -> bool:
    """
    Validates a single metrics CSV file against the aggregated_metrics schema.
    Note: The schema defines the structure of the 'aggregated' record (e.g. AUCC, p-value).
    Since CSVs are row-based, we validate the structure of the first row (header)
    and ensure the file is not empty.
    """
    if not file_path.exists():
        logger.error(f"File not found: {file_path}")
        return False

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            # Load CSV as a list of dicts for easier validation logic if needed
            # But for schema validation, we usually validate the JSON representation
            import csv
            reader = csv.DictReader(f)
            headers = reader.fieldnames
            
            if not headers:
                logger.error(f"File {file_path} is empty or has no headers.")
                return False

            # Convert first row to JSON structure for validation against schema
            # We assume the schema expects a list of records or a single record object
            # The schema likely defines properties like 'aucc', 'final_accuracy', 'std_aucc', etc.
            first_row = next(reader, None)
            if not first_row:
                logger.warning(f"File {file_path} has headers but no data rows.")
                return True # Or False depending on strictness

            # Validate the structure of the data row against the schema's 'properties'
            # We treat the row as the object to validate
            is_valid, errors = validate_against_schema(first_row, schema)
            
            if not is_valid:
                logger.error(f"Validation failed for {file_path}: {errors}")
                return False
            
            logger.info(f"Validation passed for {file_path}")
            return True

    except Exception as e:
        logger.error(f"Error reading/validating {file_path}: {e}")
        return False

def validate_comparison_report(file_path: Path, schema: Dict[str, Any]) -> bool:
    """
    Validates the JSON comparison report.
    """
    if not file_path.exists():
        logger.error(f"File not found: {file_path}")
        return False

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        is_valid, errors = validate_against_schema(data, schema)
        
        if not is_valid:
            logger.error(f"Validation failed for {file_path}: {errors}")
            return False
        
        logger.info(f"Validation passed for {file_path}")
        return True

    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in {file_path}: {e}")
        return False
    except Exception as e:
        logger.error(f"Error reading/validating {file_path}: {e}")
        return False

def main():
    """
    Main entry point for T034: Validate results against aggregated_metrics.schema.yaml
    """
    logger.info("Starting validation of results against schema...")

    # 1. Load Schema
    if not SCHEMA_FILE.exists():
        logger.error(f"Schema file not found at {SCHEMA_FILE}")
        sys.exit(1)

    try:
        with open(SCHEMA_FILE, 'r', encoding='utf-8') as f:
            schema = yaml.safe_load(f)
        logger.info(f"Schema loaded successfully from {SCHEMA_FILE}")
    except Exception as e:
        logger.error(f"Failed to load schema: {e}")
        sys.exit(1)

    # 2. Validate CSVs (Baseline and CAP)
    csv_results = []
    for csv_path in [
        PROJECT_ROOT / "data" / "metrics" / "baseline_results.csv",
        PROJECT_ROOT / "data" / "metrics" / "cap_results.csv"
    ]:
        # We need to ensure the CSV structure matches the schema.
        # Since the schema is for 'aggregated_metrics', and CSVs contain rows,
        # we validate the row content.
        if csv_path.exists():
            success = validate_single_result_file(csv_path, schema)
            csv_results.append((csv_path.name, success))
        else:
            logger.warning(f"Expected file not found: {csv_path}")
            csv_results.append((csv_path.name, False))

    # 3. Validate JSON Report
    report_path = PROJECT_ROOT / "data" / "metrics" / "comparison_report.json"
    report_success = False
    if report_path.exists():
        report_success = validate_comparison_report(report_path, schema)
    else:
        logger.warning(f"Expected file not found: {report_path}")

    # 4. Summary
    all_passed = all(res for _, res in csv_results) and report_success

    print("\n--- Validation Summary ---")
    for name, res in csv_results:
        status = "PASS" if res else "FAIL"
        print(f"{name}: {status}")
    
    report_status = "PASS" if report_success else "FAIL"
    print(f"comparison_report.json: {report_status}")

    if all_passed:
        logger.info("All validations PASSED.")
        sys.exit(0)
    else:
        logger.error("Validation FAILED. Check logs for details.")
        sys.exit(1)

if __name__ == "__main__":
    main()