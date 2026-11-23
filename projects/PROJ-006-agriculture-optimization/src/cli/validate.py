import argparse
import logging
import sys
import json
from pathlib import Path
from typing import Optional, List, Dict, Any

import pandas as pd
import yaml

from src.config.schemas import validate_dataset_schema, validate_regression_output
from src.utils.io_helpers import setup_logging, FatalError

logger = logging.getLogger(__name__)

def validate_csv_artifact(file_path: Path, schema_type: str = "dataset") -> bool:
    """
    Validates a CSV artifact against the specified schema.
    Currently supports 'dataset' schema type.
    """
    if not file_path.exists():
        raise FatalError(f"File not found: {file_path}")

    logger.info(f"Validating {file_path} against {schema_type} schema...")

    try:
        df = pd.read_csv(file_path)
        if schema_type == "dataset":
            is_valid, errors = validate_dataset_schema(df)
            if not is_valid:
                logger.error("Validation failed. Errors:")
                for err in errors:
                    logger.error(f"  - {err}")
                return False
            logger.info("Validation passed.")
            return True
        else:
            raise FatalError(f"Unsupported schema type for CSV: {schema_type}")
    except Exception as e:
        logger.exception(f"Error during validation: {e}")
        return False

def validate_json_artifact(file_path: Path, schema_type: str = "regression") -> bool:
    """
    Validates a JSON artifact against the specified schema.
    Currently supports 'regression' schema type.
    """
    if not file_path.exists():
        raise FatalError(f"File not found: {file_path}")

    logger.info(f"Validating {file_path} against {schema_type} schema...")

    try:
        with open(file_path, 'r') as f:
            data = json.load(f)

        if schema_type == "regression":
            is_valid, errors = validate_regression_output(data)
            if not is_valid:
                logger.error("Validation failed. Errors:")
                for err in errors:
                    logger.error(f"  - {err}")
                return False
            logger.info("Validation passed.")
            return True
        else:
            raise FatalError(f"Unsupported schema type for JSON: {schema_type}")
    except Exception as e:
        logger.exception(f"Error during validation: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Validate data artifacts against schema contracts.")
    parser.add_argument("file_path", type=str, help="Path to the file to validate.")
    parser.add_argument("--schema-type", choices=["dataset", "regression", "sensitivity"], required=True,
                        help="Type of schema to validate against.")
    parser.add_argument("--no-strict", action="store_true", help="Do not exit with error code on failure (for CI).")
    parser.add_argument("--log-level", choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], default="INFO",
                        help="Logging level.")

    args = parser.parse_args()

    setup_logging(level=args.log_level)

    file_path = Path(args.file_path)
    success = False

    if file_path.suffix.lower() == ".csv":
        success = validate_csv_artifact(file_path, args.schema_type)
    elif file_path.suffix.lower() == ".json":
        success = validate_json_artifact(file_path, args.schema_type)
    else:
        logger.error(f"Unsupported file extension: {file_path.suffix}")
        success = False

    if not success and not args.no_strict:
        sys.exit(1)
    elif success:
        sys.exit(0)
    else:
        # Failed but --no-strict was set
        sys.exit(0)

if __name__ == "__main__":
    main()
