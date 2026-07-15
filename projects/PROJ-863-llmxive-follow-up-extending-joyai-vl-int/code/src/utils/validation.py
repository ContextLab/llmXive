"""
Validation utilities for llmXive.

Provides schema validation and data integrity checks.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

class ValidationError(Exception):
    """Custom exception for validation errors."""
    pass

def validate_schema(data: Any, schema: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Validate data against a JSON schema.

    Args:
        data: The data to validate.
        schema: The JSON schema to validate against.

    Returns:
        Tuple of (is_valid, error_message).
    """
    try:
        import jsonschema
        jsonschema.validate(instance=data, schema=schema)
        return True, ""
    except Exception as e:
        return False, str(e)

def validate_jsonl_file(file_path: str, schema: Optional[Dict[str, Any]] = None) -> List[int]:
    """
    Validate a JSONL file.

    Args:
        file_path: Path to the JSONL file.
        schema: Optional schema to validate each line against.

    Returns:
        List of line numbers that failed validation.
    """
    failed_lines = []
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    with open(path, 'r') as f:
        for i, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                data = json.loads(line)
                if schema:
                    is_valid, err = validate_schema(data, schema)
                    if not is_valid:
                        failed_lines.append(i)
            except json.JSONDecodeError:
                failed_lines.append(i)

    return failed_lines

def validate_manifest_structure(manifest_path: str) -> Tuple[bool, str]:
    """
    Validate the structure of a manifest file.

    Args:
        manifest_path: Path to the manifest file.

    Returns:
        Tuple of (is_valid, error_message).
    """
    path = Path(manifest_path)
    if not path.exists():
        return False, "Manifest file not found"

    try:
        with open(path, 'r') as f:
            data = json.load(f)
        
        # Basic checks
        required_keys = ["version", "chunks", "total_duration"]
        for key in required_keys:
            if key not in data:
                return False, f"Missing required key: {key}"
        
        if not isinstance(data["chunks"], list):
            return False, "Chunks must be a list"
        
        if not isinstance(data["total_duration"], (int, float)):
            return False, "Total duration must be a number"

        return True, ""
    except Exception as e:
        return False, str(e)

def validate_dimension_match(expected: int, actual: int, name: str = "dimension") -> None:
    """
    Validate that two dimensions match.

    Args:
        expected: Expected dimension value.
        actual: Actual dimension value.
        name: Name of the dimension for error message.

    Raises:
        ValidationError: If dimensions do not match.
    """
    if expected != actual:
        raise ValidationError(f"Dimension mismatch for {name}: Expected: {expected}, Actual: {actual}")

def validate_feature_keys(feature_dict: Dict[str, Any], required_keys: List[str]) -> None:
    """
    Validate that a feature dictionary contains required keys.

    Args:
        feature_dict: The feature dictionary.
        required_keys: List of required keys.

    Raises:
        ValidationError: If any required key is missing.
    """
    missing_keys = [key for key in required_keys if key not in feature_dict]
    if missing_keys:
        raise ValidationError(f"Missing required feature keys: {missing_keys}")
