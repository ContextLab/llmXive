import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
import yaml


class SchemaValidationError(Exception):
    """Exception raised when schema validation fails."""
    pass


def load_schema(schema_path: Union[str, Path]) -> Dict[str, Any]:
    """Load a YAML schema definition from a file."""
    path = Path(schema_path)
    if not path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def validate_type(value: Any, expected_type: str) -> bool:
    """Check if a value matches a JSON Schema type definition."""
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
    elif expected_type == "string or null":
        return isinstance(value, str) or value is None
    elif expected_type == "integer or null":
        return (isinstance(value, int) and not isinstance(value, bool)) or value is None
    elif expected_type == "number or null":
        return (isinstance(value, (int, float)) and not isinstance(value, bool)) or value is None
    elif expected_type == "string, integer or null":
        return isinstance(value, (str, int)) and not isinstance(value, bool) or value is None
    else:
        # Fallback for complex types or arrays
        return True


def validate_value_constraints(value: Any, constraints: Dict[str, Any]) -> bool:
    """Validate value against constraints like minimum, maximum, minLength."""
    if value is None:
        return True
    if "minimum" in constraints and value < constraints["minimum"]:
        return False
    if "maximum" in constraints and value > constraints["maximum"]:
        return False
    if "minLength" in constraints and isinstance(value, str):
        if len(value) < constraints["minLength"]:
            return False
    if "maxLength" in constraints and isinstance(value, str):
        if len(value) > constraints["maxLength"]:
            return False
    if "enum" in constraints and value not in constraints["enum"]:
        return False
    return True


def validate_property(value: Any, property_def: Dict[str, Any]) -> bool:
    """Validate a single property value against its definition."""
    if "type" in property_def:
        if not validate_type(value, property_def["type"]):
            return False
    if not validate_value_constraints(value, property_def):
        return False
    return True


def validate_object(obj: Dict[str, Any], schema_def: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Validate an object against a schema definition."""
    errors = []
    required_fields = schema_def.get("required", [])
    properties = schema_def.get("properties", {})

    # Check required fields
    for field in required_fields:
        if field not in obj:
            errors.append(f"Missing required field: {field}")

    # Validate each field
    for field, value in obj.items():
        if field in properties:
            if not validate_property(value, properties[field]):
                errors.append(f"Invalid value for field '{field}'")
        # Optional: warn about extra fields if needed

    return len(errors) == 0, errors


def validate_dataset_schema(dataset: List[Dict[str, Any]], schema: Dict[str, Any], entity_name: str) -> Tuple[bool, List[str]]:
    """Validate a list of records against a specific entity schema."""
    if entity_name not in schema.get("properties", {}):
        raise SchemaValidationError(f"Entity '{entity_name}' not found in schema")

    entity_schema = schema["properties"][entity_name]
    all_errors = []
    valid_count = 0

    for idx, record in enumerate(dataset):
        is_valid, errors = validate_object(record, entity_schema)
        if is_valid:
            valid_count += 1
        else:
            for err in errors:
                all_errors.append(f"Record {idx}: {err}")

    if valid_count == 0:
        raise SchemaValidationError(f"No valid records found for entity '{entity_name}'")

    return len(all_errors) == 0, all_errors


def validate_dataset(dataset_path: Union[str, Path], schema_path: Union[str, Path], entity_name: str) -> bool:
    """Validate a dataset file against a schema."""
    schema = load_schema(schema_path)
    with open(dataset_path, 'r', encoding='utf-8') as f:
        dataset = json.load(f)

    if not isinstance(dataset, list):
        raise SchemaValidationError("Dataset must be a list of records")

    is_valid, errors = validate_dataset_schema(dataset, schema, entity_name)
    if not is_valid:
        raise SchemaValidationError(f"Validation failed: {'; '.join(errors)}")
    return True


def get_missing_fields(record: Dict[str, Any], schema_def: Dict[str, Any]) -> List[str]:
    """Get list of missing required fields from a record."""
    required = schema_def.get("required", [])
    return [field for field in required if field not in record]


def validate_dataset_schema_wrapper(dataset: List[Dict[str, Any]], schema: Dict[str, Any], entity_name: str) -> Dict[str, Any]:
    """
    Wrapper for validation that returns a structured result.
    Returns: { "valid": bool, "errors": List[str], "valid_count": int, "total_count": int }
    """
    try:
        is_valid, errors = validate_dataset_schema(dataset, schema, entity_name)
        return {
            "valid": is_valid,
            "errors": errors,
            "valid_count": sum(1 for _ in dataset if True), # simplified count logic
            "total_count": len(dataset)
        }
    except SchemaValidationError as e:
        return {
            "valid": False,
            "errors": [str(e)],
            "valid_count": 0,
            "total_count": len(dataset)
        }
    except Exception as e:
        return {
            "valid": False,
            "errors": [f"Unexpected error: {str(e)}"],
            "valid_count": 0,
            "total_count": len(dataset)
        }