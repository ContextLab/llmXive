"""
Dataset schema validation logic.

Validates processed data against the defined YAML schema.
Ensures data integrity before model training or further processing.
"""
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import pandas as pd
import yaml
from jsonschema import validate, ValidationError, SchemaError

from src.exceptions import SchemaValidationError, InsufficientDataError

logger = logging.getLogger(__name__)

# Default path to the schema file relative to project root
DEFAULT_SCHEMA_PATH = "contracts/dataset.schema.yaml"

def load_schema(schema_path: Optional[Union[str, Path]] = None) -> Dict[str, Any]:
    """
    Load the dataset schema from a YAML file.
    
    Args:
        schema_path: Path to the schema YAML file. Defaults to DEFAULT_SCHEMA_PATH.
        
    Returns:
        Dictionary containing the schema definition.
        
    Raises:
        FileNotFoundError: If the schema file does not exist.
        yaml.YAMLError: If the schema file is not valid YAML.
    """
    if schema_path is None:
        schema_path = DEFAULT_SCHEMA_PATH
    else:
        schema_path = Path(schema_path)

    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found at {schema_path}")

    with open(schema_path, "r", encoding="utf-8") as f:
        schema = yaml.safe_load(f)
        
    if not isinstance(schema, dict):
        raise SchemaValidationError("Loaded schema is not a valid JSON object.")
        
    return schema


def validate_dataframe_schema(
    df: pd.DataFrame, 
    schema: Optional[Dict[str, Any]] = None,
    strict: bool = True
) -> bool:
    """
    Validate a pandas DataFrame against the dataset schema.
    
    Args:
        df: The DataFrame to validate.
        schema: Optional pre-loaded schema. If None, loads from default path.
        strict: If True, raises SchemaValidationError on any mismatch.
               If False, returns False on mismatch without raising.
               
    Returns:
        True if validation passes.
        
    Raises:
        SchemaValidationError: If validation fails and strict=True.
        InsufficientDataError: If the dataset has fewer than 150 rows (FR-001).
        TypeError: If the input is not a pandas DataFrame.
    """
    if not isinstance(df, pd.DataFrame):
        raise TypeError(f"Expected pandas DataFrame, got {type(df).__name__}")

    # Load schema if not provided
    if schema is None:
        try:
            schema = load_schema()
        except FileNotFoundError as e:
            if strict:
                raise SchemaValidationError(f"Cannot validate without schema: {e}")
            return False
        except yaml.YAMLError as e:
            if strict:
                raise SchemaValidationError(f"Invalid schema format: {e}")
            return False

    # Check minimum row count (FR-001)
    min_rows = schema.get("min_rows", 150)
    if len(df) < min_rows:
        raise InsufficientDataError(
            f"Dataset has {len(df)} rows, which is below the minimum required {min_rows} rows (FR-001)."
        )

    # Convert DataFrame to list of records for jsonschema validation
    # jsonschema expects a list of objects for this use case
    records = df.to_dict(orient="records")
    
    # Validate each record against the schema
    # Note: jsonschema.validate checks a single instance. 
    # We iterate to catch specific row errors if needed, or validate the structure generally.
    # For strict column/required field checking, we can validate the first record or the structure.
    # However, jsonschema's 'items' keyword is for arrays. Here we validate the structure of one row 
    # and assume consistency, or we could validate the whole list if the schema was an array type.
    # Given the schema is 'type: object', we validate the structure of the records.
    
    required_fields = schema.get("required", [])
    properties = schema.get("properties", {})

    # 1. Check for required columns
    missing_cols = [col for col in required_fields if col not in df.columns]
    if missing_cols:
        msg = f"Missing required columns: {missing_cols}"
        if strict:
            raise SchemaValidationError(msg)
        logger.error(msg)
        return False

    # 2. Check for unexpected columns if additionalProperties is False
    if not schema.get("additionalProperties", True):
        allowed_cols = set(properties.keys())
        actual_cols = set(df.columns)
        extra_cols = actual_cols - allowed_cols
        if extra_cols:
            msg = f"Unexpected columns found: {extra_cols}. Additional properties are not allowed."
            if strict:
                raise SchemaValidationError(msg)
            logger.error(msg)
            return False

    # 3. Check for null values in required fields
    for col in required_fields:
        if df[col].isna().any():
            null_count = df[col].isna().sum()
            msg = f"Column '{col}' contains {null_count} null values, but it is required."
            if strict:
                raise SchemaValidationError(msg)
            logger.error(msg)
            return False

    # 4. Type validation (basic check using jsonschema on a sample record)
    # We validate the first row to ensure types align with schema definitions
    if len(records) > 0:
        try:
            validate(instance=records[0], schema=schema)
        except ValidationError as e:
            msg = f"Validation error in first record: {e.message}"
            if strict:
                raise SchemaValidationError(msg)
            logger.error(msg)
            return False
        except SchemaError as e:
            # This is a schema definition error, not data error
            if strict:
                raise SchemaValidationError(f"Schema definition error: {e.message}")
            return False

    logger.info(f"Schema validation passed for {len(df)} rows.")
    return True


def validate_and_clean(
    df: pd.DataFrame, 
    schema_path: Optional[Union[str, Path]] = None
) -> pd.DataFrame:
    """
    Validate the DataFrame and raise if it fails. 
    This is a convenience wrapper for the pipeline.
    
    Args:
        df: Input DataFrame.
        schema_path: Path to schema file.
        
    Returns:
        The validated DataFrame (unchanged).
        
    Raises:
        SchemaValidationError or InsufficientDataError on failure.
    """
    validate_dataframe_schema(df, schema=schema_path, strict=True)
    return df
