"""
Contract validation module for data and output integrity.
Implements schema loading and validation against YAML definitions.
"""
import os
import yaml
import csv
from typing import List, Dict, Any, Optional
from datetime import datetime
from exceptions import E_NO_DATA

def load_schema(schema_path: str) -> Dict[str, Any]:
    """Load a YAML schema definition from disk."""
    if not os.path.exists(schema_path):
        raise E_NO_DATA(f"Schema file not found: {schema_path}")
    
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

def validate_date_format(date_str: str, format_str: str = "%Y-%m-%d") -> bool:
    """Validate a date string against a format."""
    try:
        datetime.strptime(date_str, format_str)
        return True
    except ValueError:
        return False

def validate_numeric(value: Any, min_val: Optional[float] = None, max_val: Optional[float] = None) -> bool:
    """Validate that a value is numeric and within bounds."""
    if not isinstance(value, (int, float)):
        return False
    if min_val is not None and value < min_val:
        return False
    if max_val is not None and value > max_val:
        return False
    return True

def validate_record(record: Dict[str, Any], schema: Dict[str, Any]) -> bool:
    """Validate a single record against a schema definition."""
    required = schema.get('required', [])
    properties = schema.get('properties', {})
    
    # Check required fields
    for field in required:
        if field not in record:
            return False
    
    # Validate field types and constraints
    for field, value in record.items():
        if field in properties:
            field_schema = properties[field]
            field_type = field_schema.get('type')
            
            if field_type == 'string' and not isinstance(value, str):
                return False
            elif field_type == 'integer' and not isinstance(value, int):
                return False
            elif field_type == 'number' and not isinstance(value, (int, float)):
                return False
            elif field_type == 'boolean' and not isinstance(value, bool):
                return False
            
            # Check pattern constraints
            if 'pattern' in field_schema and isinstance(value, str):
                import re
                if not re.match(field_schema['pattern'], value):
                    return False
    
    return True

def validate_csv_file(file_path: str, schema: Dict[str, Any]) -> bool:
    """Validate a CSV file against a schema."""
    if not os.path.exists(file_path):
        return False
    
    with open(file_path, 'r') as f:
        reader = csv.DictReader(f)
        
        # Check columns
        required_columns = schema.get('columns', [])
        if not all(col in reader.fieldnames for col in required_columns):
            return False
        
        # Validate rows
        for row in reader:
            if not validate_record(row, schema):
                return False
    
    return True

def validate_raw_data() -> bool:
    """Validate raw data files against dataset schema."""
    dataset_schema_path = 'contracts/dataset.schema.yaml'
    dataset_schema = load_schema(dataset_schema_path)
    
    # Validate FluView data
    fluview_schema = dataset_schema['properties']['fluview']
    fluview_path = fluview_schema['properties']['file_path']['pattern'].replace('^', '').replace('$', '').replace('\\', '')
    
    if not os.path.exists(fluview_path):
        return False
    
    if not validate_csv_file(fluview_path, fluview_schema):
        return False
    
    # Validate ground truth data
    gt_schema = dataset_schema['properties']['ground_truth']
    gt_path = gt_schema['properties']['file_path']['pattern'].replace('^', '').replace('$', '').replace('\\', '')
    
    if not os.path.exists(gt_path):
        return False
    
    if not validate_csv_file(gt_path, gt_schema):
        return False
    
    return True

def validate_output_data() -> bool:
    """Validate output files against output schema."""
    output_schema_path = 'contracts/output.schema.yaml'
    output_schema = load_schema(output_schema_path)
    
    # Validate flags
    flags_schema = output_schema['properties']['flags']
    flags_path = flags_schema['properties']['file_path']['pattern'].replace('^', '').replace('$', '').replace('\\', '')
    
    if not os.path.exists(flags_path):
        return False
    
    if not validate_csv_file(flags_path, flags_schema):
        return False
    
    # Validate baselines
    baselines_schema = output_schema['properties']['baselines']
    baselines_path = baselines_schema['properties']['file_path']['pattern'].replace('^', '').replace('$', '').replace('\\', '')
    
    if not os.path.exists(baselines_path):
        return False
    
    if not validate_csv_file(baselines_path, baselines_schema):
        return False
    
    # Validate sensitivity results
    sensitivity_schema = output_schema['properties']['sensitivity']
    grid_schema = sensitivity_schema['properties']['grid_file']['properties']
    grid_path = grid_schema['file_path']['pattern'].replace('^', '').replace('$', '').replace('\\', '')
    
    if not os.path.exists(grid_path):
        return False
    
    if not validate_csv_file(grid_path, grid_schema):
        return False
    
    tolerance_schema = sensitivity_schema['properties']['tolerance_file']['properties']
    tolerance_path = tolerance_schema['file_path']['pattern'].replace('^', '').replace('$', '').replace('\\', '')
    
    if not os.path.exists(tolerance_path):
        return False
    
    if not validate_csv_file(tolerance_path, tolerance_schema):
        return False
    
    return True