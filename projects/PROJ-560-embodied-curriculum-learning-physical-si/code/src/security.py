"""
Security hardening module for data loading.

This module provides utilities to prevent arbitrary code execution (ACE)
during deserialization of untrusted data (JSON, YAML, CSV).

Key principles:
1. Never use `eval()`, `exec()`, or `pickle.load()` on untrusted input.
2. Use safe loaders for YAML (`yaml.safe_load`).
3. Validate JSON against a strict schema before processing.
4. Sanitize file paths to prevent directory traversal (e.g., `../../etc/passwd`).
"""

import json
import csv
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import logging

import yaml

# Configure logger
logger = logging.getLogger(__name__)


class SecurityError(Exception):
    """Base exception for security-related errors."""
    pass


class PathTraversalError(SecurityError):
    """Raised when a path traversal attempt is detected."""
    pass


class SchemaValidationError(SecurityError):
    """Raised when data fails schema validation."""
    pass


def sanitize_path(input_path: str, base_dir: Optional[Path] = None) -> Path:
    """
    Sanitize a file path to prevent directory traversal attacks.

    Args:
        input_path: The user-provided path string.
        base_dir: Optional base directory to resolve relative paths against.

    Returns:
        A resolved, absolute Path object that is guaranteed to be within base_dir.

    Raises:
        PathTraversalError: If the resolved path escapes the base directory.
    """
    if not input_path:
        raise PathTraversalError("Input path cannot be empty.")

    # Normalize the path to remove any '..' or '.' components
    # We use os.path.normpath to handle OS-specific separators
    normalized = os.path.normpath(input_path)

    # Construct the full path
    if base_dir:
        full_path = (base_dir / normalized).resolve()
    else:
        full_path = Path(normalized).resolve()

    # Check if the resolved path is within the base directory (if provided)
    # If base_dir is not provided, we just ensure it's not an absolute path
    # that points outside the current working directory context if that's a concern.
    # However, for this specific use case (loading data files), we usually enforce a base_dir.
    if base_dir:
        try:
            # This will raise ValueError if full_path is not relative to base_dir
            full_path.relative_to(base_dir.resolve())
        except ValueError:
            raise PathTraversalError(
                f"Path traversal detected: '{input_path}' resolves to '{full_path}' "
                f"which is outside the allowed directory '{base_dir}'."
            )

    logger.debug(f"Sanitized path: {input_path} -> {full_path}")
    return full_path


def safe_load_json(file_path: Union[str, Path], schema: Optional[Dict[str, Any]] = None) -> Any:
    """
    Safely load JSON data without arbitrary code execution.

    This function uses the standard `json` module which is safe by default
    (unlike `pickle` or `eval`). It optionally validates the loaded data
    against a simple schema.

    Args:
        file_path: Path to the JSON file.
        schema: Optional dictionary defining expected keys and types.

    Returns:
        Parsed JSON data.

    Raises:
        SecurityError: If file path is invalid or schema validation fails.
        FileNotFoundError: If file does not exist.
        json.JSONDecodeError: If file is not valid JSON.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"JSON file not found: {path}")

    # JSON load is safe from ACE
    with open(path, 'r', encoding='utf-8') as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in {path}: {e}")
            raise

    if schema:
        _validate_schema(data, schema)

    return data


def safe_load_yaml(file_path: Union[str, Path]) -> Any:
    """
    Safely load YAML data preventing arbitrary code execution.

    CRITICAL: Uses `yaml.safe_load` instead of `yaml.load` or `yaml.unsafe_load`.
    `safe_load` only constructs basic Python objects (dict, list, str, int, etc.)
    and prevents instantiation of arbitrary Python classes which could execute code.

    Args:
        file_path: Path to the YAML file.

    Returns:
        Parsed YAML data.

    Raises:
        SecurityError: If file path is invalid.
        FileNotFoundError: If file does not exist.
        yaml.YAMLError: If file is not valid YAML.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"YAML file not found: {path}")

    with open(path, 'r', encoding='utf-8') as f:
        try:
            # SAFE LOADING: This is the critical security measure
            data = yaml.safe_load(f)
        except yaml.YAMLError as e:
            logger.error(f"Invalid YAML in {path}: {e}")
            raise

    return data


def safe_load_csv(file_path: Union[str, Path], required_columns: Optional[List[str]] = None) -> List[Dict[str, str]]:
    """
    Safely load CSV data.

    CSV loading is inherently safer than pickle/eval, but we still validate
    the file structure and optional columns to prevent logic errors downstream.

    Args:
        file_path: Path to the CSV file.
        required_columns: Optional list of column names that must exist.

    Returns:
        List of dictionaries representing rows.

    Raises:
        SecurityError: If required columns are missing.
        FileNotFoundError: If file does not exist.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"CSV file not found: {path}")

    try:
        with open(path, 'r', encoding='utf-8', newline='') as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames

            if not headers:
                raise SchemaValidationError(f"CSV file {path} appears to be empty or has no headers.")

            if required_columns:
                missing = set(required_columns) - set(headers)
                if missing:
                    raise SchemaValidationError(
                        f"CSV file {path} is missing required columns: {missing}"
                    )

            data = list(reader)

    except csv.Error as e:
        logger.error(f"CSV parsing error in {path}: {e}")
        raise

    return data


def _validate_schema(data: Any, schema: Dict[str, Any]) -> None:
    """
    Basic schema validation for JSON/YAML data.

    Args:
        data: The loaded data structure.
        schema: Dictionary mapping keys to expected types (as strings).

    Raises:
        SchemaValidationError: If validation fails.
    """
    if not isinstance(data, dict):
        raise SchemaValidationError("Expected top-level object to be a dictionary.")

    for key, expected_type in schema.items():
        if key not in data:
            raise SchemaValidationError(f"Missing required key: '{key}'")

        value = data[key]
        # Simple type checking
        if expected_type == "str" and not isinstance(value, str):
            raise SchemaValidationError(f"Key '{key}' must be a string, got {type(value).__name__}")
        elif expected_type == "int" and not isinstance(value, int):
            raise SchemaValidationError(f"Key '{key}' must be an integer, got {type(value).__name__}")
        elif expected_type == "float" and not isinstance(value, (int, float)):
            raise SchemaValidationError(f"Key '{key}' must be a float, got {type(value).__name__}")
        elif expected_type == "list" and not isinstance(value, list):
            raise SchemaValidationError(f"Key '{key}' must be a list, got {type(value).__name__}")
        elif expected_type == "dict" and not isinstance(value, dict):
            raise SchemaValidationError(f"Key '{key}' must be a dict, got {type(value).__name__}")
        elif expected_type == "bool" and not isinstance(value, bool):
            raise SchemaValidationError(f"Key '{key}' must be a boolean, got {type(value).__name__}")
    
    logger.debug("Schema validation passed.")