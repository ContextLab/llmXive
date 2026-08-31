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
        Dictionary containing the schema definition.

    Raises:
        FileNotFoundError: If the schema file does not exist.
        ValueError: If the file content is not valid JSON/YAML.
    """
    path = Path(schema_path)
    if not path.exists():
        raise FileNotFoundError(f"Schema file not found: {path}")

    with open(path, 'r', encoding='utf-8') as f:
        try:
            return yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in schema file: {e}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in schema file: {e}")


def validate_type(value: Any, expected_type: Union[str, List[str]]) -> bool:
    """
    Validate that a value matches the expected JSON Schema type.

    Supports: string, integer, number, boolean, array, object, null.
    Handles 'type' as a list (e.g., ["string", "null"]).

    Args:
        value: The value to check.
        expected_type: The expected type string or list of strings.

    Returns:
        True if the type matches, False otherwise.
    """
    if isinstance(expected_type, str):
        types_to_check = [expected_type]
    else:
        types_to_check = expected_type

    if "null" in types_to_check and value is None:
        return True

    if "string" in types_to_check and isinstance(value, str):
        return True
    if "integer" in types_to_check and isinstance(value, int) and not isinstance(value, bool):
        return True
    if "number" in types_to_check and isinstance(value, (int, float)) and not isinstance(value, bool):
        return True
    if "boolean" in types_to_check and isinstance(value, bool):
        return True
    if "array" in types_to_check and isinstance(value, list):
        return True
    if "object" in types_to_check and isinstance(value, dict):
        return True

    return False


def validate_value_constraints(value: Any, constraints: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Validate numeric or string constraints (minimum, maximum, pattern, etc.).

    Args:
        value: The value to check.
        constraints: Dictionary of constraints (e.g., {'minimum': 1, 'maximum': 5}).

    Returns:
        Tuple of (is_valid, error_message).
    """
    if value is None:
        return True, ""

    if "minimum" in constraints:
        if value < constraints["minimum"]:
            return False, f"Value {value} is less than minimum {constraints['minimum']}"

    if "maximum" in constraints:
        if value > constraints["maximum"]:
            return False, f"Value {value} is greater than maximum {constraints['maximum']}"

    if "pattern" in constraints and isinstance(value, str):
        if not re.match(constraints["pattern"], value):
            return False, f"Value '{value}' does not match pattern '{constraints['pattern']}'"

    if "minLength" in constraints and isinstance(value, str):
        if len(value) < constraints["minLength"]:
            return False, f"String length {len(value)} is less than minLength {constraints['minLength']}"

    if "maxLength" in constraints and isinstance(value, str):
        if len(value) > constraints["maxLength"]:
            return False, f"String length {len(value)} is greater than maxLength {constraints['maxLength']}"

    if "enum" in constraints and value not in constraints["enum"]:
        return False, f"Value '{value}' is not in allowed enum values: {constraints['enum']}"

    return True, ""


def validate_property(value: Any, property_schema: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Validate a single property against its schema definition.

    Args:
        value: The value to validate.
        property_schema: The schema definition for this property.

    Returns:
        Tuple of (is_valid, error_message).
    """
    # Check type
    if "type" in property_schema:
        if not validate_type(value, property_schema["type"]):
            return False, f"Type mismatch: expected {property_schema['type']}, got {type(value).__name__}"

    # Check constraints
    if value is not None:
        is_valid, error = validate_value_constraints(value, property_schema)
        if not is_valid:
            return False, error

    # If it's an object, recursively validate properties
    if "type" in property_schema and property_schema["type"] == "object" and isinstance(value, dict):
        return validate_object(value, property_schema)

    # If it's an array, validate items
    if "type" in property_schema and property_schema["type"] == "array" and isinstance(value, list):
        items_schema = property_schema.get("items", {})
        if items_schema:
            for idx, item in enumerate(value):
                item_valid, item_error = validate_property(item, items_schema)
                if not item_valid:
                    return False, f"Item at index {idx} failed: {item_error}"

    return True, ""


def validate_object(obj: Dict[str, Any], schema: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Validate an object (dict) against a schema definition.

    Args:
        obj: The dictionary to validate.
        schema: The schema definition for the object.

    Returns:
        Tuple of (is_valid, error_message).
    """
    properties = schema.get("properties", {})
    required = schema.get("required", [])
    additional_properties = schema.get("additionalProperties", True)

    # Check required properties
    for req_prop in required:
        if req_prop not in obj:
            return False, f"Missing required property: {req_prop}"

    # Validate each property
    for key, value in obj.items():
        if key in properties:
            is_valid, error = validate_property(value, properties[key])
            if not is_valid:
                return False, f"Property '{key}' failed: {error}"
        elif additional_properties is False:
            return False, f"Unexpected property: {key}"

    return True, ""


def validate_dataset_schema(schema_path: Union[str, Path]) -> bool:
    """
    Validate the schema file itself for basic structural integrity.

    Args:
        schema_path: Path to the schema file.

    Returns:
        True if the schema is structurally valid.

    Raises:
        SchemaValidationError: If the schema is invalid.
    """
    schema = load_schema(schema_path)

    if not isinstance(schema, dict):
        raise SchemaValidationError("Schema must be a JSON object")

    if "type" in schema and schema["type"] != "object":
        raise SchemaValidationError("Dataset schema root must be of type 'object'")

    if "properties" not in schema:
        raise SchemaValidationError("Dataset schema must define 'properties'")

    return True


def validate_dataset(data: Union[List[Dict], Dict], schema: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate a dataset (list of records or single record) against a schema.

    Args:
        data: The data to validate.
        schema: The loaded schema dictionary.

    Returns:
        Tuple of (is_valid, list_of_errors).
    """
    errors = []

    # If data is a single record, wrap it in a list for uniform processing
    if isinstance(data, dict):
        data = [data]

    if not isinstance(data, list):
        return False, ["Data must be a list of records or a single record"]

    if not data:
        return True, []

    # Validate each record
    for idx, record in enumerate(data):
        if not isinstance(record, dict):
            errors.append(f"Record {idx} is not an object")
            continue

        is_valid, error = validate_object(record, schema)
        if not is_valid:
            errors.append(f"Record {idx}: {error}")

    return len(errors) == 0, errors


def get_missing_fields(data: List[Dict], schema: Dict[str, Any]) -> List[str]:
    """
    Identify which required fields are missing across the dataset.

    Args:
        data: List of data records.
        schema: The schema definition.

    Returns:
        List of missing required field names.
    """
    required_fields = set(schema.get("required", []))
    found_fields = set()

    for record in data:
        if isinstance(record, dict):
            found_fields.update(record.keys())

    return list(required_fields - found_fields)


def validate_dataset_schema_wrapper(
    data_path: Union[str, Path],
    schema_path: Union[str, Path],
    is_list: bool = True
) -> Tuple[bool, List[str]]:
    """
    Convenience wrapper to load data and schema from files and validate.

    Args:
        data_path: Path to the data file (JSON or JSONL).
        schema_path: Path to the schema file (YAML or JSON).
        is_list: True if the data file contains a list of objects, False if it contains a single object.

    Returns:
        Tuple of (is_valid, list_of_errors).
    """
    # Load schema
    schema = load_schema(schema_path)

    # Load data
    data_path = Path(data_path)
    with open(data_path, 'r', encoding='utf-8') as f:
        if data_path.suffix == '.jsonl':
            # JSONL: read line by line
            data = []
            for line in f:
                if line.strip():
                    data.append(json.loads(line))
            if not is_list and len(data) == 1:
                data = data[0]
        else:
            data = json.load(f)

    return validate_dataset(data, schema)
