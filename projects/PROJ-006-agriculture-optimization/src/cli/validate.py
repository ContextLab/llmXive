"""
CLI tool to enforce schema contracts on ingestion artifacts.

This module validates CSV and JSON artifacts against the schema contracts
defined in `contracts/` and `src/config/schemas.py`. It ensures data integrity
before downstream processing steps.
"""
import argparse
import logging
import sys
from pathlib import Path
from typing import Optional, List, Dict, Any

# Import strict I/O utilities
from src.utils.io_helpers import FatalError, IntegrityError, load_json_strict, read_csv_strict
# Import schema validation logic
from src.config.schemas import validate_dataset_schema, validate_regression_output
from src.config.constants import PROJECT_ROOT

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def validate_csv_artifact(
    file_path: Path,
    schema_type: str = "dataset",
    strict: bool = True
) -> Dict[str, Any]:
    """
    Validate a CSV artifact against a specific schema contract.

    Args:
        file_path: Path to the CSV file.
        schema_type: Type of schema to validate against ('dataset' or 'regression').
                     Currently only 'dataset' is supported for CSVs.
        strict: If True, raise FatalError on validation failure.

    Returns:
        Dict containing validation results (passed, errors, row_count).

    Raises:
        FatalError: If file is missing, unreadable, or fails strict validation.
        IntegrityError: If schema validation fails but strict=False.
    """
    if not file_path.exists():
        msg = f"Artifact file not found: {file_path}"
        logger.error(msg)
        if strict:
            raise FatalError(msg)
        return {"passed": False, "errors": [msg], "row_count": 0}

    logger.info(f"Validating CSV artifact: {file_path}")
    try:
        df = read_csv_strict(file_path)
    except IntegrityError as e:
        msg = f"Failed to read CSV with strict integrity checks: {e}"
        logger.error(msg)
        if strict:
            raise FatalError(msg)
        return {"passed": False, "errors": [str(e)], "row_count": 0}

    if df.empty:
        msg = "CSV file is empty or contains no valid data rows."
        logger.warning(msg)
        if strict:
            raise FatalError(msg)
        return {"passed": False, "errors": [msg], "row_count": 0}

    errors = []
    if schema_type == "dataset":
        try:
            validate_dataset_schema(df)
            logger.info(f"Dataset schema validation passed for {file_path} ({len(df)} rows).")
            return {"passed": True, "errors": [], "row_count": len(df)}
        except IntegrityError as e:
            errors.append(str(e))
    else:
        errors.append(f"Unsupported schema type for CSV: {schema_type}")

    if errors:
        msg = f"Schema validation failed: {errors}"
        logger.error(msg)
        if strict:
            raise FatalError(msg)
        raise IntegrityError(msg)

    return {"passed": False, "errors": ["Unknown validation state"], "row_count": len(df)}

def validate_json_artifact(
    file_path: Path,
    schema_type: str = "regression",
    strict: bool = True
) -> Dict[str, Any]:
    """
    Validate a JSON artifact against a specific schema contract.

    Args:
        file_path: Path to the JSON file.
        schema_type: Type of schema ('regression' or 'sensitivity').
        strict: If True, raise FatalError on validation failure.

    Returns:
        Dict containing validation results.

    Raises:
        FatalError: If file is missing, unreadable, or fails strict validation.
        IntegrityError: If schema validation fails but strict=False.
    """
    if not file_path.exists():
        msg = f"Artifact file not found: {file_path}"
        logger.error(msg)
        if strict:
            raise FatalError(msg)
        return {"passed": False, "errors": [msg], "row_count": 0}

    logger.info(f"Validating JSON artifact: {file_path}")
    try:
        data = load_json_strict(file_path)
    except IntegrityError as e:
        msg = f"Failed to read JSON with strict integrity checks: {e}"
        logger.error(msg)
        if strict:
            raise FatalError(msg)
        return {"passed": False, "errors": [str(e)], "row_count": 0}

    errors = []
    if schema_type == "regression":
        try:
            validate_regression_output(data)
            logger.info(f"Regression output schema validation passed for {file_path}.")
            return {"passed": True, "errors": [], "row_count": 1} # JSON is a single object
        except IntegrityError as e:
            errors.append(str(e))
    else:
        errors.append(f"Unsupported schema type for JSON: {schema_type}")

    if errors:
        msg = f"Schema validation failed: {errors}"
        logger.error(msg)
        if strict:
            raise FatalError(msg)
        raise IntegrityError(msg)

    return {"passed": False, "errors": ["Unknown validation state"], "row_count": 1}

def main():
    """CLI entry point for schema validation."""
    parser = argparse.ArgumentParser(
        description="Enforce schema contracts on ingestion artifacts.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument(
        "file_path",
        type=str,
        help="Path to the artifact file (CSV or JSON) to validate."
    )
    parser.add_argument(
        "--schema-type",
        type=str,
        choices=["dataset", "regression", "sensitivity"],
        default="dataset",
        help="Type of schema contract to enforce."
    )
    parser.add_argument(
        "--no-strict",
        action="store_true",
        help="Do not raise FatalError on validation failure; return status code 1 instead."
    )

    args = parser.parse_args()
    file_path = Path(args.file_path)

    if not file_path.is_absolute():
        file_path = PROJECT_ROOT / file_path

    strict = not args.no_strict
    result = {}

    try:
        if file_path.suffix.lower() == ".csv":
            result = validate_csv_artifact(file_path, args.schema_type, strict)
        elif file_path.suffix.lower() in [".json", ".yaml", ".yml"]:
            # For JSON/YAML, we usually validate against regression output
            # unless specified otherwise.
            schema = args.schema_type if args.schema_type != "dataset" else "regression"
            result = validate_json_artifact(file_path, schema, strict)
        else:
            msg = f"Unsupported file extension: {file_path.suffix}"
            logger.error(msg)
            if strict:
                raise FatalError(msg)
            result = {"passed": False, "errors": [msg], "row_count": 0}

        if result["passed"]:
            print(f"VALIDATION PASSED: {file_path}")
            sys.exit(0)
        else:
            print(f"VALIDATION FAILED: {file_path}")
            for err in result.get("errors", []):
                print(f"  - {err}")
            sys.exit(1)

    except FatalError as e:
        print(f"FATAL ERROR: {e}")
        sys.exit(1)
    except IntegrityError as e:
        # Should be caught by validate functions, but handle just in case
        print(f"INTEGRITY ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
