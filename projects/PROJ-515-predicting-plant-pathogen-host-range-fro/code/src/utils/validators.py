"""
Validation utilities to enforce contract schemas.

This module provides functions to validate data against JSON/YAML schemas
defined in the contracts/ directory.
"""
import os
import json
import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Union
from loguru import logger
import pandas as pd
import jsonschema
from jsonschema import validate, ValidationError, SchemaError

# Import config for path constants
from src.config import Paths

# Ensure jsonschema is available (it's a dependency for validation)
# If not installed, this will fail loudly as required
try:
    import jsonschema
except ImportError:
    logger.error("jsonschema library is required but not installed. Please install it.")
    raise


def _get_contracts_dir() -> Path:
    """Get the contracts directory path."""
    return Path(Paths.CONTRACTS_DIR)


def _load_schema(schema_name: str) -> Dict[str, Any]:
    """
    Load a schema from the contracts directory.
    
    Args:
        schema_name: Name of the schema file (e.g., 'dataset.schema.yaml')
        
    Returns:
        The schema as a dictionary
        
    Raises:
        FileNotFoundError: If the schema file doesn't exist
        yaml.YAMLError: If the schema file is not valid YAML
    """
    contracts_dir = _get_contracts_dir()
    schema_path = contracts_dir / schema_name
    
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(schema_path, 'r') as f:
        try:
            schema = yaml.safe_load(f)
        except yaml.YAMLError as e:
            logger.error(f"Invalid YAML in schema {schema_name}: {e}")
            raise
    
    return schema


def validate_schema_exists(schema_name: str) -> bool:
    """
    Check if a schema file exists in the contracts directory.
    
    Args:
        schema_name: Name of the schema file
        
    Returns:
        True if the schema exists, False otherwise
    """
    contracts_dir = _get_contracts_dir()
    schema_path = contracts_dir / schema_name
    return schema_path.exists()


def list_available_schemas() -> List[str]:
    """
    List all available schema files in the contracts directory.
    
    Returns:
        List of schema filenames
    """
    contracts_dir = _get_contracts_dir()
    if not contracts_dir.exists():
        logger.warning(f"Contracts directory does not exist: {contracts_dir}")
        return []
    
    schemas = []
    for file in contracts_dir.iterdir():
        if file.is_file() and file.suffix in ['.yaml', '.yml']:
            schemas.append(file.name)
    
    return sorted(schemas)


def validate_all_schemas_exist() -> Tuple[bool, List[str]]:
    """
    Validate that all expected schema files exist.
    
    Expected schemas based on T007:
    - dataset.schema.yaml
    - genomic_features.schema.yaml
    - interaction.schema.yaml
    - model_output.schema.yaml
    
    Returns:
        Tuple of (all_exist, list_of_missing_schemas)
    """
    expected_schemas = [
        'dataset.schema.yaml',
        'genomic_features.schema.yaml',
        'interaction.schema.yaml',
        'model_output.schema.yaml'
    ]
    
    missing = []
    for schema in expected_schemas:
        if not validate_schema_exists(schema):
            missing.append(schema)
    
    return len(missing) == 0, missing


def check_required_fields(data: Dict[str, Any], required_fields: List[str]) -> Tuple[bool, List[str]]:
    """
    Check if all required fields are present in a dictionary.
    
    Args:
        data: The data dictionary to check
        required_fields: List of required field names
        
    Returns:
        Tuple of (all_present, list_of_missing_fields)
    """
    missing = []
    for field in required_fields:
        if field not in data:
            missing.append(field)
    
    return len(missing) == 0, missing


