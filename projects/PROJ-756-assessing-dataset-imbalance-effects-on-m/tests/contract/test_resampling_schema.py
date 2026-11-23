"""
Contract test for resampling logic (T020).
Validates that the resampling pipeline output and configuration adhere to
the constraints defined in contracts/resampling.schema.yaml.

Specifically checks:
1. The existence and schema of the output CSV (results/resampling_cv_metrics.csv).
2. The CV constraints: real-data CV <= 0.10 and combined CV <= 0.30.
"""
import os
import sys
import csv
import json
import logging
from pathlib import Path
from typing import Dict, Any, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Project root detection
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
CONTRACTS_DIR = PROJECT_ROOT / "contracts"
RESULTS_DIR = PROJECT_ROOT / "results"
SCHEMA_PATH = CONTRACTS_DIR / "resampling.schema.yaml"
OUTPUT_CSV_PATH = RESULTS_DIR / "resampling_cv_metrics.csv"

def load_schema(schema_path: Path) -> Dict[str, Any]:
    """Load the YAML schema definition."""
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    import yaml
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

def validate_csv_schema(csv_path: Path, schema: Dict[str, Any]) -> bool:
    """
    Validate that the CSV file exists and matches the schema definition.
    Checks column names and basic types.
    """
    if not csv_path.exists():
        logger.error(f"Output CSV not found: {csv_path}")
        return False

    required_columns = schema.get("required_columns", [])
    expected_types = schema.get("expected_types", {})

    with open(csv_path, 'r', newline='') as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames

        if headers is None:
            logger.error("CSV file is empty or has no headers.")
            return False

        # Check required columns
        missing_cols = set(required_columns) - set(headers)
        if missing_cols:
            logger.error(f"Missing required columns: {missing_cols}")
            return False

        # Read first row to validate types (basic check)
        try:
            row = next(reader)
            for col, expected_type in expected_types.items():
                if col in row:
                    val = row[col]
                    if expected_type == "float":
                        float(val)
                    elif expected_type == "int":
                        int(val)
                    elif expected_type == "string":
                        if not isinstance(val, str):
                            raise ValueError(f"Column {col} is not a string")
            logger.info("CSV schema validation passed.")
            return True
        except StopIteration:
            logger.warning("CSV file has headers but no data rows.")
            return True # Schema is valid, just empty
        except ValueError as e:
            logger.error(f"Type validation failed: {e}")
            return False

def validate_cv_constraints(csv_path: Path, schema: Dict[str, Any]) -> bool:
    """
    Validate the specific CV constraints defined in the schema.
    Constraints usually look like:
    - real_data_cv <= 0.10
    - combined_cv <= 0.30
    """
    if not csv_path.exists():
        return False

    constraints = schema.get("constraints", [])
    if not constraints:
        logger.warning("No constraints defined in schema.")
        return True

    passed = True
    with open(csv_path, 'r', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            for constraint in constraints:
                column = constraint.get("column")
                max_value = constraint.get("max_value")
                min_value = constraint.get("min_value")

                if column and column in row:
                    try:
                        val = float(row[column])
                        
                        if max_value is not None and val > max_value:
                            logger.error(
                                f"Constraint failed: {column}={val} exceeds max {max_value}"
                            )
                            passed = False
                        
                        if min_value is not None and val < min_value:
                            logger.error(
                                f"Constraint failed: {column}={val} is below min {min_value}"
                            )
                            passed = False
                    except ValueError:
                        logger.error(f"Could not parse float for {column}: {row[column]}")
                        passed = False

    if passed:
        logger.info("CV constraints validation passed.")
    return passed

def run_t020_contract_test() -> bool:
    """
    Main entry point for T020.
    Returns True if all validations pass, False otherwise.
    """
    logger.info(f"Starting T020 Contract Test for Resampling Logic.")
    logger.info(f"Project Root: {PROJECT_ROOT}")
    logger.info(f"Schema Path: {SCHEMA_PATH}")
    logger.info(f"Output CSV Path: {OUTPUT_CSV_PATH}")

    # 1. Ensure schema exists
    if not SCHEMA_PATH.exists():
        logger.error(f"Schema file missing: {SCHEMA_PATH}")
        logger.error("Run T010b to generate contracts/resampling.schema.yaml first.")
        return False

    # 2. Load schema
    try:
        schema = load_schema(SCHEMA_PATH)
    except Exception as e:
        logger.error(f"Failed to load schema: {e}")
        return False

    # 3. Validate CSV Schema
    schema_valid = validate_csv_schema(OUTPUT_CSV_PATH, schema)
    if not schema_valid:
        logger.error("CSV Schema validation failed.")
        return False

    # 4. Validate CV Constraints
    constraints_valid = validate_cv_constraints(OUTPUT_CSV_PATH, schema)
    if not constraints_valid:
        logger.error("CV Constraints validation failed.")
        return False

    logger.info("T020 Contract Test PASSED.")
    return True

def main():
    success = run_t020_contract_test()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()