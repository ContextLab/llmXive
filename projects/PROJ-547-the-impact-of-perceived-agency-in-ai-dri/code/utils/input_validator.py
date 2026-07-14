"""
Input validation utilities for the pipeline.

Provides functions to validate file paths, extensions, MIME types, and JSON/YAML
schemas, ensuring that all inputs conform to expected formats and structures.
"""

from __future__ import annotations

import json
import mimetypes
import os
from pathlib import Path
from typing import Any, Dict, Optional, Union

import yaml
from jsonschema import validate, ValidationError

from logging.pipeline_logger import get_logger
from utils.error_handler import PipelineError


def validate_file_path(
    path: Union[str, Path], must_exist: bool = True, must_be_file: bool = True
) -> Path:
    """
    Validate a file path.

    Args:
        path: The path to validate.
        must_exist: If True, the path must exist. Default is True.
        must_be_file: If True, the path must be a file (not a directory). Default is True.

    Returns:
        The validated Path object.

    Raises:
        PipelineError: If the path is invalid.
    """
    logger = get_logger()
    path_obj = Path(path)

    if must_exist and not path_obj.exists():
        error_msg = f"Path does not exist: {path_obj}"
        logger.error(error_msg)
        raise PipelineError(error_msg)

    if must_be_file and not path_obj.is_file():
        error_msg = f"Path is not a file: {path_obj}"
        logger.error(error_msg)
        raise PipelineError(error_msg)

    logger.debug(f"Validated file path: {path_obj}")
    return path_obj


def validate_file_extension(
    path: Union[str, Path], allowed_extensions: list[str]
) -> None:
    """
    Validate that a file has one of the allowed extensions.

    Args:
        path: The path to validate.
        allowed_extensions: List of allowed extensions (e.g., ['.csv', '.json']).

    Raises:
        PipelineError: If the file extension is not allowed.
    """
    logger = get_logger()
    path_obj = Path(path)
    ext = path_obj.suffix.lower()

    if ext not in allowed_extensions:
        error_msg = (
            f"File extension '{ext}' not allowed. "
            f"Allowed extensions: {allowed_extensions}"
        )
        logger.error(error_msg)
        raise PipelineError(error_msg)

    logger.debug(f"Validated file extension: {ext}")


def validate_file_mime_type(
    path: Union[str, Path], allowed_mime_types: list[str]
) -> None:
    """
    Validate that a file has one of the allowed MIME types.

    Args:
        path: The path to validate.
        allowed_mime_types: List of allowed MIME types (e.g., ['text/csv', 'application/json']).

    Raises:
        PipelineError: If the file MIME type is not allowed.
    """
    logger = get_logger()
    path_obj = Path(path)

    mime_type, _ = mimetypes.guess_type(str(path_obj))

    if mime_type is None:
        error_msg = f"Could not determine MIME type for: {path_obj}"
        logger.error(error_msg)
        raise PipelineError(error_msg)

    if mime_type not in allowed_mime_types:
        error_msg = (
            f"MIME type '{mime_type}' not allowed. "
            f"Allowed MIME types: {allowed_mime_types}"
        )
        logger.error(error_msg)
        raise PipelineError(error_msg)

    logger.debug(f"Validated MIME type: {mime_type}")


def validate_json_schema(
    data: Dict[str, Any], schema: Dict[str, Any]
) -> None:
    """
    Validate data against a JSON schema.

    Args:
        data: The data to validate.
        schema: The JSON schema to validate against.

    Raises:
        PipelineError: If the data does not conform to the schema.
    """
    logger = get_logger()

    try:
        validate(instance=data, schema=schema)
        logger.debug("Data validated against JSON schema")
    except ValidationError as e:
        error_msg = f"Data does not conform to schema: {e.message}"
        logger.error(error_msg)
        raise PipelineError(error_msg) from e


