import os
import yaml
import csv
from typing import List, Dict, Any, Optional
from datetime import datetime
from exceptions import E_NO_DATA

def load_schema(schema_path: str) -> Dict[str, Any]:
    """Load a YAML schema file."""
    if not os.path.exists(schema_path):
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

def validate_date_format(date_str: str, format_str: str = "%Y-%m-%d") -> bool:
    """Validate if a string matches the specified date format."""
    try:
        datetime.strptime(date_str, format_str)
        return True
    except ValueError:
        return False

def validate_numeric(value: Any, min_val: Optional[float] = None, max_val: Optional[float] = None) -> bool:
    """Validate if a value is numeric and within bounds."""
    if not isinstance(value, (int, float)):
        return False
    if min_val is not None and value < min_val:
        return False
    if max_val is not None and value > max_val:
        return False
    return True

def validate_record(record: Dict[str, Any], schema: Dict[str, Any]) -> List[str]:
    """Validate a record against a schema definition. Returns list of errors."""
    errors = []
    properties = schema.get('properties', {})
    required = schema.get('required', [])
    
    # Check required fields
    for field in required:
        if field not in record:
            errors.append(f"Missing required field: {field}")

    # Check types and constraints
    for key, value in record.items():
        if key not in properties:
            if schema.get('additionalProperties', True) is False:
                errors.append(f"Unexpected field: {key}")
            continue
        
        prop_def = properties[key]
        expected_type = prop_def.get('type')
        
        if expected_type == 'integer' and not isinstance(value, int):
            errors.append(f"Field {key} must be integer, got {type(value).__name__}")
        elif expected_type == 'number' and not isinstance(value, (int, float)):
            errors.append(f"Field {key} must be number, got {type(value).__name__}")
        
        if 'minimum' in prop_def and value < prop_def['minimum']:
            errors.append(f"Field {key} value {value} < minimum {prop_def['minimum']}")
        if 'exclusiveMinimum' in prop_def and value <= prop_def['exclusiveMinimum']:
            errors.append(f"Field {key} value {value} <= exclusiveMinimum {prop_def['exclusiveMinimum']}")
        
        if 'maximum' in prop_def and value > prop_def['maximum']:
            errors.append(f"Field {key} value {value} > maximum {prop_def['maximum']}")
        if 'exclusiveMaximum' in prop_def and value >= prop_def['exclusiveMaximum']:
            errors.append(f"Field {key} value {value} >= exclusiveMaximum {prop_def['exclusiveMaximum']}")

    return errors

def validate_csv_file(file_path: str, required_columns: List[str]) -> bool:
    """Validate that a CSV file exists and contains required columns."""
    if not os.path.exists(file_path):
        return False
    try:
        with open(file_path, 'r') as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames
            if headers is None:
                return False
            return all(col in headers for col in required_columns)
    except Exception:
        return False

def validate_raw_data(data_path: str) -> bool:
    """Validate raw data file existence and basic structure."""
    if not os.path.exists(data_path):
        raise E_NO_DATA(f"Raw data file not found: {data_path}")
    return True

def validate_output_data(output_path: str, expected_columns: List[str]) -> bool:
    """Validate output data file structure."""
    if not os.path.exists(output_path):
        return False
    try:
        with open(output_path, 'r') as f:
            reader = csv.DictReader(f)
            if reader.fieldnames is None:
                return False
            return all(col in reader.fieldnames for col in expected_columns)
    except Exception:
        return False
