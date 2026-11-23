"""
Validator module for schema validation of input and output data.

This module provides functions to validate DataFrames against JSON/YAML schemas
defined in the contracts directory. It ensures data integrity and compliance
with project specifications.
"""

import logging
import json
import yaml
from typing import Any, Dict, List, Optional, Tuple
from pathlib import Path
import pandas as pd
from utils.logger import get_logger

# Configure logger
logger = get_logger(__name__)

# Constants
PROJECT_ROOT = Path(__file__).parent.parent.parent
CONTRACTS_DIR = PROJECT_ROOT / "contracts"
DATASET_SCHEMA_PATH = CONTRACTS_DIR / "dataset.schema.yaml"
OUTPUT_SCHEMA_PATH = CONTRACTS_DIR / "output.schema.yaml"

# Schema cache to avoid reloading
_schema_cache: Dict[str, Dict] = {}

def load_schema(schema_path: Path) -> Dict:
    """
    Load a schema from a YAML file.
    
    Args:
        schema_path: Path to the schema YAML file.
        
    Returns:
        Dictionary containing the schema definition.
        
    Raises:
        FileNotFoundError: If the schema file does not exist.
        yaml.YAMLError: If the YAML file is malformed.
    """
    cache_key = str(schema_path)
    if cache_key in _schema_cache:
        return _schema_cache[cache_key]
    
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(schema_path, 'r') as f:
        schema = yaml.safe_load(f)
    
    _schema_cache[cache_key] = schema
    logger.debug(f"Loaded schema from {schema_path}")
    return schema

def validate_dataframe_against_schema(
    df: pd.DataFrame, 
    schema: Dict, 
    schema_name: str = "unknown"
) -> Tuple[bool, List[str]]:
    """
    Validate a DataFrame against a JSON schema definition.
    
    Args:
        df: The DataFrame to validate.
        schema: The schema definition (loaded from YAML).
        schema_name: Name of the schema for logging purposes.
        
    Returns:
        Tuple of (is_valid, list_of_errors).
    """
    errors = []
    properties = schema.get('properties', {})
    required_fields = schema.get('required', [])
    
    # Check required columns
    missing_columns = set(required_fields) - set(df.columns)
    if missing_columns:
        errors.append(f"Missing required columns: {missing_columns}")
        return False, errors
    
    # Validate each column against schema properties
    for col_name, col_props in properties.items():
        if col_name not in df.columns:
            continue  # Already handled by required check
        
        col_data = df[col_name]
        
        # Type validation
        expected_type = col_props.get('type')
        if expected_type:
            if expected_type == 'integer':
                if not pd.api.types.is_integer_dtype(col_data):
                    # Allow float columns that contain only integers
                    if not pd.api.types.is_float_dtype(col_data) or not col_data.equals(col_data.astype(int)):
                        errors.append(f"Column '{col_name}' should be integer type")
            elif expected_type == 'number':
                if not (pd.api.types.is_integer_dtype(col_data) or pd.api.types.is_float_dtype(col_data)):
                    errors.append(f"Column '{col_name}' should be number type")
            elif expected_type == 'string':
                if not pd.api.types.is_string_dtype(col_data) and not pd.api.types.is_object_dtype(col_data):
                    errors.append(f"Column '{col_name}' should be string type")
            elif expected_type == 'array':
                # Check if all elements are lists/arrays
                if not col_data.apply(lambda x: isinstance(x, (list, tuple))).all():
                    errors.append(f"Column '{col_name}' should contain array values")
        
        # Minimum value validation
        if 'minimum' in col_props:
            min_val = col_props['minimum']
            if pd.api.types.is_numeric_dtype(col_data):
                if (col_data < min_val).any():
                    errors.append(f"Column '{col_name}' has values below minimum {min_val}")
        
        # Enum validation
        if 'enum' in col_props:
            allowed_values = col_props['enum']
            invalid_values = set(col_data.unique()) - set(allowed_values)
            if invalid_values:
                errors.append(f"Column '{col_name}' contains invalid values: {invalid_values}")
    
    return len(errors) == 0, errors

