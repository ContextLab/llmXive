"""
CLI tool to enforce schema contracts on ingestion.

This script validates data artifacts against the contracts defined in
contracts/dataset.schema.yaml and contracts/output.schema.yaml.
It ensures that ingestion pipelines produce data compliant with
the project's internal contracts before downstream analysis proceeds.
"""

import argparse
import logging
import sys
from pathlib import Path
from typing import Optional

# Import project utilities and schemas
from src.utils.io_helpers import FatalError, load_json_strict, read_csv_strict
from src.config.schemas import (
    validate_dataset_schema,
    validate_regression_output,
    AnalysisDatasetRecord,
    RegressionOutput,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


def validate_csv_artifact(
    file_path: Path,
    schema_name: str = "dataset",
) -> bool:
    """
    Validate a CSV artifact against the dataset schema.

    Args:
        file_path: Path to the CSV file to validate.
        schema_name: Name of the schema to validate against (currently 'dataset').

    Returns:
        True if validation passes, False otherwise.

    Raises:
        FatalError: If the file does not exist or cannot be read.
    """
    logger.info(f"Validating CSV artifact: {file_path}")

    if not file_path.exists():
        raise FatalError(f"Artifact not found: {file_path}")

    try:
        # Read CSV strictly (raises on missing columns or type mismatches)
        df = read_csv_strict(file_path)
    except Exception as e:
        raise FatalError(f"Failed to read CSV strictly: {e}")

    if df.empty:
        logger.warning(f"CSV file {file_path} is empty. Skipping schema validation.")
        return True

    # Validate against the AnalysisDatasetRecord schema
    # Convert dataframe rows to dictionaries and validate each
    try:
        for idx, row in df.iterrows():
            record_dict = row.to_dict()
            # Pydantic validation
            AnalysisDatasetRecord(**record_dict)
    except Exception as e:
        logger.error(f"Schema validation failed for row {idx}: {e}")
        raise FatalError(f"Data in {file_path} does not conform to {schema_name} schema.")

    logger.info(f"Validation PASSED for {file_path} ({len(df)} records).")
    return True


def validate_json_artifact(
    file_path: Path,
    schema_name: str = "regression",
) -> bool:
    """
    Validate a JSON artifact against the regression output schema.

    Args:
        file_path: Path to the JSON file to validate.
        schema_name: Name of the schema to validate against (currently 'regression').

    Returns:
        True if validation passes, False otherwise.

    Raises:
        FatalError: If the file does not exist or cannot be read.
    """
    logger.info(f"Validating JSON artifact: {file_path}")

    if not file_path.exists():
        raise FatalError(f"Artifact not found: {file_path}")

    try:
        data = load_json_strict(file_path)
    except Exception as e:
        raise FatalError(f"Failed to read JSON strictly: {e}")

    if not data:
        logger.warning(f"JSON file {file_path} is empty. Skipping schema validation.")
        return True

    # Validate against RegressionOutput schema
    try:
        # Assume top-level structure matches RegressionOutput or list thereof
        if isinstance(data, list):
            for idx, item in enumerate(data):
                RegressionOutput(**item)
        else:
            RegressionOutput(**data)
    except Exception as e:
        logger.error(f"Schema validation failed: {e}")
        raise FatalError(f"Data in {file_path} does not conform to {schema_name} schema.")

    logger.info(f"Validation PASSED for {file_path}.")
    return True


def main() -> int:
    """
    Main entry point for the validation CLI.

    Returns:
        0 on success, 1 on failure.
    """
    parser = argparse.ArgumentParser(
        description="Enforce schema contracts on ingestion artifacts."
    )
    parser.add_argument(
        "--file",
        type=str,
        required=True,
        help="Path to the artifact file to validate (CSV or JSON).",
    )
    parser.add_argument(
        "--type",
        type=str,
        choices=["csv", "json", "auto"],
        default="auto",
        help="Type of the artifact. 'auto' infers from extension.",
    )
    parser.add_argument(
        "--schema",
        type=str,
        default="auto",
        help="Schema name to validate against. 'auto' infers from file path.",
    )

    args = parser.parse_args()

    file_path = Path(args.file)

    if not file_path.exists():
        logger.error(f"File not found: {file_path}")
        return 1

    # Infer type if auto
    if args.type == "auto":
        if file_path.suffix.lower() == ".csv":
            artifact_type = "csv"
        elif file_path.suffix.lower() in [".json", ".yaml", ".yml"]:
            artifact_type = "json"
        else:
            logger.error(f"Cannot infer artifact type for: {file_path}")
            return 1
    else:
        artifact_type = args.type

    # Infer schema if auto
    if args.schema == "auto":
        if "analysis_dataset" in file_path.name or "dataset" in file_path.name:
            schema_name = "dataset"
        elif "regression" in file_path.name or "model" in file_path.name:
            schema_name = "regression"
        else:
            logger.warning("Could not infer schema name. Defaulting to 'dataset'.")
            schema_name = "dataset"
    else:
        schema_name = args.schema

    try:
        if artifact_type == "csv":
          validate_csv_artifact(file_path, schema_name)
        else:
          validate_json_artifact(file_path, schema_name)
        return 0
    except FatalError as e:
        logger.error(f"Validation FAILED: {e}")
        return 1
    except Exception as e:
        logger.error(f"Unexpected error during validation: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())