import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
import pandas as pd
import numpy as np
import yaml

logger = logging.getLogger(__name__)

def load_schema(schema_path: Union[str, Path]) -> Dict[str, Any]:
    """Load a YAML schema file."""
    path = Path(schema_path)
    if not path.exists():
        raise FileNotFoundError(f"Schema file not found: {path}")
    
    with open(path, 'r') as f:
        return yaml.safe_load(f)

def validate_field_type(value: Any, expected_type: str) -> bool:
    """Validate that a value matches the expected type string."""
    if expected_type == 'string':
        return isinstance(value, str)
    elif expected_type == 'integer':
        return isinstance(value, int) and not isinstance(value, bool)
    elif expected_type == 'number':
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    elif expected_type == 'boolean':
        return isinstance(value, bool)
    else:
        logger.warning(f"Unknown type definition: {expected_type}")
        return True

def validate_enum(value: Any, allowed_values: List[Any]) -> bool:
    """Validate that a value is in the allowed list."""
    return value in allowed_values

def validate_range(value: Union[int, float], min_val: Optional[float] = None, max_val: Optional[float] = None) -> bool:
    """Validate that a numeric value is within range."""
    if min_val is not None and value < min_val:
        return False
    if max_val is not None and value > max_val:
        return False
    return True

def validate_dataframe_against_schema(df: pd.DataFrame, schema: Dict[str, Any]) -> List[str]:
    """
    Validate a DataFrame against a schema definition.
    Returns a list of error messages.
    """
    errors = []
    dataset_schema = schema.get('dataset', {})
    properties = dataset_schema.get('properties', {})
    required_fields = dataset_schema.get('required', [])
    
    # Check required fields exist
    missing_fields = set(required_fields) - set(df.columns)
    if missing_fields:
        errors.append(f"Missing required columns: {missing_fields}")
    
    # Validate each row
    for idx, row in df.iterrows():
        for field in required_fields:
            if pd.isna(row[field]):
                errors.append(f"Row {idx}: Field '{field}' is null.")
                continue
            
            if field not in properties:
                continue
            
            spec = properties[field]
            value = row[field]
            field_type = spec.get('type')
            
            if not validate_field_type(value, field_type):
                errors.append(f"Row {idx}: Field '{field}' has invalid type. Expected {field_type}, got {type(value)}")
                continue
            
            if field_type == 'string' and 'enum' in spec:
                if not validate_enum(value, spec['enum']):
                    errors.append(f"Row {idx}: Field '{field}' value '{value}' not in {spec['enum']}")
            
            if field_type in ['integer', 'number']:
                min_val = spec.get('minimum')
                if min_val is not None and not validate_range(value, min_val=min_val):
                    errors.append(f"Row {idx}: Field '{field}' value {value} is below minimum {min_val}")
    
    return errors

def validate_dataset(df: pd.DataFrame, schema_path: Union[str, Path]) -> bool:
    """
    Validate a dataset against a schema file.
    Returns True if valid, raises ValueError with details if invalid.
    """
    schema = load_schema(schema_path)
    errors = validate_dataframe_against_schema(df, schema)
    
    if errors:
        error_msg = "Dataset validation failed:\n" + "\n".join(errors)
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    logger.info("Dataset validation passed.")
    return True

def main():
    """Main entry point for standalone validation."""
    import sys
    if len(sys.argv) < 3:
        print("Usage: python validation.py <csv_path> <schema_path>")
        sys.exit(1)
    
    csv_path = sys.argv[1]
    schema_path = sys.argv[2]
    
    try:
        df = pd.read_csv(csv_path)
        validate_dataset(df, schema_path)
        print("Validation successful.")
    except Exception as e:
        print(f"Validation failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