def validate_input_schema(df: pd.DataFrame) -> Tuple[bool, List[str]]:
    """
    Validate a DataFrame against the input dataset schema (T007a).
    
    Args:
        df: The DataFrame to validate.
        
    Returns:
        Tuple of (is_valid, list_of_errors).
    """
    logger.info("Validating input dataset against dataset.schema.yaml")
    
    try:
        schema = load_schema(DATASET_SCHEMA_PATH)
    except FileNotFoundError as e:
        logger.error(f"Cannot find input schema: {e}")
        return False, [str(e)]
    except yaml.YAMLError as e:
        logger.error(f"Invalid YAML in input schema: {e}")
        return False, [str(e)]
    
    is_valid, errors = validate_dataframe_against_schema(df, schema, "dataset.schema.yaml")
    
    if is_valid:
        logger.info("Input dataset validation passed")
    else:
        logger.warning(f"Input dataset validation failed with {len(errors)} errors: {errors}")
    
    return is_valid, errors

def validate_output_schema(df: pd.DataFrame) -> Tuple[bool, List[str]]:
    """
    Validate a DataFrame against the output schema (T007b).
    
    Args:
        df: The DataFrame to validate.
        
    Returns:
        Tuple of (is_valid, list_of_errors).
    """
    logger.info("Validating output against output.schema.yaml")
    
    try:
        schema = load_schema(OUTPUT_SCHEMA_PATH)
    except FileNotFoundError as e:
        logger.error(f"Cannot find output schema: {e}")
        return False, [str(e)]
    except yaml.YAMLError as e:
        logger.error(f"Invalid YAML in output schema: {e}")
        return False, [str(e)]
    
    is_valid, errors = validate_dataframe_against_schema(df, schema, "output.schema.yaml")
    
    if is_valid:
        logger.info("Output validation passed")
    else:
        logger.warning(f"Output validation failed with {len(errors)} errors: {errors}")
    
    return is_valid, errors

def validate_parsed_data(df: pd.DataFrame) -> Tuple[bool, List[str]]:
    """
    Main validation function for parsed data from T014a.
    
    This function validates the parsed DataFrame against the dataset schema
    (T007a) to ensure all required fields are present and have correct types.
    
    Args:
        df: The parsed DataFrame from preprocessing.
        
    Returns:
        Tuple of (is_valid, list_of_errors).
        
    Raises:
        ValueError: If validation fails.
    """
    logger.info(f"Validating parsed data with {len(df)} rows")
    
    is_valid, errors = validate_input_schema(df)
    
    if not is_valid:
        error_msg = f"Schema validation failed: {errors}"
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    logger.info("Parsed data validation successful")
    return True, []

def main():
    """
    Main function for standalone testing of the validator.
    
    This function creates a sample DataFrame matching the expected schema
    and validates it.
    """
    logger.info("Running validator self-test")
    
    # Create a sample DataFrame matching the schema
    sample_data = {
        'discharge_id': [123456, 123457],
        'island_width': [0.05, 0.08],
        'tau_e': [0.12, 0.15],
        'confinement_mode': ['H-mode', 'L-mode'],
        'h98y2': [0.95, 0.78],
        'q_min': [1.2, 1.5],
        'q_max': [3.8, 4.2],
        'resonant_surface_density': [2.5, 3.1],
        'te_profile': [[1.0, 2.0, 3.0], [1.5, 2.5, 3.5]],
        'ne_profile': [[0.5, 1.0, 1.5], [0.6, 1.1, 1.6]]
    }
    
    df = pd.DataFrame(sample_data)
    
    try:
        is_valid, errors = validate_parsed_data(df)
        if is_valid:
            print("✓ Validation passed successfully")
            return 0
        else:
            print(f"✗ Validation failed: {errors}")
            return 1
    except Exception as e:
        print(f"✗ Validation error: {e}")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())
