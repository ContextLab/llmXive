"""
Schema Validator for HCI_P2 Dialogue Dataset

This module provides functions to validate dataset schemas against
the contracts/dataset.schema.yaml definition.
"""

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import yaml


class SchemaValidationError(Exception):
    """Custom exception for schema validation errors."""
    pass


def load_schema(schema_path: Union[str, Path] = None) -> Dict[str, Any]:
    """
    Load the dataset schema from a YAML file.
    
    Args:
        schema_path: Path to the schema YAML file. Defaults to 
                    'contracts/dataset.schema.yaml' relative to project root.
    
    Returns:
        Dictionary containing the parsed schema.
    
    Raises:
        FileNotFoundError: If the schema file does not exist.
        yaml.YAMLError: If the schema file is not valid YAML.
    """
    if schema_path is None:
        # Default path relative to project root
        project_root = Path(__file__).parent.parent.parent
        schema_path = project_root / "contracts" / "dataset.schema.yaml"
    else:
        schema_path = Path(schema_path)
    
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(schema_path, 'r', encoding='utf-8') as f:
        schema = yaml.safe_load(f)
    
    return schema


def validate_type(value: Any, expected_type: str, field_name: str) -> bool:
    """
    Validate that a value matches the expected JSON Schema type.
    
    Args:
        value: The value to validate.
        expected_type: The expected type as a string (e.g., 'string', 'integer', 'array', 'object').
        field_name: Name of the field being validated (for error messages).
    
    Returns:
        True if the type matches.
    
    Raises:
        SchemaValidationError: If the type does not match.
    """
    type_map = {
        'string': str,
        'integer': int,
        'number': (int, float),
        'boolean': bool,
        'array': list,
        'object': dict,
        'null': type(None)
    }
    
    if expected_type not in type_map:
        raise SchemaValidationError(f"Unknown type '{expected_type}' for field '{field_name}'")
    
    expected_python_type = type_map[expected_type]
    
    # Special case: integer should not match bool (bool is subclass of int in Python)
    if expected_type == 'integer' and isinstance(value, bool):
        raise SchemaValidationError(f"Field '{field_name}' expected integer, got boolean")
    
    if not isinstance(value, expected_python_type):
        raise SchemaValidationError(
            f"Field '{field_name}' expected type '{expected_type}', got '{type(value).__name__}'"
        )
    
    return True


def validate_value_constraints(value: Any, constraints: Dict[str, Any], field_name: str) -> bool:
    """
    Validate value constraints like minimum, maximum, pattern, minLength, etc.
    
    Args:
        value: The value to validate.
        constraints: Dictionary of constraint definitions from the schema.
        field_name: Name of the field being validated.
    
    Returns:
        True if all constraints are satisfied.
    
    Raises:
        SchemaValidationError: If any constraint is violated.
    """
    # Numeric constraints
    if 'minimum' in constraints:
        if value < constraints['minimum']:
            raise SchemaValidationError(
                f"Field '{field_name}' value {value} is less than minimum {constraints['minimum']}"
            )
    
    if 'maximum' in constraints:
        if value > constraints['maximum']:
            raise SchemaValidationError(
                f"Field '{field_name}' value {value} is greater than maximum {constraints['maximum']}"
            )
    
    # String constraints
    if isinstance(value, str):
        if 'minLength' in constraints:
            if len(value) < constraints['minLength']:
                raise SchemaValidationError(
                    f"Field '{field_name}' length {len(value)} is less than minimum {constraints['minLength']}"
                )
        
        if 'maxLength' in constraints:
            if len(value) > constraints['maxLength']:
                raise SchemaValidationError(
                    f"Field '{field_name}' length {len(value)} is greater than maximum {constraints['maxLength']}"
                )
        
        if 'pattern' in constraints:
            pattern = constraints['pattern']
            if not re.match(pattern, value):
                raise SchemaValidationError(
                    f"Field '{field_name}' value '{value}' does not match pattern '{pattern}'"
                )
        
        if 'enum' in constraints:
            if value not in constraints['enum']:
                raise SchemaValidationError(
                    f"Field '{field_name}' value '{value}' is not in allowed values {constraints['enum']}"
                )
    
    # Array constraints
    if isinstance(value, list):
        if 'minItems' in constraints:
            if len(value) < constraints['minItems']:
                raise SchemaValidationError(
                    f"Field '{field_name}' has {len(value)} items, minimum is {constraints['minItems']}"
                )
        
        if 'maxItems' in constraints:
            if len(value) > constraints['maxItems']:
                raise SchemaValidationError(
                    f"Field '{field_name}' has {len(value)} items, maximum is {constraints['maxItems']}"
                )
    
    return True


