"""
Utility module for validating JSON data against JSON Schema definitions.
Used to ensure data hygiene and provenance (Constitution Principle VI).
"""
import json
import logging
from pathlib import Path
from typing import Any, Dict, Tuple

try:
    import jsonschema
    from jsonschema import validate, ValidationError, Draft7Validator
    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False
    logging.warning("jsonschema library not installed. Validation will be skipped or fall back to basic checks.")

logger = logging.getLogger(__name__)

def load_schema(schema_path: Path) -> Dict[str, Any]:
    """Load a JSON schema from a file."""
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(schema_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_data(data_path: Path) -> Dict[str, Any]:
    """Load JSON data from a file."""
    if not data_path.exists():
        raise FileNotFoundError(f"Data file not found: {data_path}")
    
    with open(data_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def validate_single_record(record: Dict[str, Any], schema: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Validate a single record (dict) against a schema.
    Returns (is_valid, error_message).
    """
    if not HAS_JSONSCHEMA:
        logger.warning("jsonschema not available, performing basic type checks only.")
        # Basic fallback check for required keys if jsonschema is missing
        required = schema.get('required', [])
        for key in required:
            if key not in record:
                return False, f"Missing required key: {key}"
        return True, "Basic validation passed (jsonschema unavailable)"

    try:
        validate(instance=record, schema=schema)
        return True, "Valid"
    except ValidationError as e:
        return False, e.message

def validate_array_data(data_path: Path, schema_path: Path) -> Tuple[bool, str]:
    """
    Validate a JSON file containing an array of records against a schema.
    Each record in the array is validated against the schema.
    """
    try:
        schema = load_schema(schema_path)
        data = load_data(data_path)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        return False, str(e)

    if not isinstance(data, list):
        # If it's a single object, wrap it or validate as single
        if isinstance(data, dict):
            data = [data]
        else:
            return False, "Data file must contain a JSON array or a single object."

    errors = []
    for i, record in enumerate(data):
        is_valid, msg = validate_single_record(record, schema)
        if not is_valid:
            errors.append(f"Record {i}: {msg}")

    if errors:
        return False, "; ".join(errors)
    
    return True, "All records valid"

def validate_single_file(data_path: Path, schema_path: Path) -> Tuple[bool, str]:
    """
    Validate a JSON file (single object or array) against a schema.
    """
    try:
        schema = load_schema(schema_path)
        data = load_data(data_path)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        return False, str(e)

    # If data is an array, validate each item
    if isinstance(data, list):
        errors = []
        for i, record in enumerate(data):
            is_valid, msg = validate_single_record(record, schema)
            if not is_valid:
                errors.append(f"Record {i}: {msg}")
        if errors:
            return False, "; ".join(errors)
        return True, "All records valid"
    
    # If data is a single object
    is_valid, msg = validate_single_record(data, schema)
    return is_valid, msg

def main():
    """CLI entry point for schema validation."""
    import argparse
    parser = argparse.ArgumentParser(description="Validate JSON data against a JSON schema.")
    parser.add_argument("--data", required=True, help="Path to the JSON data file")
    parser.add_argument("--schema", required=True, help="Path to the JSON schema file")
    args = parser.parse_args()

    is_valid, message = validate_single_file(Path(args.data), Path(args.schema))
    
    if is_valid:
        print(f"Validation PASSED: {message}")
        return 0
    else:
        print(f"Validation FAILED: {message}")
        return 1

if __name__ == "__main__":
    exit(main())