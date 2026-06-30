"""
Contract validation utilities for dataset and output schemas.

This module provides functions to validate CSV data against the schemas
defined in contracts/dataset.schema.yaml and contracts/output.schema.yaml.
"""

import os
import yaml
import csv
from typing import List, Dict, Any, Optional
from datetime import datetime

# Import local exceptions
from exceptions import E_NO_DATA

# Paths relative to project root
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCHEMA_DIR = os.path.join(PROJECT_ROOT, "contracts")
DATA_RAW_DIR = os.path.join(PROJECT_ROOT, "data", "raw")
DATA_PROCESSED_DIR = os.path.join(PROJECT_ROOT, "data", "processed")

def load_schema(schema_name: str) -> Dict[str, Any]:
    """
    Load a schema definition from the contracts directory.
    
    Args:
        schema_name: Name of the schema file without extension (e.g., 'dataset.schema')
        
    Returns:
        Dictionary containing the schema definition.
        
    Raises:
        E_NO_DATA: If the schema file is not found.
    """
    schema_path = os.path.join(SCHEMA_DIR, f"{schema_name}.yaml")
    if not os.path.exists(schema_path):
        raise E_NO_DATA(f"Schema file not found: {schema_path}")
    
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

def validate_date_format(date_str: str) -> bool:
    """
    Validate if a string matches ISO 8601 date format (YYYY-MM-DD).
    
    Args:
        date_str: Date string to validate.
        
    Returns:
        True if valid, False otherwise.
    """
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False

def validate_numeric(value: Any, min_val: Optional[float] = None, max_val: Optional[float] = None) -> bool:
    """
    Validate if a value is numeric and within optional bounds.
    
    Args:
        value: Value to validate.
        min_val: Minimum allowed value.
        max_val: Maximum allowed value.
        
    Returns:
        True if valid, False otherwise.
    """
    if value is None:
        return True  # Allow null for optional numeric fields
    try:
        num = float(value)
        if min_val is not None and num < min_val:
            return False
        if max_val is not None and num > max_val:
            return False
        return True
    except (ValueError, TypeError):
        return False

def validate_record(record: Dict[str, Any], schema_def: Dict[str, Any]) -> List[str]:
    """
    Validate a single record against a schema definition.
    
    Args:
        record: Dictionary representing a row in the CSV.
        schema_def: Definition of the record structure from the schema.
        
    Returns:
        List of error messages. Empty if valid.
    """
    errors = []
    required_fields = schema_def.get("required", [])
    properties = schema_def.get("properties", {})
    
    # Check required fields
    for field in required_fields:
        if field not in record or record[field] == "" or record[field] is None:
            errors.append(f"Missing required field: {field}")
    
    # Validate each field
    for field, value in record.items():
        if field in properties:
            prop_def = properties[field]
            
            # Type check
            if prop_def.get("type") == "string":
                if not isinstance(value, str):
                    errors.append(f"Field {field} must be a string")
                
                # Pattern check
                if "pattern" in prop_def:
                    import re
                    if not re.match(prop_def["pattern"], str(value)):
                        errors.append(f"Field {field} does not match pattern: {prop_def['pattern']}")
                
                # Enum check
                if "enum" in prop_def:
                    if value not in prop_def["enum"]:
                        errors.append(f"Field {field} must be one of {prop_def['enum']}")
                
                # Date format check
                if "format" in prop_def and prop_def["format"] == "date":
                    if not validate_date_format(str(value)):
                        errors.append(f"Field {field} must be a valid date (YYYY-MM-DD)")
            
            elif prop_def.get("type") == "number":
                if not validate_numeric(
                    value, 
                    prop_def.get("minimum"), 
                    prop_def.get("maximum")
                ):
                    errors.append(f"Field {field} must be a number within bounds")
            
            elif prop_def.get("type") == "integer":
                if not validate_numeric(value):
                    errors.append(f"Field {field} must be an integer")
                else:
                    num_val = int(float(value))
                    if "minimum" in prop_def and num_val < prop_def["minimum"]:
                        errors.append(f"Field {field} must be >= {prop_def['minimum']}")
                    if "maximum" in prop_def and num_val > prop_def["maximum"]:
                        errors.append(f"Field {field} must be <= {prop_def['maximum']}")
            
            elif prop_def.get("type") == "boolean":
                if value not in [True, False, "True", "False", 0, 1]:
                    errors.append(f"Field {field} must be a boolean")
    
    return errors

def validate_csv_file(file_path: str, schema_name: str) -> bool:
    """
    Validate a CSV file against a named schema.
    
    Args:
        file_path: Path to the CSV file.
        schema_name: Name of the schema to validate against (e.g., 'fluview_ili_csv').
        
    Returns:
        True if valid.
        
    Raises:
        E_NO_DATA: If the file does not exist or validation fails.
    """
    if not os.path.exists(file_path):
        raise E_NO_DATA(f"Data file not found: {file_path}")
    
    # Load the full schema definition
    full_schema = load_schema("dataset.schema") if "dataset" in schema_name else load_schema("output.schema")
    
    # Find the specific schema definition
    schema_def = None
    if "schemas" in full_schema:
        if schema_name in full_schema["schemas"]:
            schema_def = full_schema["schemas"][schema_name]
    
    if not schema_def:
        raise E_NO_DATA(f"Schema definition '{schema_name}' not found in schema file")
    
    items_def = schema_def.get("items", {})
    
    errors = []
    with open(file_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        row_num = 1
        for row in reader:
            row_num += 1
            row_errors = validate_record(row, items_def)
            if row_errors:
                errors.extend([f"Row {row_num}: {err}" for err in row_errors])
            
            # Early exit if too many errors
            if len(errors) > 50:
                errors.append("... validation aborted due to excessive errors")
                break
    
    if errors:
        error_msg = f"Validation failed for {file_path}:\n" + "\n".join(errors[:10])
        raise E_NO_DATA(error_msg)
    
    return True

def validate_raw_data():
    """
    Validate the presence and integrity of raw data files.
    
    Raises:
        E_NO_DATA: If files are missing or invalid.
    """
    ili_path = os.path.join(DATA_RAW_DIR, "fluview_ili.csv")
    ground_truth_path = os.path.join(DATA_RAW_DIR, "ground_truth_events.csv")
    
    # Validate ILI data
    try:
        validate_csv_file(ili_path, "fluview_ili_csv")
    except E_NO_DATA as e:
        raise E_NO_DATA(f"Invalid ILI data: {e}")
    
    # Validate Ground Truth data
    try:
        validate_csv_file(ground_truth_path, "ground_truth_events_csv")
    except E_NO_DATA as e:
        raise E_NO_DATA(f"Invalid Ground Truth data: {e}")

def validate_output_data():
    """
    Validate the presence and integrity of output data files.
    
    Raises:
        E_NO_DATA: If files are missing or invalid.
    """
    flags_path = os.path.join(DATA_PROCESSED_DIR, "flags.csv")
    metrics_path = os.path.join(DATA_PROCESSED_DIR, "metrics.csv")
    
    if os.path.exists(flags_path):
        validate_csv_file(flags_path, "flags_csv")
    
    if os.path.exists(metrics_path):
        validate_csv_file(metrics_path, "metrics_csv")