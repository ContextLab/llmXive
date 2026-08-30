"""
Validation utility for schema-based data validation.

This module provides functions to load YAML schemas and validate
datasets and output files against them.
"""
import os
import sys
import logging
from typing import Dict, Any, Optional, List, Tuple
import re
import yaml
import pandas as pd
from datetime import datetime

# Import logging utility from sibling module
try:
    from utils.logging import get_logger
except ImportError:
    # Fallback if running as __main__ or direct import
    def get_logger(name: str = __name__) -> logging.Logger:
        logger = logging.getLogger(name)
        if not logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger

logger = get_logger(__name__)


class ValidationError(Exception):
    """Custom exception for validation errors."""
    pass


def load_schema(schema_path: str) -> Dict[str, Any]:
    """
    Load a YAML schema file.
    
    Args:
        schema_path: Path to the YAML schema file.
        
    Returns:
        Dictionary containing the schema definition.
        
    Raises:
        ValidationError: If the file cannot be loaded or is invalid YAML.
    """
    if not os.path.exists(schema_path):
        raise ValidationError(f"Schema file not found: {schema_path}")
    
    try:
        with open(schema_path, 'r', encoding='utf-8') as f:
            schema = yaml.safe_load(f)
        
        if schema is None:
            raise ValidationError(f"Schema file is empty: {schema_path}")
        
        logger.info(f"Successfully loaded schema from {schema_path}")
        return schema
    except yaml.YAMLError as e:
        raise ValidationError(f"Invalid YAML in schema {schema_path}: {e}")
    except Exception as e:
        raise ValidationError(f"Error loading schema {schema_path}: {e}")


def validate_field_type(value: Any, expected_type: str) -> bool:
    """
    Validate that a value matches the expected type.
    
    Args:
        value: The value to check.
        expected_type: Expected type as string ('string', 'integer', 'float', 'boolean', 'date', 'datetime').
        
    Returns:
        True if the type matches, False otherwise.
    """
    if expected_type == 'string':
        return isinstance(value, str)
    elif expected_type == 'integer':
        return isinstance(value, int) and not isinstance(value, bool)
    elif expected_type == 'float':
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    elif expected_type == 'boolean':
        return isinstance(value, bool)
    elif expected_type == 'date':
        # Check if it's a string in ISO format or a datetime.date object
        if isinstance(value, datetime):
            return True
        if isinstance(value, str):
            try:
                datetime.strptime(value, '%Y-%m-%d')
                return True
            except ValueError:
                return False
        return False
    elif expected_type == 'datetime':
        if isinstance(value, datetime):
            return True
        if isinstance(value, str):
            try:
                datetime.fromisoformat(value.replace('Z', '+00:00'))
                return True
            except ValueError:
                return False
        return False
    else:
        logger.warning(f"Unknown type: {expected_type}")
        return False


def validate_value_constraints(value: Any, constraints: Dict[str, Any]) -> bool:
    """
    Validate that a value meets specified constraints.
    
    Args:
        value: The value to check.
        constraints: Dictionary of constraints (e.g., {'min': 0, 'max': 100, 'pattern': r'^[A-Z]+$'}).
        
    Returns:
        True if all constraints are satisfied, False otherwise.
    """
    if 'min' in constraints and value is not None:
        if value < constraints['min']:
            return False
    
    if 'max' in constraints and value is not None:
        if value > constraints['max']:
            return False
    
    if 'pattern' in constraints and isinstance(value, str):
        if not re.match(constraints['pattern'], value):
            return False
    
    if 'enum' in constraints and value is not None:
        if value not in constraints['enum']:
            return False
    
    if 'min_length' in constraints and isinstance(value, str):
        if len(value) < constraints['min_length']:
            return False
    
    if 'max_length' in constraints and isinstance(value, str):
        if len(value) > constraints['max_length']:
            return False
    
    return True


def validate_record(record: Dict[str, Any], schema: Dict[str, Any]) -> List[str]:
    """
    Validate a single record against a schema.
    
    Args:
        record: Dictionary representing a single row/record.
        schema: The schema definition.
        
    Returns:
        List of error messages (empty if valid).
    """
    errors = []
    properties = schema.get('properties', {})
    required_fields = schema.get('required', [])
    
    # Check required fields
    for field in required_fields:
        if field not in record or record[field] is None:
            errors.append(f"Missing required field: {field}")
    
    # Validate each field
    for field_name, field_value in record.items():
        if field_name not in properties:
            # Unknown field - could be an error or just ignored based on policy
            # For now, we'll log a warning but not fail
            logger.debug(f"Unknown field in record: {field_name}")
            continue
        
        field_def = properties[field_name]
        expected_type = field_def.get('type')
        constraints = field_def.get('constraints', {})
        
        # Skip validation for null values if not required
        if field_value is None:
            if field_name in required_fields:
                errors.append(f"Field {field_name} is required but is null")
            continue
        
        # Type validation
        if expected_type and not validate_field_type(field_value, expected_type):
            errors.append(
                f"Field '{field_name}' has invalid type. Expected {expected_type}, got {type(field_value).__name__}"
            )
            continue
        
        # Constraint validation
        if constraints and not validate_value_constraints(field_value, constraints):
            errors.append(
                f"Field '{field_name}' violates constraints: {constraints}"
            )
    
    return errors