def validate_object(obj: Dict[str, Any], schema: Dict[str, Any], obj_name: str) -> List[str]:
    """
    Validate an object against a schema definition.
    
    Args:
        obj: The object to validate.
        schema: The schema definition for the object.
        obj_name: Name of the object for error messages.
    
    Returns:
        List of validation error messages (empty if valid).
    """
    errors = []
    
    # Check required fields
    if 'required' in schema:
        for field in schema['required']:
            if field not in obj:
                errors.append(f"Missing required field '{field}' in {obj_name}")
    
    # Validate properties
    if 'properties' in schema:
        for field_name, field_schema in schema['properties'].items():
            if field_name in obj:
                field_value = obj[field_name]
                
                # Type validation
                if 'type' in field_schema:
                    try:
                        validate_type(field_value, field_schema['type'], f"{obj_name}.{field_name}")
                    except SchemaValidationError as e:
                        errors.append(str(e))
                        continue  # Skip further validation if type is wrong
                
                # Constraint validation
                try:
                    validate_value_constraints(field_value, field_schema, f"{obj_name}.{field_name}")
                except SchemaValidationError as e:
                    errors.append(str(e))
                
                # Nested object validation
                if field_schema['type'] == 'object' and 'properties' in field_schema:
                    nested_errors = validate_object(field_value, field_schema, f"{obj_name}.{field_name}")
                    errors.extend(nested_errors)
                
                # Array items validation
                if field_schema['type'] == 'array' and 'items' in field_schema:
                    items_schema = field_schema['items']
                    if '$ref' in items_schema:
                        # Resolve reference
                        ref_path = items_schema['$ref'].split('/')[-1]
                        if ref_path in schema.get('definitions', {}):
                            items_schema = schema['definitions'][ref_path]
                        elif ref_path in schema.get('properties', {}):
                            items_schema = schema['properties'][ref_path]
                    
                    for idx, item in enumerate(field_value):
                        if items_schema['type'] == 'object' and 'properties' in items_schema:
                            item_errors = validate_object(item, items_schema, f"{obj_name}.{field_name}[{idx}]")
                            errors.extend(item_errors)
                        elif 'type' in items_schema:
                            try:
                                validate_type(item, items_schema['type'], f"{obj_name}.{field_name}[{idx}]")
                            except SchemaValidationError as e:
                                errors.append(str(e))
    
    # Additional properties check
    if 'additionalProperties' in schema and schema['additionalProperties'] is False:
        allowed_fields = set(schema.get('properties', {}).keys())
        for field in obj.keys():
            if field not in allowed_fields:
                errors.append(f"Unexpected field '{field}' in {obj_name}")
    
    return errors


