"""
CLI tool to validate data artifacts against schema contracts.
Supports validation of CSV datasets and JSON regression outputs.
"""
import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Optional, List, Dict, Any

import pandas as pd
import yaml

# Local imports from existing API surface
from src.utils.io_helpers import setup_logging, load_json_strict, load_yaml
from src.config.schemas import (
    validate_dataset_schema,
    validate_regression_output,
    AnalysisDatasetRecord,
    RegressionOutput
)

def validate_csv_artifact(
    file_path: Path,
    schema_path: Path,
    schema_type: str,
    log_level: str = "INFO"
) -> bool:
    """
    Validate a CSV artifact against a dataset schema.
    
    Args:
        file_path: Path to the CSV file.
        schema_type: Type of schema to validate against ('dataset', 'regression', 'sensitivity').
        log_level: Logging level.

    Returns:
        True if validation passes, False otherwise.
    """
    logger = setup_logging("validate_cli", log_level)

    if not file_path.exists():
        logger.error(f"Input file not found: {file_path}")
        return False

    if schema_type != "dataset":
        logger.error(f"CSV validation only supports 'dataset' schema type. Got: {schema_type}")
        return False

    try:
        df = pd.read_csv(file_path)
        logger.info(f"Loaded CSV with {len(df)} rows and {len(df.columns)} columns")
        logger.info(f"Columns: {list(df.columns)}")

        # Validate against Pydantic schema
        validation_errors = validate_dataset_schema(df)

        if validation_errors:
            logger.error(f"Validation failed with {len(validation_errors)} errors:")
            for error in validation_errors:
                logger.error(f"  - {error}")
            return False

        logger.info("CSV validation passed successfully.")
        return True

    except Exception as e:
        logger.error(f"Error during CSV validation: {e}", exc_info=True)
        return False

    try:
        df = pd.read_csv(file_path)
    except Exception as e:
        logger.error(f"Failed to read CSV: {e}")
        return False

    # Dataset schema validation logic
    if schema_type == 'dataset':
        required_columns = schema.get('required_columns', [])
        column_types = schema.get('column_types', {})
        
        # Check columns
        missing_cols = [col for col in required_columns if col not in df.columns]
        if missing_cols:
            msg = f"Missing required columns: {missing_cols}"
            if strict:
                logger.error(msg)
                return False
            else:
                logger.warning(msg)
        
        # Check types (basic check)
        for col, expected_type in column_types.items():
            if col in df.columns:
                actual_type = str(df[col].dtype)
                # Simple mapping check
                type_map = {
                    'int': ['int64', 'int32'],
                    'float': ['float64', 'float32'],
                    'str': ['object', 'string'],
                    'bool': ['bool']
                }
                if expected_type in type_map:
                    if actual_type not in type_map[expected_type]:
                        msg = f"Column '{col}' expected {expected_type}, got {actual_type}"
                        if strict:
                            logger.error(msg)
                            return False
                        else:
                            logger.warning(msg)
        
        logger.info(f"CSV validation passed: {len(df)} rows, {len(df.columns)} columns")
        return True

    # Sensitivity schema validation logic
    elif schema_type == 'sensitivity':
        required_columns = ['threshold', 'model', 'coefficient', 'p_value', 'std_err']
        missing_cols = [col for col in required_columns if col not in df.columns]
        if missing_cols:
            msg = f"Missing required columns for sensitivity: {missing_cols}"
            if strict:
                logger.error(msg)
                return False
            else:
                logger.warning(msg)
        else:
            logger.info("Sensitivity CSV validation passed")
            return True

    return False


def validate_json_artifact(
    file_path: Path,
    schema_path: Path,
    schema_type: str,
    log_level: str = "INFO"
) -> bool:
    """
    Validate a JSON artifact against the specified schema.

    Args:
        file_path: Path to the JSON file.
        schema_type: Type of schema to validate against ('dataset', 'regression', 'sensitivity').
        log_level: Logging level.

    Returns:
        True if validation passes, False otherwise.
    """
    logger = setup_logging("validate_cli", log_level)

    if not file_path.exists():
        logger.error(f"Input file not found: {file_path}")
        return False

    if schema_type not in ["regression", "sensitivity"]:
        logger.error(f"JSON validation only supports 'regression' or 'sensitivity' schema types. Got: {schema_type}")
        return False

    try:
        data = load_json_strict(file_path)
        logger.info(f"Loaded JSON file: {file_path.name}")

        if schema_type == "regression":
            validation_errors = validate_regression_output(data)
            if validation_errors:
                logger.error(f"Regression validation failed with {len(validation_errors)} errors:")
                for error in validation_errors:
                    logger.error(f"  - {error}")
                return False
            logger.info("Regression JSON validation passed successfully.")

        elif schema_type == "sensitivity":
            # Basic structure check for sensitivity results
            required_keys = ["threshold", "model", "coefficient", "p_value"]
            if isinstance(data, list):
                if not all(all(key in row for key in required_keys) for row in data if isinstance(row, dict)):
                    logger.error(f"Sensitivity JSON missing required keys: {required_keys}")
                    return False
            logger.info("Sensitivity JSON validation passed successfully.")

        return True

    except Exception as e:
        logger.error(f"Error during JSON validation: {e}", exc_info=True)
        return False

def main() -> int:
    """
    Main entry point for the validation CLI.
    Returns exit code 0 on success, 1 on failure.
    """
    parser = argparse.ArgumentParser(
        description="Validate data artifacts against schema contracts.",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        "file_path",
        type=Path,
        help="Path to the artifact file (CSV or JSON) to validate."
    )

    parser.add_argument(
        "--schema-type",
        type=str,
        required=True,
        choices=["dataset", "regression", "sensitivity"],
        help="Type of schema to validate against: 'dataset' (for CSV), 'regression' or 'sensitivity' (for JSON)."
    )

    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging level (default: INFO)."
    )

    parser.add_argument(
        "--no-strict",
        action="store_true",
        help="Disable strict validation (currently unused, reserved for future)."
    )

    args = parser.parse_args()

    # Determine validation type based on file extension
    if args.file_path.suffix.lower() == ".csv":
        if args.schema_type != "dataset":
            print(f"Error: CSV files must be validated with --schema-type dataset. Got: {args.schema_type}")
            return 1
        success = validate_csv_artifact(args.file_path, args.schema_type, args.log_level)

    elif args.file_path.suffix.lower() in [".json", ".yaml", ".yml"]:
        if args.schema_type == "dataset":
            print(f"Error: JSON/YAML files cannot be validated with --schema-type dataset.")
            return 1
        success = validate_json_artifact(args.file_path, args.schema_type, args.log_level)

    else:
        print(f"Error: Unsupported file extension: {args.file_path.suffix}")
        return 1

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
