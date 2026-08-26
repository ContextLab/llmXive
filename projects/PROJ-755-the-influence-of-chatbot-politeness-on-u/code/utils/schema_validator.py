import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
import yaml

class SchemaValidationError(Exception):
    """Raised when schema validation fails."""
    pass

def load_schema(schema_path: Union[str, Path]) -> Dict[str, Any]:
    """Load a YAML schema file and return the parsed dictionary."""
    path = Path(schema_path)
    if not path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(path, 'r', encoding='utf-8') as f:
        try:
            schema = yaml.safe_load(f)
        except yaml.YAMLError as e:
            raise SchemaValidationError(f"Invalid YAML in schema file: {e}")
    
    return schema

def validate_type(value: Any, expected_type: Union[str, List[str]], field_name: str) -> None:
    """Validate that a value matches the expected JSON Schema type."""
    if isinstance(expected_type, list):
        # Handle "type": ["integer", "null"]
        valid = False
        for t in expected_type:
            if _check_single_type(value, t):
                valid = True
                break
        if not valid:
            raise SchemaValidationError(
                f"Field '{field_name}' has invalid type. Expected one of {expected_type}, got {type(value).__name__}"
            )
    else:
        if not _check_single_type(value, expected_type):
            raise SchemaValidationError(
                f"Field '{field_name}' has invalid type. Expected {expected_type}, got {type(value).__name__}"
            )

def _check_single_type(value: Any, expected_type: str) -> bool:
    """Check if value matches a single JSON Schema type string."""
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

def validate_value_constraints(value: Any, constraints: Dict[str, Any], field_name: str) -> None:
    """Validate value constraints like minimum, maximum, enum, pattern."""
    if "enum" in constraints:
        if value not in constraints["enum"]:
            raise SchemaValidationError(
                f"Field '{field_name}' value '{value}' not in allowed enum: {constraints['enum']}"
            )
    
    if "minimum" in constraints:
        if value < constraints["minimum"]:
            raise SchemaValidationError(
                f"Field '{field_name}' value {value} is less than minimum {constraints['minimum']}"
            )
    
    if "maximum" in constraints:
        if value > constraints["maximum"]:
            raise SchemaValidationError(
                f"Field '{field_name}' value {value} is greater than maximum {constraints['maximum']}"
            )
    
    if "pattern" in constraints and isinstance(value, str):
        pattern = constraints["pattern"]
        if not re.match(pattern, value):
            raise SchemaValidationError(
                f"Field '{field_name}' value '{value}' does not match pattern '{pattern}'"
            )

def validate_object(obj: Dict[str, Any], schema_def: Dict[str, Any], path: str = "") -> List[str]:
    """Validate an object against a schema definition, returning list of errors."""
    errors = []
    current_path = path if path else "root"
    
    # Check required fields
    if "required" in schema_def:
        for req_field in schema_def["required"]:
            if req_field not in obj:
                errors.append(f"Missing required field '{req_field}' at {current_path}")
    
    # Validate properties
    if "properties" in schema_def:
        for prop_name, prop_schema in schema_def["properties"].items():
            if prop_name in obj:
                prop_value = obj[prop_name]
                field_path = f"{current_path}.{prop_name}"
                
                # Type validation
                if "type" in prop_schema:
                    try:
                        validate_type(prop_value, prop_schema["type"], field_path)
                    except SchemaValidationError as e:
                        errors.append(str(e))
                    
                    # Constraint validation
                    if isinstance(prop_value, (int, float, str, list)) and not isinstance(prop_value, bool):
                        try:
                            validate_value_constraints(prop_value, prop_schema, field_path)
                        except SchemaValidationError as e:
                            errors.append(str(e))
                
                # Recursive validation for nested objects
                if prop_schema.get("type") == "object" and "properties" in prop_schema:
                    if isinstance(prop_value, dict):
                        errors.extend(validate_object(prop_value, prop_schema, field_path))
                
                # Recursive validation for array items
                if prop_schema.get("type") == "array" and "items" in prop_schema:
                    if isinstance(prop_value, list):
                        item_schema = prop_schema["items"]
                        if item_schema.get("$ref"):
                            # Resolve reference
                            ref_path = item_schema["$ref"].split("/")[-1]
                            if "definitions" in schema_def and ref_path in schema_def["definitions"]:
                                item_def = schema_def["definitions"][ref_path]
                                for idx, item in enumerate(prop_value):
                                    if isinstance(item, dict):
                                        errors.extend(validate_object(item, item_def, f"{field_path}[{idx}]"))
                        elif item_schema.get("type") == "object" and "properties" in item_schema:
                            for idx, item in enumerate(prop_value):
                                if isinstance(item, dict):
                                    errors.extend(validate_object(item, item_schema, f"{field_path}[{idx}]"))

    # Check for additionalProperties if defined
    if "additionalProperties" in schema_def and schema_def["additionalProperties"] is False:
        allowed_keys = set(schema_def.get("properties", {}).keys())
        for key in obj.keys():
            if key not in allowed_keys:
                errors.append(f"Unexpected field '{key}' at {current_path}")
    
    return errors

