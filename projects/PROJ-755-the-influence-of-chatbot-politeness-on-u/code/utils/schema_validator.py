import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
import yaml


class SchemaValidationError(Exception):
    """Custom exception for schema validation errors."""
    pass


def load_schema(schema_path: Union[str, Path]) -> Dict[str, Any]:
    """
    Load a JSON/YAML schema from a file path.

    Args:
        schema_path: Path to the schema file.

    Returns:
        Dictionary containing the schema.

    Raises:
        FileNotFoundError: If the schema file does not exist.
        yaml.YAMLError: If the schema file is not valid YAML/JSON.
    """
    path = Path(schema_path)
    if not path.exists():
        raise FileNotFoundError(f"Schema file not found: {path}")

    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Try YAML first, then JSON
    try:
        schema = yaml.safe_load(content)
    except yaml.YAMLError:
        try:
            schema = json.loads(content)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid schema format (neither valid YAML nor JSON): {e}")

    return schema


def validate_type(value: Any, expected_type: str) -> bool:
    """
    Validate that a value matches the expected JSON Schema type.

    Args:
        value: The value to check.
        expected_type: The expected type (e.g., 'string', 'integer', 'number', 'boolean', 'array', 'object').

    Returns:
        True if the type matches, False otherwise.
    """
    if expected_type == "string":
        return isinstance(value, str)
    elif expected_type == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    elif expected_type == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    elif expected_type == "boolean":
        return isinstance(value, bool)
    elif expected_type == "array":
        return isinstance(value, list)
    elif expected_type == "object":
        return isinstance(value, dict)
    elif expected_type == "null":
        return value is None
    return False


