"""
Schema validation utilities for contract testing.
Provides JSON schema validation logic and schema definitions.
"""
import json
from typing import Any, Dict, List, Tuple, Optional


def validate_json_schema(data: Any, schema: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate data against a JSON schema definition.

    Args:
        data: The data to validate.
        schema: The JSON schema to validate against.

    Returns:
        Tuple of (is_valid, list_of_errors).
    """
    errors = []

    def _validate_type(value: Any, expected_type: str, path: str) -> None:
        """Validate the type of a value."""
        type_map = {
            "string": str,
            "number": (int, float),
            "integer": int,
            "boolean": bool,
            "array": list,
            "object": dict,
            "null": type(None)
        }

        if expected_type not in type_map:
            errors.append(f"{path}: Unknown type '{expected_type}' in schema")
            return

        if not isinstance(value, type_map[expected_type]):
            actual_type = type(value).__name__
            errors.append(f"{path}: Expected type '{expected_type}', got '{actual_type}'")

    def _validate_object(obj: Dict[str, Any], schema: Dict[str, Any], path: str = "root") -> None:
        """Validate an object against an object schema."""
        if not isinstance(obj, dict):
            _validate_type(obj, "object", path)
            return

        properties = schema.get("properties", {})
        required = schema.get("required", [])

        # Check required fields
        for field in required:
            if field not in obj:
                errors.append(f"{path}: Missing required field '{field}'")

        # Validate each property
        for key, value in obj.items():
            if key in properties:
                _validate_value(value, properties[key], f"{path}.{key}")
            else:
                # If additionalProperties is false, reject extra fields
                if schema.get("additionalProperties") is False:
                    errors.append(f"{path}: Additional field '{key}' not allowed")

    def _validate_array(arr: List[Any], schema: Dict[str, Any], path: str = "root") -> None:
        """Validate an array against an array schema."""
        if not isinstance(arr, list):
            _validate_type(arr, "array", path)
            return

        # Check minItems
        min_items = schema.get("minItems")
        if min_items is not None and len(arr) < min_items:
            errors.append(f"{path}: Array has {len(arr)} items, minimum is {min_items}")

        # Check maxItems
        max_items = schema.get("maxItems")
        if max_items is not None and len(arr) > max_items:
            errors.append(f"{path}: Array has {len(arr)} items, maximum is {max_items}")

        # Validate items
        items_schema = schema.get("items")
        if items_schema:
            for i, item in enumerate(arr):
                _validate_value(item, items_schema, f"{path}[{i}]")

    def _validate_value(value: Any, schema: Dict[str, Any], path: str = "root") -> None:
        """Validate a value against a schema."""
        if "type" in schema:
            _validate_type(value, schema["type"], path)
            if not isinstance(value, type_map[schema["type"]]):
                return  # Type mismatch already reported

        if schema.get("type") == "object":
            _validate_object(value, schema, path)
        elif schema.get("type") == "array":
            _validate_array(value, schema, path)
        elif schema.get("type") == "string" and "enum" in schema:
            if value not in schema["enum"]:
                errors.append(f"{path}: Value '{value}' not in allowed values {schema['enum']}")

    type_map = {
        "string": str,
        "number": (int, float),
        "integer": int,
        "boolean": bool,
        "array": list,
        "object": dict,
        "null": type(None)
    }

    _validate_value(data, schema, path)

    return len(errors) == 0, errors


# Embedding output schema definition
# Matches the expected structure from src/data/embed.py
EMBEDDING_SCHEMA = {
    "type": "object",
    "required": ["file_id", "file_path", "label", "embedding", "model_name", "timestamp"],
    "properties": {
        "file_id": {
            "type": "string",
            "description": "Unique identifier for the audio file"
        },
        "file_path": {
            "type": "string",
            "description": "Path to the audio file"
        },
        "label": {
            "type": "string",
            "enum": ["benign", "jailbreak"],
            "description": "Classification label for the sample"
        },
        "embedding": {
            "type": "array",
            "items": {
                "type": "number"
            },
            "minItems": 1,
            "description": "Fixed-dimensional latent embedding vector"
        },
        "model_name": {
            "type": "string",
            "description": "Name of the encoder model used"
        },
        "timestamp": {
            "type": "string",
            "description": "ISO 8601 timestamp of extraction"
        }
    },
    "additionalProperties": False
}
