"""
Schema validation utilities for the GENEB sequence feature pipeline.

This module provides functions to validate data against the JSON Schema
defined in specs/001-gene-regulation/contracts/dataset.schema.yaml.
It ensures that feature extraction outputs conform to the expected structure,
types, and constraints (e.g., excluding 'at_content', enforcing float ranges).
"""
import json
import os
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import yaml

# Try to import jsonschema, but handle missing dependency gracefully
try:
    import jsonschema
    from jsonschema import validate, ValidationError as JsonSchemaValidationError
except ImportError:
    # If jsonschema is not installed, we cannot validate.
    # This should ideally be caught by requirements.txt, but we handle it here.
    jsonschema = None
    JsonSchemaValidationError = Exception  # type: ignore


from utils.logging import get_logger, PipelineError, ValidationError

logger = get_logger(__name__)

SCHEMA_PATH = Path("specs/001-gene-regulation/contracts/dataset.schema.yaml")


def load_schema(schema_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Load the JSON Schema from the YAML file.

    Args:
        schema_path: Path to the schema file. Defaults to SCHEMA_PATH.

    Returns:
        The schema dictionary.

    Raises:
        PipelineError: If the schema file cannot be found or loaded.
    """
    path = schema_path or SCHEMA_PATH
    if not path.exists():
        raise PipelineError(f"Schema file not found at {path}")

    try:
        with open(path, "r", encoding="utf-8") as f:
            schema = yaml.safe_load(f)
        if not isinstance(schema, dict):
            raise PipelineError(f"Schema at {path} is not a valid YAML dictionary.")
        return schema
    except yaml.YAMLError as e:
        raise PipelineError(f"Failed to parse schema YAML: {e}")


def validate_record(record: Dict[str, Any], schema: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate a single data record against the schema.

    Args:
        record: The data record (dictionary) to validate.
        schema: The JSON Schema to validate against.

    Returns:
        A tuple (is_valid, errors).
        is_valid: True if the record is valid.
        errors: A list of error messages if invalid.
    """
    if jsonschema is None:
        raise PipelineError("jsonschema library is not installed. Cannot validate.")

    errors = []
    try:
        validate(instance=record, schema=schema)
        return True, []
    except JsonSchemaValidationError as e:
        errors.append(f"Schema validation failed: {e.message} (Path: {list(e.path)})")
        return False, errors


def validate_dataset(
    records: List[Dict[str, Any]],
    schema: Optional[Dict[str, Any]] = None,
    fail_fast: bool = False
) -> Tuple[bool, List[str]]:
    """
    Validate a list of records (dataset) against the schema.

    Args:
        records: List of data records to validate.
        schema: Optional pre-loaded schema. If None, loads from default path.
        fail_fast: If True, stop at the first invalid record.

    Returns:
        A tuple (is_valid, errors).
        is_valid: True if all records are valid.
        errors: A list of error messages.
    """
    if schema is None:
        schema = load_schema()

    all_errors = []
    valid_count = 0
    invalid_count = 0

    for i, record in enumerate(records):
        is_valid, record_errors = validate_record(record, schema)
        if is_valid:
            valid_count += 1
        else:
            invalid_count += 1
            all_errors.extend([f"Record {i}: {err}" for err in record_errors])
            if fail_fast:
                break

    logger.info(f"Validation complete: {valid_count} valid, {invalid_count} invalid.")

    if invalid_count > 0:
        return False, all_errors
    return True, []


def validate_file(
    file_path: Path,
    schema: Optional[Dict[str, Any]] = None,
    fail_fast: bool = False
) -> Tuple[bool, List[str]]:
    """
    Validate a CSV or JSON file against the schema.

    For CSV, it assumes the first row is headers and converts each row to a dict.
    For JSON, it assumes a list of objects.

    Args:
        file_path: Path to the file.
        schema: Optional pre-loaded schema.
        fail_fast: If True, stop at the first invalid record.

    Returns:
        A tuple (is_valid, errors).
    """
    if not file_path.exists():
        raise PipelineError(f"File not found: {file_path}")

    if schema is None:
        schema = load_schema()

    records = []
    extension = file_path.suffix.lower()

    try:
        if extension == ".csv":
            import pandas as pd
            df = pd.read_csv(file_path)
            records = df.to_dict(orient="records")
        elif extension == ".json":
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    records = data
                else:
                    records = [data]
        else:
            raise PipelineError(f"Unsupported file extension: {extension}")
    except Exception as e:
        raise PipelineError(f"Failed to read file {file_path}: {e}")

    return validate_dataset(records, schema, fail_fast)


def ensure_schema_exists() -> bool:
    """
    Checks if the schema file exists.

    Returns:
        True if the schema exists, False otherwise.
    """
    return SCHEMA_PATH.exists()
