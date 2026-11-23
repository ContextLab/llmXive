"""
Validation utilities for the llmXive pipeline.

This module implements strict schema validation for feature vectors and raw datasets
to enforce the Single Source of Truth principle.
"""
import os
import sys
import logging
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Union

import pandas as pd
import yaml
from pydantic import BaseModel, Field, ValidationError
from pydantic import create_model

# Local imports
from config import get_paths
from utils.errors import DataSchemaError, create_missing_dataset_error
from utils.logging import get_logger

logger = get_logger(__name__)


def load_schema(schema_path: str) -> Dict[str, Any]:
    """
    Load a JSON/YAML schema from disk.

    Args:
        schema_path: Path to the schema file.

    Returns:
        Dictionary containing the schema definition.

    Raises:
        FileNotFoundError: If the schema file does not exist.
        ValueError: If the schema is invalid JSON/YAML.
    """
    path = Path(schema_path)
    if not path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")

    with open(path, 'r', encoding='utf-8') as f:
        try:
            if path.suffix in ['.yaml', '.yml']:
                return yaml.safe_load(f)
            else:
                return json.load(f)
        except (json.JSONDecodeError, yaml.YAMLError) as e:
            raise ValueError(f"Invalid schema format in {schema_path}: {e}")


def _schema_to_pydantic_model(schema: Dict[str, Any], model_name: str = "DynamicSchema") -> type[BaseModel]:
    """
    Convert a JSON Schema dict into a Pydantic model dynamically.

    This allows us to validate DataFrames against the contract defined in YAML.
    """
    properties = schema.get('properties', {})
    required_fields = schema.get('required', [])

    field_definitions = {}
    for field_name, field_schema in properties.items():
        field_type = field_schema.get('type', 'string')
        description = field_schema.get('description', '')

        # Map JSON Schema types to Python types
        if field_type == 'string':
            py_type = str
        elif field_type == 'integer':
            py_type = int
        elif field_type == 'number':
            py_type = float
        elif field_type == 'boolean':
            py_type = bool
        else:
            py_type = Any

        # Determine if optional or required
        if field_name in required_fields:
            field_definitions[field_name] = (py_type, Field(..., description=description))
        else:
            field_definitions[field_name] = (Optional[py_type], Field(None, description=description))

    return create_model(model_name, **field_definitions)


def validate_dataframe(df: pd.DataFrame, schema: Dict[str, Any]) -> None:
    """
    Validate a DataFrame against a JSON Schema using Pydantic.

    Args:
        df: The DataFrame to validate.
        schema: The schema definition.

    Raises:
        ValueError: If the DataFrame does not match the schema.
        DataSchemaError: If required columns are missing.
    """
    required_cols = schema.get('required', [])
    missing_cols = [col for col in required_cols if col not in df.columns]

    if missing_cols:
        raise DataSchemaError(f"Missing required columns in DataFrame: {missing_cols}")

    # Check for extra columns not in schema (optional strictness, usually we just check required)
    # For this task, we focus on required structure and types.

    model_class = _schema_to_pydantic_model(schema)

    # Convert DataFrame to list of dicts for validation
    # We only validate the rows that are present
    try:
        for idx, row in df.iterrows():
            # Filter row to only include schema properties to avoid extra key errors
            # unless the schema allows 'additionalProperties': true (which we assume not for strict contracts)
            row_dict = {k: v for k, v in row.items() if k in schema.get('properties', {})}
            model_class(**row_dict)
    except ValidationError as e:
        raise ValueError(f"DataFrame validation failed: {e}")


def validate_raw_dataset_availability(raw_data_path: str, required_columns: List[str]) -> None:
    """
    Validate that the raw dataset exists and contains required columns.

    This implements FR-003: Validate raw dataset availability and 'human_rating' column presence.

    Args:
        raw_data_path: Path to the raw parquet file.
        required_columns: List of column names that must exist.

    Raises:
        DataSchemaError: If file is missing or columns are absent.
    """
    path = Path(raw_data_path)
    if not path.exists():
        raise DataSchemaError(f"Raw dataset not found at: {raw_data_path}")

    try:
        # Read just the schema/columns to avoid loading full data if huge
        # Using pyarrow or pandas with nrows=0 is efficient
        df = pd.read_parquet(path, columns=required_columns[:1]) # Read minimal to check existence
        available_cols = set(df.columns)

        missing = [col for col in required_columns if col not in available_cols]
        if missing:
            # Format error message per T004b requirement
            # Assuming the source is 'pick-a-pic' based on context
            raise DataSchemaError(f"Missing required dataset or column: pick-a-pic/{missing[0]}")

    except Exception as e:
        if isinstance(e, DataSchemaError):
            raise
        raise DataSchemaError(f"Failed to validate raw dataset at {raw_data_path}: {e}")


def validate_feature_vector_schema(df: pd.DataFrame) -> None:
    """
    Main entry point for validating the feature vector DataFrame.

    1. Loads the contract from `specs/.../contracts/feature_vector.schema.yaml`.
    2. Validates the DataFrame structure and types.
    3. Validates the raw dataset availability (human_rating) before feature validation.

    Args:
        df: The DataFrame containing extracted features.

    Raises:
        ValueError: If validation fails.
        DataSchemaError: If raw data requirements are not met.
    """
    paths = get_paths()
    schema_path = paths.project_root / "specs" / "001-llmxive-follow-up-extending-lens-rethink" / "contracts" / "feature_vector.schema.yaml"
    raw_data_path = paths.project_root / "data" / "raw" / "pick-a-pic.parquet"

    logger.info(f"Validating feature vector schema against {schema_path}")

    # 1. Validate Raw Dataset Availability (FR-003)
    # We must ensure the source data had 'human_rating' before we trust the features derived from it
    # even though features might not directly contain it, the pipeline integrity depends on it.
    validate_raw_dataset_availability(str(raw_data_path), ['human_rating'])

    # 2. Load Schema
    schema = load_schema(str(schema_path))

    # 3. Validate DataFrame
    validate_dataframe(df, schema)

    logger.info("Feature vector schema validation passed.")


def main() -> None:
    """
    CLI entry point for T018a.

    Loads the processed features CSV (produced by T017/T018b),
    validates it against the schema, and exits.
    """
    paths = get_paths()
    features_path = paths.project_root / "data" / "processed" / "features.csv"

    if not features_path.exists():
        logger.error(f"Features file not found: {features_path}")
        logger.error("Run code/data/features.py first to generate features.")
        sys.exit(1)

    try:
        logger.info(f"Loading features from {features_path}")
        df = pd.read_csv(features_path)

        logger.info(f"Loaded {len(df)} rows. Validating...")
        validate_feature_vector_schema(df)

        logger.info("SUCCESS: All validations passed.")
        sys.exit(0)

    except DataSchemaError as e:
        logger.critical(f"Data Schema Error: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.critical(f"Validation Error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.exception(f"Unexpected error during validation: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