def validate_dataset(data: List[Dict[str, Any]], schema: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Validate a list of records (dataset) against the schema."""
    errors = []
    
    # Check root properties
    if "properties" in schema:
        if "records" in schema["properties"]:
            records_def = schema["properties"]["records"]
            if records_def.get("type") == "array" and "items" in records_def:
                item_schema = records_def["items"]
                
                # Resolve $ref if present
                if item_schema.get("$ref"):
                    ref_name = item_schema["$ref"].split("/")[-1]
                    if "definitions" in schema and ref_name in schema["definitions"]:
                        item_schema = schema["definitions"][ref_name]
                
                if item_schema.get("type") == "object":
                    for idx, record in enumerate(data):
                        if not isinstance(record, dict):
                            errors.append(f"Record at index {idx} is not an object")
                            continue
                        record_errors = validate_object(record, item_schema, f"records[{idx}]")
                        errors.extend(record_errors)
    
    return len(errors) == 0, errors

def validate_dataset_schema(dataset_path: Union[str, Path], schema_path: Union[str, Path]) -> Tuple[bool, List[str]]:
    """
    Validate a dataset (list of dicts) against a YAML schema file.
    Returns (is_valid, list_of_errors).
    """
    schema = load_schema(schema_path)
    
    # Load dataset - expecting a list of dictionaries
    dataset_path = Path(dataset_path)
    if not dataset_path.exists():
        raise FileNotFoundError(f"Dataset file not found: {dataset_path}")
    
    # Simple JSON/Parquet loading logic for validation
    # In a real scenario, we might need to handle different formats
    if dataset_path.suffix == '.json':
        with open(dataset_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    elif dataset_path.suffix == '.parquet':
        try:
            import pandas as pd
            df = pd.read_parquet(dataset_path)
            data = df.to_dict(orient='records')
        except ImportError:
            raise SchemaValidationError("pandas not installed, cannot read parquet files")
    else:
        # Try to load as JSON for now
        with open(dataset_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    
    if not isinstance(data, list):
        # If it's a dict with a 'records' key, extract it
        if isinstance(data, dict) and 'records' in data:
            data = data['records']
        else:
            raise SchemaValidationError(f"Dataset must be a list of records, got {type(data).__name__}")
    
    return validate_dataset(data, schema)

def get_missing_fields(dataset_path: Union[str, Path], schema_path: Union[str, Path], required_fields: List[str]) -> List[str]:
    """
    Check a dataset for the presence of specific required fields at the record level.
    Returns a list of missing field names.
    """
    schema = load_schema(schema_path)
    
    dataset_path = Path(dataset_path)
    if not dataset_path.exists():
        raise FileNotFoundError(f"Dataset file not found: {dataset_path}")
    
    # Load data
    if dataset_path.suffix == '.json':
        with open(dataset_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    elif dataset_path.suffix == '.parquet':
        import pandas as pd
        df = pd.read_parquet(dataset_path)
        data = df.to_dict(orient='records')
    else:
        with open(dataset_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    
    if not isinstance(data, list):
        if isinstance(data, dict) and 'records' in data:
            data = data['records']
        else:
            return [] # Cannot check fields if not list-like
    
    # Check first record for fields (assuming uniform schema)
    if not data:
        return required_fields # All missing if empty
    
    first_record = data[0]
    missing = []
    for field in required_fields:
        if field not in first_record:
            missing.append(field)
    
    return missing