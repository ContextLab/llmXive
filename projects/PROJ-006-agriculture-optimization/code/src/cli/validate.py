import argparse
import json
import logging
import sys
from pathlib import Path
from typing import Optional, List, Dict, Any

import pandas as pd
import yaml
from pydantic import ValidationError

from src.config.schemas import (
    AnalysisDatasetRecord,
    RegressionOutput,
    SensitivityResult,
    validate_dataset_schema,
    validate_regression_output,
    validate_sensitivity_output,
)
from src.utils.io_helpers import setup_logging, read_csv_strict, load_json_strict


def validate_csv_artifact(
    file_path: Path, schema_type: str, logger: logging.Logger
) -> bool:
    """
    Validate a CSV artifact against the dataset schema.

    Args:
        file_path: Path to the CSV file.
        schema_type: Type of schema to validate against (must be 'dataset').
        logger: Logger instance.

    Returns:
        True if validation passes, False otherwise.
    """
    if schema_type != "dataset":
        logger.error(f"Invalid schema_type for CSV validation: {schema_type}")
        return False

    try:
        df = read_csv_strict(file_path)
        logger.info(f"Loaded CSV with {len(df)} rows and {len(df.columns)} columns")

        # Convert to list of dicts for pydantic validation
        records = df.to_dict(orient="records")

        # Validate each record against the schema
        valid_count = 0
        invalid_count = 0
        errors = []

        for i, record in enumerate(records):
            try:
                AnalysisDatasetRecord(**record)
                valid_count += 1
            except ValidationError as e:
                invalid_count += 1
                errors.append(f"Row {i}: {e}")
                if len(errors) >= 5:  # Limit error reporting
                    errors.append("... (truncated)")
                    break

        if invalid_count > 0:
            logger.error(f"Validation failed: {invalid_count} invalid rows out of {len(records)}")
            for err in errors:
                logger.error(err)
            return False
        else:
            logger.info(f"Validation passed: All {valid_count} rows conform to schema")
            return True

    except Exception as e:
        logger.error(f"Error reading or validating CSV file: {e}")
        return False


def validate_json_artifact(
    file_path: Path, schema_type: str, logger: logging.Logger
) -> bool:
    """
    Validate a JSON artifact against the appropriate schema.

    Args:
        file_path: Path to the JSON file.
        schema_type: Type of schema ('regression' or 'sensitivity').
        logger: Logger instance.

    Returns:
        True if validation passes, False otherwise.
    """
    try:
        data = load_json_strict(file_path)
        logger.info(f"Loaded JSON from {file_path}")

        if schema_type == "regression":
            result = validate_regression_output(data)
            if result:
                logger.info("Regression output validation passed")
                return True
            else:
                logger.error("Regression output validation failed")
                return False

        elif schema_type == "sensitivity":
            result = validate_sensitivity_output(data)
            if result:
                logger.info("Sensitivity output validation passed")
                return True
            else:
                logger.error("Sensitivity output validation failed")
                return False

        else:
            logger.error(f"Invalid schema_type for JSON validation: {schema_type}")
            return False

    except Exception as e:
        logger.error(f"Error reading or validating JSON file: {e}")
        return False


def main() -> int:
    """Main entry point for the validation CLI."""
    parser = argparse.ArgumentParser(
        description="Validate data artifacts against schema contracts."
    )
    parser.add_argument(
        "file_path",
        type=Path,
        help="Path to the file to validate (CSV or JSON).",
    )
    parser.add_argument(
        "--schema-type",
        type=str,
        required=True,
        choices=["dataset", "regression", "sensitivity"],
        help="Type of schema to validate against.",
    )
    parser.add_argument(
        "--no-strict",
        action="store_true",
        help="Do not use strict validation (not implemented yet).",
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Set the logging level.",
    )

    args = parser.parse_args()

    # Setup logging
    logger = setup_logging("validate", args.log_level)
    logger.info(f"Starting validation for {args.file_path} with schema type {args.schema_type}")

    if not args.file_path.exists():
        logger.error(f"File not found: {args.file_path}")
        return 1

    # Determine validation function based on file extension
    if args.file_path.suffix.lower() == ".csv":
        if args.schema_type != "dataset":
            logger.error("CSV files must be validated with --schema-type dataset")
            return 1
        success = validate_csv_artifact(args.file_path, args.schema_type, logger)
    elif args.file_path.suffix.lower() == ".json":
        if args.schema_type not in ["regression", "sensitivity"]:
            logger.error(
                "JSON files must be validated with --schema-type regression or sensitivity"
            )
            return 1
        success = validate_json_artifact(args.file_path, args.schema_type, logger)
    else:
        logger.error(f"Unsupported file extension: {args.file_path.suffix}")
        return 1

    if success:
        logger.info("Validation successful")
        return 0
    else:
        logger.error("Validation failed")
        return 1


if __name__ == "__main__":
    sys.exit(main())