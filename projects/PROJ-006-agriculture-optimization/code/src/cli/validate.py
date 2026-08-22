"""
CLI module to enforce schema contracts on ingestion artifacts.

This module provides strict validation for CSV and JSON artifacts
against the schema contracts defined in `contracts/` and `src/config/schemas.py`.
It is designed to be run as a CLI tool or imported as a library.

Usage:
    python -m src.cli.validate --input data/processed/analysis_dataset.csv --type csv
    python -m src.cli.validate --input data/processed/regression_results.json --type json
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import Optional, List, Dict, Any

# Importing from existing project utilities
from src.utils.io_helpers import FatalError, load_json_strict, read_csv_strict
from src.config.schemas import (
    validate_dataset_schema,
    validate_regression_output,
    AnalysisDatasetRecord,
    RegressionOutput
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def validate_csv_artifact(
    file_path: Path,
    schema_name: str = "dataset"
) -> bool:
    """
    Validates a CSV artifact against the specified schema contract.

    Args:
        file_path: Path to the CSV file.
        schema_name: Name of the schema to validate against ('dataset').

    Returns:
        True if validation passes, False otherwise.

    Raises:
        FatalError: If the file cannot be read or schema is invalid.
    """
    if not file_path.exists():
        raise FatalError(f"Artifact not found: {file_path}")

    logger.info(f"Validating CSV artifact: {file_path}")

    try:
        # Strict read ensures file is not empty and is valid CSV
        df = read_csv_strict(file_path)
        logger.info(f"Successfully read CSV. Rows: {len(df)}, Columns: {list(df.columns)}")

        # Validate against Pydantic schema row-by-row or bulk
        # The validate_dataset_schema function in src/config/schemas.py handles this
        if schema_name == "dataset":
            validation_results = validate_dataset_schema(df)
            if not validation_results.get("valid", False):
                errors = validation_results.get("errors", [])
                logger.error(f"Schema validation failed for {file_path}:")
                for err in errors:
                    logger.error(f"  - {err}")
                return False
            logger.info("CSV schema validation PASSED.")
            return True
        else:
            raise FatalError(f"Unknown CSV schema type: {schema_name}")

    except FatalError:
        # Re-raise FatalError directly
        raise
    except Exception as e:
        logger.error(f"Unexpected error during CSV validation: {e}", exc_info=True)
        raise FatalError(f"Validation failed due to internal error: {e}")


def validate_json_artifact(
    file_path: Path,
    schema_name: str = "regression"
) -> bool:
    """
    Validates a JSON artifact against the specified schema contract.

    Args:
        file_path: Path to the JSON file.
        schema_name: Name of the schema to validate against ('regression').

    Returns:
        True if validation passes, False otherwise.

    Raises:
        FatalError: If the file cannot be read or schema is invalid.
    """
    if not file_path.exists():
        raise FatalError(f"Artifact not found: {file_path}")

    logger.info(f"Validating JSON artifact: {file_path}")

    try:
        # Strict load ensures file is valid JSON
        data = load_json_strict(file_path)
        logger.info(f"Successfully loaded JSON. Keys: {list(data.keys()) if isinstance(data, dict) else 'List/Array'}")

        # Validate against Pydantic schema
        if schema_name == "regression":
            validation_results = validate_regression_output(data)
            if not validation_results.get("valid", False):
                errors = validation_results.get("errors", [])
                logger.error(f"Schema validation failed for {file_path}:")
                for err in errors:
                    logger.error(f"  - {err}")
                return False
            logger.info("JSON schema validation PASSED.")
            return True
        else:
            raise FatalError(f"Unknown JSON schema type: {schema_name}")

    except FatalError:
        # Re-raise FatalError directly
        raise
    except Exception as e:
        logger.error(f"Unexpected error during JSON validation: {e}", exc_info=True)
        raise FatalError(f"Validation failed due to internal error: {e}")


def main() -> int:
    """
    CLI entry point for schema validation.
    """
    parser = argparse.ArgumentParser(
        description="Enforce schema contracts on ingestion artifacts."
    )
    parser.add_argument(
        "--input",
        "-i",
        type=Path,
        required=True,
        help="Path to the artifact file (CSV or JSON) to validate."
    )
    parser.add_argument(
        "--type",
        "-t",
        choices=["csv", "json"],
        required=True,
        help="Type of the artifact (csv or json)."
    )
    parser.add_argument(
        "--schema",
        "-s",
        default="dataset",
        help="Specific schema contract to use (default: dataset for CSV, inferred for JSON)."
    )

    args = parser.parse_args()

    try:
        if args.type == "csv":
            success = validate_csv_artifact(args.input, args.schema)
        elif args.type == "json":
            success = validate_json_artifact(args.input, args.schema)
        else:
            # Should be caught by argparse choices, but defensive check
            raise FatalError(f"Unsupported type: {args.type}")

        if success:
            logger.info("Validation successful.")
            return 0
        else:
            logger.error("Validation failed.")
            return 1

    except FatalError as e:
        logger.critical(f"Fatal Error: {e}")
        return 2
    except Exception as e:
        logger.critical(f"Unhandled exception: {e}", exc_info=True)
        return 3


if __name__ == "__main__":
    sys.exit(main())
