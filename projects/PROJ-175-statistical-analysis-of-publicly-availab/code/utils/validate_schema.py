"""
Schema Validation Utility for Statistical Analysis of Recipe Data

This module provides functions to validate dataframes against defined schemas.
It ensures that all required fields are present and have the correct types.
"""

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import pandas as pd
import yaml

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SchemaValidationError(Exception):
    """Exception raised when schema validation fails."""
    pass

def load_schema(schema_path: str) -> Dict[str, Any]:
    """
    Load a schema definition from a YAML file.
    
    Args:
        schema_path: Path to the schema YAML file
        
    Returns:
        Dictionary containing the schema definition
        
    Raises:
        FileNotFoundError: If the schema file does not exist
        yaml.YAMLError: If the YAML file is malformed
    """
    path = Path(schema_path)
    if not path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(path, 'r') as f:
        schema = yaml.safe_load(f)
    
    logger.info(f"Loaded schema from {schema_path}")
    return schema

def validate_field(field_def: Dict[str, Any], value: Any, field_name: str) -> Tuple[bool, Optional[str]]:
    """
    Validate a single field value against its definition.
    
    Args:
        field_def: Field definition from the schema
        value: The value to validate
        field_name: Name of the field for error messages
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    field_type = field_def.get('type')
    required = field_def.get('required', False)
    
    # Check if value is None for non-required fields
    if value is None and not required:
        return True, None
    
    # Check if required field is missing
    if value is None and required:
        return False, f"Required field '{field_name}' is missing"
    
    # Type validation
    if field_type == 'string':
        if not isinstance(value, str):
            return False, f"Field '{field_name}' must be a string, got {type(value).__name__}"
        if len(value) == 0:
            return False, f"Field '{field_name}' cannot be an empty string"
            
    elif field_type == 'integer':
        if not isinstance(value, int):
            return False, f"Field '{field_name}' must be an integer, got {type(value).__name__}"
            
    elif field_type == 'float':
        if not isinstance(value, (int, float)):
            return False, f"Field '{field_name}' must be a float, got {type(value).__name__}"
            
    elif field_type == 'object':
        if not isinstance(value, dict):
            return False, f"Field '{field_name}' must be an object, got {type(value).__name__}"
            
    elif field_type == 'array':
        if not isinstance(value, list):
            return False, f"Field '{field_name}' must be an array, got {type(value).__name__}"
    
    # Enum validation
    if 'enum' in field_def:
        if value not in field_def['enum']:
            return False, f"Field '{field_name}' must be one of {field_def['enum']}, got {value}"
    
    # Range validation
    if 'min' in field_def or 'max' in field_def:
        if isinstance(value, (int, float)):
            min_val = field_def.get('min', float('-inf'))
            max_val = field_def.get('max', float('inf'))
            if value < min_val:
                return False, f"Field '{field_name}' must be >= {min_val}, got {value}"
            if value > max_val:
                return False, f"Field '{field_name}' must be <= {max_val}, got {value}"
    
    return True, None

def validate_dataframe(df: pd.DataFrame, schema: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate a dataframe against a schema definition.
    
    Args:
        df: Pandas dataframe to validate
        schema: Schema definition dictionary
        
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    fields = schema.get('fields', [])
    
    # Check for required columns
    for field in fields:
        field_name = field.get('name')
        if field_name not in df.columns:
            if field.get('required', False):
                errors.append(f"Missing required column: {field_name}")
    
    if errors:
        return False, errors
    
    # Validate each row (sample validation for large datasets)
    sample_size = min(100, len(df))
    sample_df = df.sample(n=sample_size, random_state=42)
    
    for field in fields:
        field_name = field.get('name')
        if field_name not in df.columns:
            continue
            
        field_type = field.get('type')
        
        # Check column type consistency
        if field_type == 'string':
            if not pd.api.types.is_string_dtype(df[field_name]):
                errors.append(f"Column '{field_name}' should be string type")
        elif field_type == 'integer':
            if not pd.api.types.is_integer_dtype(df[field_name]):
                errors.append(f"Column '{field_name}' should be integer type")
        elif field_type == 'float':
            if not pd.api.types.is_float_dtype(df[field_name]):
                errors.append(f"Column '{field_name}' should be float type")
        
        # Validate sample values
        for idx, row in sample_df.iterrows():
            is_valid, error_msg = validate_field(field, row[field_name], field_name)
            if not is_valid:
                errors.append(f"Row {idx}: {error_msg}")
                if len(errors) >= 10:  # Limit error messages
                    break
        if len(errors) >= 10:
            break
    
    return len(errors) == 0, errors

def validate_schema(dataframe: pd.DataFrame, schema_path: str) -> Tuple[bool, List[str]]:
    """
    Main function to validate a dataframe against a schema file.
    
    Args:
        dataframe: Pandas dataframe to validate
        schema_path: Path to the schema YAML file
        
    Returns:
        Tuple of (is_valid, list_of_errors)
        
    Raises:
        FileNotFoundError: If schema file not found
    """
    try:
        schema = load_schema(schema_path)
        is_valid, errors = validate_dataframe(dataframe, schema)
        
        if is_valid:
            logger.info(f"Schema validation passed for {schema_path}")
        else:
            logger.warning(f"Schema validation failed with {len(errors)} errors")
        
        return is_valid, errors
        
    except Exception as e:
        logger.error(f"Error during schema validation: {str(e)}")
        return False, [str(e)]

def save_validation_report(errors: List[str], output_path: str, is_valid: bool) -> None:
    """
    Save validation results to a JSON file.
    
    Args:
        errors: List of validation errors
        output_path: Path to save the report
        is_valid: Whether validation passed
    """
    report = {
        "is_valid": is_valid,
        "error_count": len(errors),
        "errors": errors,
        "timestamp": pd.Timestamp.now().isoformat()
    }
    
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Validation report saved to {output_path}")

def main():
    """
    Command-line interface for schema validation.
    
    Usage:
        python code/utils/validate_schema.py --data <data_path> --schema <schema_path> [--output <output_path>]
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Validate dataframe against schema')
    parser.add_argument('--data', required=True, help='Path to input data file (CSV or Parquet)')
    parser.add_argument('--schema', required=True, help='Path to schema YAML file')
    parser.add_argument('--output', help='Path to save validation report (JSON)')
    
    args = parser.parse_args()
    
    # Load data
    data_path = Path(args.data)
    if data_path.suffix == '.csv':
        df = pd.read_csv(data_path)
    elif data_path.suffix == '.parquet':
        df = pd.read_parquet(data_path)
    else:
        logger.error(f"Unsupported file format: {data_path.suffix}")
        sys.exit(1)
    
    logger.info(f"Loaded {len(df)} rows from {data_path}")
    
    # Validate
    is_valid, errors = validate_schema(df, args.schema)
    
    # Save report if requested
    if args.output:
        save_validation_report(errors, args.output, is_valid)
    
    # Exit with appropriate code
    if is_valid:
        logger.info("Validation PASSED")
        sys.exit(0)
    else:
        logger.error(f"Validation FAILED with {len(errors)} errors")
        for error in errors[:10]:  # Print first 10 errors
            logger.error(f"  - {error}")
        sys.exit(1)

if __name__ == '__main__':
    main()