def validate_property(data: Any, property_schema: Dict[str, Any], property_name: str, schema: Dict[str, Any]) -> List[str]:
    """
    Validate a specific property against its schema definition.
    
    Args:
        data: The full dataset or object containing the property.
        property_schema: The schema definition for the property.
        property_name: Name of the property.
        schema: The full schema (for resolving references).
    
    Returns:
        List of validation error messages.
    """
    errors = []
    
    # Handle $ref
    if '$ref' in property_schema:
        ref_path = property_schema['$ref'].split('/')[-1]
        if ref_path in schema.get('properties', {}):
            property_schema = schema['properties'][ref_path]
        elif ref_path in schema.get('definitions', {}):
            property_schema = schema['definitions'][ref_path]
    
    # Validate based on type
    if property_schema['type'] == 'object':
        if not isinstance(data, dict):
            errors.append(f"Property '{property_name}' must be an object")
        else:
            errors.extend(validate_object(data, property_schema, property_name))
    elif property_schema['type'] == 'array':
        if not isinstance(data, list):
            errors.append(f"Property '{property_name}' must be an array")
        else:
            # Validate items if schema defined
            if 'items' in property_schema:
                items_schema = property_schema['items']
                # Resolve $ref in items
                if '$ref' in items_schema:
                    ref_path = items_schema['$ref'].split('/')[-1]
                    if ref_path in schema.get('properties', {}):
                        items_schema = schema['properties'][ref_path]
                    elif ref_path in schema.get('definitions', {}):
                        items_schema = schema['definitions'][ref_path]
                
                for idx, item in enumerate(data):
                    if items_schema['type'] == 'object' and 'properties' in items_schema:
                        item_errors = validate_object(item, items_schema, f"{property_name}[{idx}]")
                        errors.extend(item_errors)
                    else:
                        try:
                            validate_type(item, items_schema['type'], f"{property_name}[{idx}]")
                        except SchemaValidationError as e:
                            errors.append(str(e))
    else:
        try:
            validate_type(data, property_schema['type'], property_name)
        except SchemaValidationError as e:
            errors.append(str(e))
        try:
            validate_value_constraints(data, property_schema, property_name)
        except SchemaValidationError as e:
            errors.append(str(e))
    
    return errors


def validate_dataset(dataset: Dict[str, Any], schema: Dict[str, Any] = None) -> Tuple[bool, List[str]]:
    """
    Validate a dataset against the schema.
    
    Args:
        dataset: The dataset to validate (dictionary with Dialogue, Utterance, User keys).
        schema: Optional schema to use. If None, loads the default schema.
    
    Returns:
        Tuple of (is_valid, list_of_errors).
    """
    if schema is None:
        schema = load_schema()
    
    errors = []
    
    # Validate top-level structure
    required_top_level = schema.get('required', [])
    for key in required_top_level:
        if key not in dataset:
            errors.append(f"Missing required top-level section '{key}'")
    
    # Validate each section
    if 'properties' in schema:
        for section_name, section_schema in schema['properties'].items():
            if section_name in dataset:
                section_data = dataset[section_name]
                section_errors = validate_object(section_data, section_schema, section_name)
                errors.extend(section_errors)
    
    return len(errors) == 0, errors


def get_missing_fields(dataset: Dict[str, Any], schema: Dict[str, Any] = None) -> List[str]:
    """
    Get a list of missing required fields in the dataset.
    
    Args:
        dataset: The dataset to check.
        schema: Optional schema to use. If None, loads the default schema.
    
    Returns:
        List of missing required field paths (e.g., 'Dialogue.dialogue_id').
    """
    if schema is None:
        schema = load_schema()
    
    missing = []
    
    def check_required(obj: Dict[str, Any], required: List[str], prefix: str):
        for field in required:
            if field not in obj:
                missing.append(f"{prefix}.{field}" if prefix else field)
            else:
                # Check nested required fields
                field_schema = schema.get('properties', {}).get(prefix, {}).get('properties', {}).get(field, {})
                if field_schema.get('type') == 'object' and 'required' in field_schema:
                    check_required(obj[field], field_schema['required'], f"{prefix}.{field}")
    
    # Check top-level required
    for section in schema.get('required', []):
        if section in dataset:
            section_schema = schema.get('properties', {}).get(section, {})
            if 'required' in section_schema:
                check_required(dataset[section], section_schema['required'], section)
    
    return missing


def validate_dataset_schema(dataset: Dict[str, Any], schema_path: Union[str, Path] = None) -> Tuple[bool, List[str], List[str]]:
    """
    High-level function to validate a dataset against a schema file.
    
    Args:
        dataset: The dataset to validate.
        schema_path: Path to the schema file.
    
    Returns:
        Tuple of (is_valid, list_of_validation_errors, list_of_missing_fields).
    """
    schema = load_schema(schema_path)
    is_valid, validation_errors = validate_dataset(dataset, schema)
    missing_fields = get_missing_fields(dataset, schema)
    
    return is_valid, validation_errors, missing_fields