def validate_dataset_file(file_path: str, schema_path: str) -> Dict[str, Any]:
    """
    Validate a CSV dataset file against a schema.
    
    Args:
        file_path: Path to the CSV file.
        schema_path: Path to the YAML schema file.
        
    Returns:
        Dictionary with validation results.
    """
    result = {
        'file': file_path,
        'schema': schema_path,
        'valid': False,
        'total_rows': 0,
        'valid_rows': 0,
        'invalid_rows': 0,
        'errors': [],
        'timestamp': datetime.now().isoformat()
    }
    
    try:
        # Load schema
        schema = load_schema(schema_path)
        
        # Load dataset
        if not os.path.exists(file_path):
            raise ValidationError(f"Dataset file not found: {file_path}")
        
        df = pd.read_csv(file_path)
        result['total_rows'] = len(df)
        
        # Validate each row
        invalid_indices = []
        for idx, row in df.iterrows():
            record = row.to_dict()
            errors = validate_record(record, schema)
            if errors:
                invalid_indices.append(idx)
                result['errors'].append({
                    'row': idx,
                    'errors': errors
                })
        
        result['valid_rows'] = result['total_rows'] - len(invalid_indices)
        result['invalid_rows'] = len(invalid_indices)
        result['valid'] = result['invalid_rows'] == 0
        
        if result['valid']:
            logger.info(f"Validation passed for {file_path}: {result['valid_rows']} rows")
        else:
            logger.warning(
                f"Validation failed for {file_path}: {result['invalid_rows']} invalid rows out of {result['total_rows']}"
            )
        
    except Exception as e:
        result['errors'].append({'general': str(e)})
        logger.error(f"Validation error for {file_path}: {e}")
    
    return result


def validate_output_file_structure(file_path: str, schema_path: str) -> Dict[str, Any]:
    """
    Validate an output file (e.g., JSON, CSV) against a schema.
    
    This is a specialized version for output files that may have
    different structure requirements.
    
    Args:
        file_path: Path to the output file.
        schema_path: Path to the YAML schema file.
        
    Returns:
        Dictionary with validation results.
    """
    result = {
        'file': file_path,
        'schema': schema_path,
        'valid': False,
        'errors': [],
        'timestamp': datetime.now().isoformat()
    }
    
    try:
        # Load schema
        schema = load_schema(schema_path)
        
        # Check file existence
        if not os.path.exists(file_path):
            raise ValidationError(f"Output file not found: {file_path}")
        
        # Determine file type and load accordingly
        if file_path.endswith('.csv'):
            df = pd.read_csv(file_path)
            
            # Validate structure based on schema
            expected_columns = list(schema.get('properties', {}).keys())
            actual_columns = list(df.columns)
            
            missing_columns = set(expected_columns) - set(actual_columns)
            if missing_columns:
                result['errors'].append(
                    f"Missing columns: {missing_columns}"
                )
            
            # Check for required columns
            required_columns = schema.get('required', [])
            missing_required = set(required_columns) - set(actual_columns)
            if missing_required:
                result['errors'].append(
                    f"Missing required columns: {missing_required}"
                )
            
            result['valid'] = len(result['errors']) == 0
            
        elif file_path.endswith('.json'):
            import json
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Validate JSON structure
            # This is a simplified check - more complex validation would depend on schema
            if not isinstance(data, dict):
                result['errors'].append("JSON root must be an object")
            else:
                # Check required fields
                required = schema.get('required', [])
                for field in required:
                    if field not in data:
                        result['errors'].append(f"Missing required field: {field}")
            
            result['valid'] = len(result['errors']) == 0
        else:
            raise ValidationError(f"Unsupported file type: {file_path}")
        
        if result['valid']:
            logger.info(f"Output validation passed for {file_path}")
        else:
            logger.warning(f"Output validation failed for {file_path}: {result['errors']}")
        
    except Exception as e:
        result['errors'].append(str(e))
        logger.error(f"Output validation error for {file_path}: {e}")
    
    return result


def validate_against_schema(
    data_path: str,
    schema_path: str,
    output_format: str = 'dict'
) -> Any:
    """
    Main entry point for validating data against a schema.
    
    Args:
        data_path: Path to the data file (CSV or JSON).
        schema_path: Path to the YAML schema file.
        output_format: 'dict' for dictionary result, 'bool' for simple pass/fail.
        
    Returns:
        Validation result based on output_format.
    """
    if data_path.endswith('.csv'):
        result = validate_dataset_file(data_path, schema_path)
    else:
        result = validate_output_file_structure(data_path, schema_path)
    
    if output_format == 'bool':
        return result['valid']
    return result


def main():
    """
    Command-line interface for the validation utility.
    
    Usage:
        python -m utils.validation --data <path> --schema <path> [--format dict|bool]
    """
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Validate data files against YAML schemas.'
    )
    parser.add_argument(
        '--data',
        required=True,
        help='Path to the data file (CSV or JSON)'
    )
    parser.add_argument(
        '--schema',
        required=True,
        help='Path to the YAML schema file'
    )
    parser.add_argument(
        '--format',
        choices=['dict', 'bool'],
        default='dict',
        help='Output format (default: dict)'
    )
    
    args = parser.parse_args()
    
    try:
        result = validate_against_schema(
            args.data,
            args.schema,
            args.format
        )
        
        if args.format == 'bool':
            if result:
                print("VALID")
                sys.exit(0)
            else:
                print("INVALID")
                sys.exit(1)
        else:
            import json
            print(json.dumps(result, indent=2, default=str))
            sys.exit(0 if result.get('valid') else 1)
            
    except ValidationError as e:
        logger.error(f"Validation failed: {e}")
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()