"""
Schema validation utilities for the llmXive research pipeline.

This module provides functions to validate data files against YAML schemas,
ensuring data integrity before and after processing steps.
"""
import os
import sys
import logging
from typing import Dict, Any, Optional, List, Tuple
import re
import yaml
import pandas as pd
from pathlib import Path

# Configure logger
logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Custom exception for validation errors."""
    pass


def load_schema(schema_path: str) -> Dict[str, Any]:
    """
    Load a YAML schema file.
    
    Args:
        schema_path: Path to the schema YAML file.
        
    Returns:
        Dictionary containing the schema definition.
        
    Raises:
        ValidationError: If the schema file cannot be loaded or is invalid.
    """
    if not os.path.exists(schema_path):
        raise ValidationError(f"Schema file not found: {schema_path}")
    
    try:
        with open(schema_path, 'r') as f:
            schema = yaml.safe_load(f)
        if schema is None:
            raise ValidationError(f"Schema file is empty: {schema_path}")
        return schema
    except yaml.YAMLError as e:
        raise ValidationError(f"Invalid YAML in schema {schema_path}: {e}")
    except Exception as e:
        raise ValidationError(f"Error loading schema {schema_path}: {e}")


def validate_field_type(value: Any, expected_type: str, field_name: str) -> bool:
    """
    Validate that a value matches the expected type.
    
    Args:
        value: The value to check.
        expected_type: Expected type string ('string', 'float', 'integer', 'boolean').
        field_name: Name of the field (for error messages).
        
    Returns:
        True if valid, False otherwise.
        
    Raises:
        ValidationError: If the type does not match.
    """
    type_mapping = {
        'string': str,
        'float': (int, float),
        'integer': int,
        'boolean': bool
    }
    
    if expected_type not in type_mapping:
        raise ValidationError(f"Unknown type '{expected_type}' for field '{field_name}'")
    
    expected_python_type = type_mapping[expected_type]
    
    # Special handling for booleans (since bool is subclass of int in Python)
    if expected_type == 'boolean':
        if not isinstance(value, bool):
            raise ValidationError(f"Field '{field_name}' must be boolean, got {type(value).__name__}")
        return True
        
    if expected_type == 'integer':
        if isinstance(value, bool) or not isinstance(value, int):
            raise ValidationError(f"Field '{field_name}' must be integer, got {type(value).__name__}")
        return True
        
    if expected_type == 'float':
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValidationError(f"Field '{field_name}' must be float, got {type(value).__name__}")
        return True
        
    if expected_type == 'string':
        if not isinstance(value, str):
            raise ValidationError(f"Field '{field_name}' must be string, got {type(value).__name__}")
        return True
        
    return False


def validate_value_constraints(value: Any, constraints: Dict[str, Any], field_name: str) -> bool:
    """
    Validate value against constraints (pattern, min, max, allowed_values).
    
    Args:
        value: The value to check.
        constraints: Dictionary of constraint definitions.
        field_name: Name of the field (for error messages).
        
    Returns:
        True if valid, False otherwise.
        
    Raises:
        ValidationError: If constraints are violated.
    """
    if not constraints:
        return True
    
    # Check pattern (for strings)
    if 'pattern' in constraints and isinstance(value, str):
        pattern = constraints['pattern']
        if not re.match(pattern, value):
            raise ValidationError(
                f"Field '{field_name}' value '{value}' does not match pattern '{pattern}'"
            )
    
    # Check min/max (for numbers)
    if 'min' in constraints and isinstance(value, (int, float)):
        if value < constraints['min']:
            raise ValidationError(
                f"Field '{field_name}' value {value} is less than minimum {constraints['min']}"
            )
    
    if 'max' in constraints and isinstance(value, (int, float)):
        if value > constraints['max']:
            raise ValidationError(
                f"Field '{field_name}' value {value} is greater than maximum {constraints['max']}"
            )
    
    # Check allowed values
    if 'allowed_values' in constraints:
        allowed = constraints['allowed_values']
        if value not in allowed:
            raise ValidationError(
                f"Field '{field_name}' value '{value}' not in allowed values: {allowed}"
            )
    
    return True


def validate_record(record: Dict[str, Any], schema: Dict[str, Any]) -> List[str]:
    """
    Validate a single record (row) against a schema.
    
    Args:
        record: Dictionary representing a row.
        schema: Schema definition.
        
    Returns:
        List of error messages (empty if valid).
    """
    errors = []
    fields = schema.get('fields', [])
    
    for field_def in fields:
        field_name = field_def['name']
        field_type = field_def['type']
        constraints = field_def.get('constraints', {})
        
        # Check if required
        if constraints.get('required', False):
            if field_name not in record or record[field_name] is None:
                errors.append(f"Required field '{field_name}' is missing or null")
                continue
        
        if field_name not in record:
            continue
        
        value = record[field_name]
        
        # Type validation
        try:
            validate_field_type(value, field_type, field_name)
        except ValidationError as e:
            errors.append(str(e))
            continue
        
        # Constraint validation
        try:
            validate_value_constraints(value, constraints, field_name)
        except ValidationError as e:
            errors.append(str(e))
    
    return errors


def validate_dataset_file(file_path: str, schema_path: str) -> Tuple[bool, Dict[str, Any]]:
    """
    Validate a dataset CSV file against a schema.
    
    Args:
        file_path: Path to the CSV file.
        schema_path: Path to the schema YAML file.
        
    Returns:
        Tuple of (is_valid, validation_report).
        
    Raises:
        ValidationError: If file or schema cannot be loaded.
    """
    report = {
        'file': file_path,
        'schema': schema_path,
        'valid': True,
        'errors': [],
        'row_count': 0,
        'error_count': 0
    }
    
    # Load schema
    schema = load_schema(schema_path)
    
    # Load CSV
    if not os.path.exists(file_path):
        raise ValidationError(f"Data file not found: {file_path}")
    
    try:
        df = pd.read_csv(file_path)
    except Exception as e:
        raise ValidationError(f"Error reading CSV {file_path}: {e}")
    
    report['row_count'] = len(df)
    
    # Check non-empty rule
    if len(df) == 0:
        report['valid'] = False
        report['errors'].append("File is empty (no data rows)")
        return False, report
    
    # Validate each row
    for idx, row in df.iterrows():
        row_dict = row.to_dict()
        row_errors = validate_record(row_dict, schema)
        if row_errors:
            report['valid'] = False
            for err in row_errors:
                report['errors'].append(f"Row {idx}: {err}")
            report['error_count'] += 1
    
    # Check validation rules from schema
    for rule in schema.get('validation_rules', []):
        rule_name = rule['rule']
        check_code = rule['check']
        
        try:
            if rule_name == 'unique_dates':
                # Check for duplicate dates per source/metric
                if 'source' in df.columns and 'metric' in df.columns and 'date' in df.columns:
                    duplicates = df.groupby(['source', 'metric', 'date']).size()
                    if duplicates.max() > 1:
                        report['valid'] = False
                        report['errors'].append(f"Duplicate dates found: {duplicates[duplicates > 1].to_dict()}")
            elif rule_name == 'non_empty':
                # Already checked above
                pass
            elif rule_name == 'column_presence':
                # Handled separately in validate_dataset_file_structure
                pass
        except Exception as e:
            report['valid'] = False
            report['errors'].append(f"Rule '{rule_name}' check failed: {e}")
    
    return report['valid'], report


def validate_output_file(file_path: str, schema_path: str, output_type: str) -> Tuple[bool, Dict[str, Any]]:
    """
    Validate an output file (processed data, results) against a schema.
    
    Args:
        file_path: Path to the output CSV file.
        schema_path: Path to the schema YAML file.
        output_type: Type of output ('processed_timeseries', 'granger_results', 'correlation_results').
        
    Returns:
        Tuple of (is_valid, validation_report).
        
    Raises:
        ValidationError: If file or schema cannot be loaded.
    """
    report = {
        'file': file_path,
        'schema': schema_path,
        'output_type': output_type,
        'valid': True,
        'errors': [],
        'row_count': 0,
        'error_count': 0
    }
    
    # Load schema
    schema = load_schema(schema_path)
    
    # Get the specific schema for this output type
    if output_type == 'processed_timeseries':
        sub_schema = schema.get('processed_timeseries', {})
    elif output_type == 'granger_results':
        sub_schema = schema.get('granger_results', {})
    elif output_type == 'correlation_results':
        sub_schema = schema.get('correlation_results', {})
    else:
        raise ValidationError(f"Unknown output type: {output_type}")
    
    if not sub_schema:
        raise ValidationError(f"No schema definition found for output type: {output_type}")
    
    # Load CSV
    if not os.path.exists(file_path):
        raise ValidationError(f"Output file not found: {file_path}")
    
    try:
        df = pd.read_csv(file_path)
    except Exception as e:
        raise ValidationError(f"Error reading CSV {file_path}: {e}")
    
    report['row_count'] = len(df)
    
    # Check non-empty
    if len(df) == 0:
        report['valid'] = False
        report['errors'].append("Output file is empty (no data rows)")
        return False, report
    
    # Validate each row
    for idx, row in df.iterrows():
        row_dict = row.to_dict()
        row_errors = validate_record(row_dict, sub_schema)
        if row_errors:
            report['valid'] = False
            for err in row_errors:
                report['errors'].append(f"Row {idx}: {err}")
            report['error_count'] += 1
    
    return report['valid'], report


def validate_against_schema(
    data_path: str,
    schema_path: str,
    output_type: Optional[str] = None
) -> Tuple[bool, Dict[str, Any]]:
    """
    Generic validation function that selects the appropriate validator.
    
    Args:
        data_path: Path to the data file.
        schema_path: Path to the schema file.
        output_type: Optional output type hint. If None, tries to infer.
        
    Returns:
        Tuple of (is_valid, report).
    """
    if output_type is None:
        # Infer from filename
        filename = os.path.basename(data_path).lower()
        if 'granger' in filename:
            output_type = 'granger_results'
        elif 'correlation' in filename or 'analysis' in filename:
            output_type = 'correlation_results'
        elif 'aligned' in filename or 'timeseries' in filename:
            output_type = 'processed_timeseries'
        else:
            # Default to dataset schema
            return validate_dataset_file(data_path, schema_path)
    
    return validate_output_file(data_path, schema_path, output_type)


def validate_output_file_structure(file_path: str, expected_columns: List[str]) -> Tuple[bool, List[str]]:
    """
    Validate that a file has the expected columns.
    
    Args:
        file_path: Path to the CSV file.
        expected_columns: List of expected column names.
        
    Returns:
        Tuple of (is_valid, missing_columns).
    """
    if not os.path.exists(file_path):
        return False, [f"File not found: {file_path}"]
    
    try:
        df = pd.read_csv(file_path)
    except Exception as e:
        return False, [f"Error reading file: {e}"]
    
    missing = [col for col in expected_columns if col not in df.columns]
    return len(missing) == 0, missing


def validate_dataset_file_structure(file_path: str, expected_columns: List[str]) -> Tuple[bool, List[str]]:
    """
    Validate that a dataset file has the expected columns.
    
    Args:
        file_path: Path to the CSV file.
        expected_columns: List of expected column names.
        
    Returns:
        Tuple of (is_valid, missing_columns).
    """
    return validate_output_file_structure(file_path, expected_columns)


def main():
    """
    Command-line interface for schema validation.
    
    Usage:
        python -m code.utils.validation --data <path> --schema <path> [--type <output_type>]
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Validate data files against YAML schemas.')
    parser.add_argument('--data', required=True, help='Path to the data file to validate')
    parser.add_argument('--schema', required=True, help='Path to the schema file')
    parser.add_argument('--type', dest='output_type', default=None,
                      help='Output type (processed_timeseries, granger_results, correlation_results)')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.basicConfig(level=logging.INFO)
    else:
        logging.basicConfig(level=logging.WARNING)
    
    try:
        is_valid, report = validate_against_schema(
            args.data,
            args.schema,
            args.output_type
        )
        
        if is_valid:
            logger.info(f"Validation PASSED for {args.data}")
            logger.info(f"  Rows: {report['row_count']}")
            logger.info(f"  Errors: {report['error_count']}")
            sys.exit(0)
        else:
            logger.error(f"Validation FAILED for {args.data}")
            logger.error(f"  Rows: {report['row_count']}")
            logger.error(f"  Errors: {report['error_count']}")
            for err in report['errors'][:10]:  # Show first 10 errors
                logger.error(f"    - {err}")
            if len(report['errors']) > 10:
                logger.error(f"    ... and {len(report['errors']) - 10} more errors")
            sys.exit(1)
            
    except ValidationError as e:
        logger.error(f"Validation error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(2)


if __name__ == '__main__':
    main()