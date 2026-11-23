"""
Utility module for loading and validating the energy decay schema.
"""
import yaml
import os
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import csv
import re

SCHEMA_PATH = Path(__file__).parent.parent.parent / "contracts" / "energy_schema.schema.yaml"

def load_energy_schema(schema_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Load the energy decay schema from YAML file.
    
    Args:
        schema_path: Optional path to schema file. Defaults to contracts/energy_schema.schema.yaml
    
    Returns:
        Dictionary containing the schema definition
    
    Raises:
        FileNotFoundError: If schema file does not exist
        yaml.YAMLError: If schema file is not valid YAML
    """
    if schema_path is None:
        schema_path = SCHEMA_PATH
    
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(schema_path, 'r', encoding='utf-8') as f:
        schema = yaml.safe_load(f)
    
    return schema

def validate_csv_against_schema(csv_path: Path, schema: Optional[Dict[str, Any]] = None) -> Tuple[bool, list]:
    """
    Validate a CSV file against the energy decay schema.
    
    Args:
        csv_path: Path to the CSV file to validate
        schema: Optional schema dictionary. If None, loads from default location.
    
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    
    if schema is None:
        try:
            schema = load_energy_schema()
        except FileNotFoundError as e:
            return False, [str(e)]
    
    if not csv_path.exists():
        return False, [f"CSV file not found: {csv_path}"]
    
    # Get required fields from schema
    required_fields = schema.get('required', [])
    properties = schema.get('properties', {})
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        # Check if all required columns exist
        if reader.fieldnames is None:
            return False, ["CSV file is empty or has no headers"]
        
        missing_columns = set(required_fields) - set(reader.fieldnames)
        if missing_columns:
            errors.append(f"Missing required columns: {missing_columns}")
        
        # Validate each row
        for row_num, row in enumerate(reader, start=2):  # Start at 2 (1 is header)
            # Check for missing required fields in row
            for field in required_fields:
                if field not in row or row[field] == '' or row[field] is None:
                    errors.append(f"Row {row_num}: Missing required field '{field}'")
            
            # Validate field types and constraints
            for field, value in row.items():
                if field not in properties:
                    continue  # Skip extra fields if additionalProperties is False
                
                field_schema = properties[field]
                field_type = field_schema.get('type')
                
                # Type validation
                if field_type == 'string':
                    if not isinstance(value, str):
                        errors.append(f"Row {row_num}: Field '{field}' should be string")
                    elif 'pattern' in field_schema:
                        pattern = field_schema['pattern']
                        if not re.match(pattern, value):
                            errors.append(f"Row {row_num}: Field '{field}' does not match pattern {pattern}")
                
                elif field_type == 'number':
                    try:
                        num_value = float(value) if value else None
                        if num_value is not None:
                            if 'minimum' in field_schema and num_value < field_schema['minimum']:
                                errors.append(f"Row {row_num}: Field '{field}' ({num_value}) is below minimum {field_schema['minimum']}")
                            if 'maximum' in field_schema and num_value > field_schema['maximum']:
                                errors.append(f"Row {row_num}: Field '{field}' ({num_value}) is above maximum {field_schema['maximum']}")
                    except ValueError:
                        errors.append(f"Row {row_num}: Field '{field}' is not a valid number: {value}")
                
                elif field_type == 'object':
                    # For JSON fields, we expect string representation of JSON
                    if value and not isinstance(value, dict):
                        try:
                            import json
                            json.loads(value)  # Validate it's valid JSON
                        except (ValueError, TypeError):
                            errors.append(f"Row {row_num}: Field '{field}' is not valid JSON")
    
    is_valid = len(errors) == 0
    return is_valid, errors