def validate_dataframe_schema(df: pd.DataFrame, schema_name: str) -> Tuple[bool, str]:
    """
    Validate a DataFrame against a schema.
    
    This function checks:
    1. All required columns exist
    2. Column types match the schema (if specified)
    
    Args:
        df: The DataFrame to validate
        schema_name: Name of the schema file
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        schema = _load_schema(schema_name)
    except FileNotFoundError as e:
        return False, str(e)
    except yaml.YAMLError as e:
        return False, f"Invalid schema format: {e}"
    
    # Get required columns from schema
    required_columns = schema.get('required_columns', [])
    column_types = schema.get('column_types', {})
    
    # Check required columns
    missing_columns = []
    for col in required_columns:
        if col not in df.columns:
            missing_columns.append(col)
    
    if missing_columns:
        return False, f"Missing required columns: {missing_columns}"
    
    # Check column types
    type_errors = []
    for col, expected_type in column_types.items():
        if col in df.columns:
            actual_type = df[col].dtype
            # Simple type checking
            type_mapping = {
                'int': ['int64', 'int32', 'int'],
                'float': ['float64', 'float32', 'float'],
                'str': ['object', 'string'],
                'bool': ['bool']
            }
            
            expected_types = type_mapping.get(expected_type, [expected_type])
            if str(actual_type) not in expected_types:
                type_errors.append(f"Column '{col}': expected {expected_type}, got {actual_type}")
    
    if type_errors:
        return False, "Type errors: " + "; ".join(type_errors)
    
    return True, "Schema validation passed"


def validate_data(data: Any, schema_name: str) -> Tuple[bool, str]:
    """
    Validate data (dict or DataFrame) against a schema using jsonschema.
    
    Args:
        data: The data to validate (dict or DataFrame)
        schema_name: Name of the schema file
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        schema = _load_schema(schema_name)
    except FileNotFoundError as e:
        return False, f"Schema not found: {e}"
    except yaml.YAMLError as e:
        return False, f"Invalid schema: {e}"
    
    # Convert DataFrame to dict if needed
    if isinstance(data, pd.DataFrame):
        data = data.to_dict(orient='records')
    
    try:
        validate(instance=data, schema=schema)
        return True, "Validation successful"
    except ValidationError as e:
        return False, f"Validation error: {e.message}"
    except SchemaError as e:
        return False, f"Schema error: {e.message}"


def validate_file(file_path: Union[str, Path], schema_name: str) -> Tuple[bool, str]:
    """
    Validate a file (JSON or YAML) against a schema.
    
    Args:
        file_path: Path to the file to validate
        schema_name: Name of the schema file
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        return False, f"File not found: {file_path}"
    
    # Load the file
    try:
        with open(file_path, 'r') as f:
            if file_path.suffix in ['.yaml', '.yml']:
                data = yaml.safe_load(f)
            elif file_path.suffix == '.json':
                data = json.load(f)
            else:
                return False, f"Unsupported file format: {file_path.suffix}"
    except json.JSONDecodeError as e:
        return False, f"Invalid JSON: {e}"
    except yaml.YAMLError as e:
        return False, f"Invalid YAML: {e}"
    
    # Validate against schema
    return validate_data(data, schema_name)


def validate_pipeline_output(output_dir: Union[str, Path]) -> Dict[str, Any]:
    """
    Validate all outputs from a pipeline run against their respective schemas.
    
    Expected outputs:
    - data/processed/features_matrix.csv -> genomic_features.schema.yaml
    - data/processed/train_val_split.json -> dataset.schema.yaml
    - data/models/model.pkl -> model_output.schema.yaml (conceptual)
    - data/reports/data_quality_report.json -> data_quality.schema.yaml (if exists)
    
    Args:
        output_dir: Path to the output directory
        
    Returns:
        Dictionary with validation results for each output
    """
    output_dir = Path(output_dir)
    results = {}
    
    # Define expected outputs and their schemas
    validations = [
        ('data/processed/features_matrix.csv', 'genomic_features.schema.yaml'),
        ('data/processed/train_val_split.json', 'dataset.schema.yaml'),
        ('data/processed/holdout_set.json', 'dataset.schema.yaml'),
        ('data/reports/data_quality_report.json', None),  # No schema defined yet
        ('data/reports/shap_values_all.npy', None),  # Binary, no schema
        ('data/reports/feature_importance.csv', None),  # CSV, custom validation
        ('data/reports/significant_features.tsv', None),  # TSV, custom validation
    ]
    
    for relative_path, schema_name in validations:
        full_path = output_dir / relative_path
        
        if not full_path.exists():
            results[relative_path] = {
                'exists': False,
                'valid': False,
                'error': 'File not found'
            }
            continue
        
        results[relative_path] = {
            'exists': True,
            'valid': True,
            'error': None
        }
        
        if schema_name:
            is_valid, error_msg = validate_file(full_path, schema_name)
            results[relative_path]['valid'] = is_valid
            if not is_valid:
                results[relative_path]['error'] = error_msg
    
    return results