def load_and_validate_yaml(
    path: Union[str, Path], schema: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Load and optionally validate a YAML file.

    Args:
        path: Path to the YAML file.
        schema: Optional JSON schema to validate the loaded data against.

    Returns:
        The loaded data as a dictionary.

    Raises:
        PipelineError: If the file cannot be loaded or does not conform to the schema.
    """
    logger = get_logger()
    path_obj = validate_file_path(path)

    try:
        with open(path_obj, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        error_msg = f"Failed to parse YAML file: {path_obj}"
        logger.error(error_msg)
        raise PipelineError(error_msg) from e
    except Exception as e:
        error_msg = f"Failed to read YAML file: {path_obj}"
        logger.error(error_msg)
        raise PipelineError(error_msg) from e

    if not isinstance(data, dict):
        error_msg = f"YAML file does not contain a dictionary: {path_obj}"
        logger.error(error_msg)
        raise PipelineError(error_msg)

    if schema is not None:
        validate_json_schema(data, schema)

    logger.debug(f"Loaded and validated YAML file: {path_obj}")
    return data


def validate_json_file(
    path: Union[str, Path], schema: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Validate a JSON file and optionally check against a schema.

    Args:
        path: Path to the JSON file.
        schema: Optional JSON schema to validate the loaded data against.

    Returns:
        The loaded data as a dictionary.

    Raises:
        PipelineError: If the file cannot be loaded or does not conform to the schema.
    """
    logger = get_logger()
    path_obj = validate_file_path(path)
    validate_file_extension(path_obj, [".json"])

    try:
        with open(path_obj, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        error_msg = f"Failed to parse JSON file: {path_obj}"
        logger.error(error_msg)
        raise PipelineError(error_msg) from e
    except Exception as e:
        error_msg = f"Failed to read JSON file: {path_obj}"
        logger.error(error_msg)
        raise PipelineError(error_msg) from e

    if not isinstance(data, dict):
        error_msg = f"JSON file does not contain a dictionary: {path_obj}"
        logger.error(error_msg)
        raise PipelineError(error_msg)

    if schema is not None:
        validate_json_schema(data, schema)

    logger.debug(f"Validated JSON file: {path_obj}")
    return data


def validate_csv_file(
    path: Union[str, Path], required_columns: Optional[list[str]] = None
) -> list[str]:
    """
    Validate a CSV file and check for required columns.

    Args:
        path: Path to the CSV file.
        required_columns: Optional list of required column names.

    Returns:
        List of column names in the CSV file.

    Raises:
        PipelineError: If the file cannot be loaded or does not contain required columns.
    """
    logger = get_logger()
    path_obj = validate_file_path(path)
    validate_file_extension(path_obj, [".csv"])

    try:
        import pandas as pd
        df = pd.read_csv(path_obj, nrows=0)
        columns = list(df.columns)
    except Exception as e:
        error_msg = f"Failed to read CSV file: {path_obj}"
        logger.error(error_msg)
        raise PipelineError(error_msg) from e

    if required_columns:
        missing_cols = set(required_columns) - set(columns)
        if missing_cols:
            error_msg = (
                f"CSV file missing required columns: {missing_cols}. "
                f"Found columns: {columns}"
            )
            logger.error(error_msg)
            raise PipelineError(error_msg)

    logger.debug(f"Validated CSV file: {path_obj} with columns: {columns}")
    return columns


def validate_input(
    path: Union[str, Path],
    file_type: str,
    schema: Optional[Dict[str, Any]] = None,
    required_columns: Optional[list[str]] = None,
) -> Any:
    """
    Generic input validation function.

    This function dispatches to the appropriate validation function based on
    the file type.

    Args:
        path: Path to the input file.
        file_type: Type of the file ('json', 'yaml', 'csv').
        schema: Optional schema for JSON/YAML validation.
        required_columns: Optional list of required columns for CSV files.

    Returns:
        The validated and loaded data.

    Raises:
        PipelineError: If validation fails.
    """
    logger = get_logger()

    if file_type == "json":
        return validate_json_file(path, schema)
    elif file_type == "yaml":
        return load_and_validate_yaml(path, schema)
    elif file_type == "csv":
        validate_csv_file(path, required_columns)
        return None
    else:
        error_msg = f"Unsupported file type: {file_type}"
        logger.error(error_msg)
        raise PipelineError(error_msg)
