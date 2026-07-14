"""
Input validation utilities for the llmXive automated science pipeline.

This module provides functions to validate file types, JSON schemas, and YAML files.
"""

from __future__ import annotations

import json
import mimetypes
from pathlib import Path
from typing import Any, Dict

import yaml

from logging.pipeline_logger import get_logger


def validate_file_type(
    file_path: Path,
    allowed_extensions: list[str] | None = None,
    allowed_mimetypes: list[str] | None = None,
) -> bool:
    """
    Validate that a file has an allowed extension and/or MIME type.

    Args:
        file_path: Path to the file to validate.
        allowed_extensions: List of allowed extensions (e.g., ['.csv', '.json']).
        allowed_mimetypes: List of allowed MIME types (e.g., ['text/csv', 'application/json']).

    Returns:
        True if the file is valid, raises PipelineError otherwise.

    Raises:
        PipelineError: If the file does not match allowed types.
    """
    from utils.error_handler import PipelineError, log_and_exit

    logger = get_logger()

    if not file_path.exists():
        log_and_exit(f"File not found: {file_path}", "E001")

    extension = file_path.suffix.lower()
    mime_type, _ = mimetypes.guess_type(str(file_path))

    if allowed_extensions and extension not in allowed_extensions:
        log_and_exit(
            f"Invalid file extension: {extension}. Allowed: {allowed_extensions}",
            "E002",
        )

    if allowed_mimetypes and mime_type not in allowed_mimetypes:
        log_and_exit(
            f"Invalid MIME type: {mime_type}. Allowed: {allowed_mimetypes}",
            "E003",
        )

    logger.info(f"File validation passed: {file_path}")
    return True


def validate_json_schema(
    file_path: Path,
    schema: Dict[str, Any],
) -> bool:
    """
    Validate a JSON file against a JSON Schema.

    Args:
        file_path: Path to the JSON file.
        schema: The JSON Schema dictionary.

    Returns:
        True if valid, raises PipelineError otherwise.

    Raises:
        PipelineError: If validation fails.
    """
    from utils.error_handler import PipelineError, log_and_exit

    logger = get_logger()

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        log_and_exit(f"Invalid JSON in {file_path}: {e}", "E004")

    try:
        import jsonschema
        jsonschema.validate(instance=data, schema=schema)
        logger.info(f"JSON schema validation passed: {file_path}")
        return True
    except jsonschema.exceptions.ValidationError as e:
        log_and_exit(f"JSON schema validation failed: {e.message}", "E005")


def validate_yaml_file(file_path: Path) -> Dict[str, Any]:
    """
    Load and validate a YAML file.

    Args:
        file_path: Path to the YAML file.

    Returns:
        The parsed YAML data.

    Raises:
        PipelineError: If the file cannot be parsed.
    """
    from utils.error_handler import PipelineError, log_and_exit

    logger = get_logger()

    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        logger.info(f"YAML file loaded successfully: {file_path}")
        return data
    except yaml.YAMLError as e:
        log_and_exit(f"Invalid YAML in {file_path}: {e}", "E006")