def validate_value_constraints(value: Any, constraints: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Validate a value against specific constraints (min, max, enum, pattern).

    Args:
        value: The value to validate.
        constraints: Dictionary of constraints.

    Returns:
        Tuple of (is_valid, error_message).
    """
    if not constraints:
        return True, ""

    # Check minimum
    if "minimum" in constraints:
        if value < constraints["minimum"]:
            return False, f"Value {value} is less than minimum {constraints['minimum']}"

    # Check maximum
    if "maximum" in constraints:
        if value > constraints["maximum"]:
            return False, f"Value {value} is greater than maximum {constraints['maximum']}"

    # Check enum
    if "enum" in constraints:
        if value not in constraints["enum"]:
            return False, f"Value {value} not in allowed values: {constraints['enum']}"

    # Check pattern (for strings)
    if "pattern" in constraints and isinstance(value, str):
        if not re.match(constraints["pattern"], value):
            return False, f"Value '{value}' does not match pattern '{constraints['pattern']}'"

    return True, ""


def validate_object(obj: Dict[str, Any], schema_props: Dict[str, Any], path: str = "") -> List[str]:
    """
    Validate an object against a set of property definitions.

    Args:
        obj: The object to validate.
        schema_props: Schema definitions for the properties.
        path: Current path in the data structure for error reporting.

    Returns:
        List of error messages.
    """
    errors = []

    for prop_name, prop_schema in schema_props.items():
        current_path = f"{path}.{prop_name}" if path else prop_name

        # Check if required
        is_required = prop_schema.get("required", False)
        if prop_name not in obj:
            if is_required:
                errors.append(f"Missing required field: {current_path}")
            continue

        value = obj[prop_name]

        # Validate type
        if "type" in prop_schema:
            expected_type = prop_schema["type"]
            if not validate_type(value, expected_type):
                errors.append(f"Type mismatch at {current_path}: expected {expected_type}, got {type(value).__name__}")
                continue

        # Validate constraints
        if isinstance(value, (int, float, str)) and not isinstance(value, bool):
            is_valid, msg = validate_value_constraints(value, prop_schema)
            if not is_valid:
                errors.append(f"Constraint violation at {current_path}: {msg}")

        # Validate nested objects
        if prop_schema.get("type") == "object" and "properties" in prop_schema:
            nested_errors = validate_object(value, prop_schema["properties"], current_path)
            errors.extend(nested_errors)

        # Validate arrays
        if prop_schema.get("type") == "array" and "items" in prop_schema:
            item_schema = prop_schema["items"]
            for idx, item in enumerate(value):
                if item_schema.get("type") == "object" and "properties" in item_schema:
                    item_errors = validate_object(item, item_schema["properties"], f"{current_path}[{idx}]")
                    errors.extend(item_errors)
                elif "type" in item_schema:
                    if not validate_type(item, item_schema["type"]):
                        errors.append(f"Array item type mismatch at {current_path}[{idx}]: expected {item_schema['type']}, got {type(item).__name__}")

    return errors


def validate_property(prop_def: Dict[str, Any]) -> bool:
    """
    Validate that a property definition is well-formed.

    Args:
        prop_def: The property definition dictionary.

    Returns:
        True if valid, False otherwise.
    """
    if "type" not in prop_def:
        return False

    valid_types = ["string", "integer", "number", "boolean", "array", "object", "null"]
    if prop_def["type"] not in valid_types:
        return False

    return True


def validate_dataset(data: Dict[str, Any], schema: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate a dataset dictionary against a schema.

    Args:
        data: The dataset to validate.
        schema: The schema to validate against.

    Returns:
        Tuple of (is_valid, list_of_errors).
    """
    errors = []

    # Check root properties
    if "properties" not in schema:
        errors.append("Schema missing 'properties' definition")
        return False, errors

    if not isinstance(schema["properties"], dict):
        errors.append("'properties' in schema must be a dictionary")
        return False, errors

    # Validate each field in the data against the schema
    for field_name, field_value in data.items():
        if field_name in schema["properties"]:
            field_schema = schema["properties"][field_name]

            # Validate type
            if "type" in field_schema:
                if not validate_type(field_value, field_schema["type"]):
                    errors.append(f"Field '{field_name}' has incorrect type: expected {field_schema['type']}, got {type(field_value).__name__}")
                    continue

            # Validate constraints
            if isinstance(field_value, (int, float, str)) and not isinstance(field_value, bool):
                is_valid, msg = validate_value_constraints(field_value, field_schema)
                if not is_valid:
                    errors.append(f"Field '{field_name}' constraint violation: {msg}")

            # Validate nested objects
            if field_schema.get("type") == "object" and "properties" in field_schema:
                if isinstance(field_value, dict):
                    nested_errors = validate_object(field_value, field_schema["properties"], field_name)
                    errors.extend(nested_errors)

            # Validate arrays
            if field_schema.get("type") == "array" and "items" in field_schema:
                if isinstance(field_value, list):
                    item_schema = field_schema["items"]
                    for idx, item in enumerate(field_value):
                        if item_schema.get("type") == "object" and "properties" in item_schema:
                            item_errors = validate_object(item, item_schema["properties"], f"{field_name}[{idx}]")
                            errors.extend(item_errors)
                        elif "type" in item_schema:
                            if not validate_type(item, item_schema["type"]):
                                errors.append(f"Array item at '{field_name}[{idx}]' has incorrect type: expected {item_schema['type']}, got {type(item).__name__}")

    # Check required fields
    if "required_fields" in schema:
        for req_field in schema["required_fields"]:
            if req_field not in data:
                errors.append(f"Missing required field: {req_field}")

    return len(errors) == 0, errors


def validate_dataset_schema(schema: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate that the schema itself is well-formed.

    Args:
        schema: The schema dictionary to validate.

    Returns:
        Tuple of (is_valid, list_of_errors).
    """
    errors = []

    if "properties" not in schema:
        errors.append("Schema must define 'properties'")
    elif not isinstance(schema["properties"], dict):
        errors.append("'properties' must be a dictionary")
    else:
        for prop_name, prop_def in schema["properties"].items():
            if not validate_property(prop_def):
                errors.append(f"Invalid property definition for '{prop_name}'")

    return len(errors) == 0, errors


def get_missing_fields(data: Dict[str, Any], schema: Dict[str, Any]) -> List[str]:
    """
    Get a list of fields that are missing from the data but required by the schema.

    Args:
        data: The dataset dictionary.
        schema: The schema dictionary.

    Returns:
        List of missing field names.
    """
    missing = []

    if "required_fields" in schema:
        for field in schema["required_fields"]:
            if field not in data:
                missing.append(field)

    # Also check properties marked as required: true
    if "properties" in schema:
        for field_name, field_def in schema["properties"].items():
            if field_def.get("required", False) and field_name not in data:
                if field_name not in missing:
                    missing.append(field_name)

    return missing