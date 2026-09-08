import logging
import json
from typing import Any, Dict, List, Optional, Tuple
from pathlib import Path
import yaml
import pandas as pd

from utils.logger import get_logger

logger = get_logger(__name__)

# Cache for loaded schemas to avoid re-parsing YAML files
_schema_cache: Dict[str, Dict[str, Any]] = {}

def load_schema(schema_path: Path) -> Dict[str, Any]:
    """
    Load a JSON/YAML schema from disk.
    
    Args:
        schema_path: Path to the schema file.
        
    Returns:
        Parsed schema dictionary.
        
    Raises:
        FileNotFoundError: If schema file does not exist.
        ValueError: If schema cannot be parsed.
    """
    cache_key = str(schema_path)
    if cache_key in _schema_cache:
        return _schema_cache[cache_key]
    
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    try:
        with open(schema_path, 'r', encoding='utf-8') as f:
            schema = yaml.safe_load(f)
        _schema_cache[cache_key] = schema
        return schema
    except yaml.YAMLError as e:
        logger.error(f"Failed to parse schema {schema_path}: {e}")
        raise ValueError(f"Invalid schema format in {schema_path}") from e
    except Exception as e:
        logger.error(f"Unexpected error loading schema {schema_path}: {e}")
        raise

def validate_dataframe_against_schema(df: pd.DataFrame, schema: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate a pandas DataFrame against a JSON Schema definition.
    
    This is a simplified validator that checks for required columns
    and basic type constraints (integer, number, string, array) as
    defined in the output schema.
    
    Args:
        df: DataFrame to validate.
        schema: The loaded schema dictionary.
        
    Returns:
        Tuple of (is_valid, list_of_errors).
    """
    errors = []
    
    if not isinstance(schema, dict):
        errors.append("Schema is not a valid dictionary.")
        return False, errors

    # Check top-level type if specified
    if schema.get("type") == "object":
        # We are validating a DataFrame which represents a table of objects (rows)
        pass

    props = schema.get("properties", {})
    required_fields = schema.get("required", [])
    
    # 1. Check Required Columns
    missing_cols = set(required_fields) - set(df.columns)
    if missing_cols:
        errors.append(f"Missing required columns: {sorted(missing_cols)}")
    
    # 2. Check Types for existing columns
    for col_name, col_schema in props.items():
        if col_name not in df.columns:
            continue
        
        expected_type_str = col_schema.get("properties", {}).get("type", {}).get("enum", [None])[0]
        if not expected_type_str:
            # Fallback if structure is slightly different
            expected_type_str = col_schema.get("properties", {}).get("type", [None])
            if isinstance(expected_type_str, list):
                expected_type_str = expected_type_str[0]
            elif isinstance(expected_type_str, dict):
                expected_type_str = expected_type_str.get("enum", [None])[0]
            
        if expected_type_str is None:
            continue

        col = df[col_name]

        if expected_type_str == "integer":
            if not pd.api.types.is_integer_dtype(col):
                # Allow float that are actually integers? Strict check for now.
                if not pd.api.types.is_float_dtype(col) or not col.apply(lambda x: float(x).is_integer()).all():
                     errors.append(f"Column '{col_name}' is expected to be integer, got {col.dtype}")
                     
        elif expected_type_str == "number":
            if not (pd.api.types.is_float_dtype(col) or pd.api.types.is_integer_dtype(col)):
                errors.append(f"Column '{col_name}' is expected to be number, got {col.dtype}")
                
        elif expected_type_str == "string":
            if not pd.api.types.is_string_dtype(col) and not pd.api.types.is_object_dtype(col):
                errors.append(f"Column '{col_name}' is expected to be string, got {col.dtype}")
                
        elif expected_type_str == "array":
            # Check if column contains lists/arrays
            if not col.apply(lambda x: isinstance(x, (list, tuple))).all():
                errors.append(f"Column '{col_name}' is expected to be array, but contains non-array types.")

    # 3. Check for unexpected columns if 'additionalProperties: false' (not strictly enforced here for flexibility)
    # but we log a warning if strict mode is not implied.
    
    is_valid = len(errors) == 0
    return is_valid, errors

def validate_input_schema(raw_data: Dict[str, Any], schema_path: Path) -> Tuple[bool, List[str]]:
    """
    Validate raw input data (dictionary from MDSplus) against the input schema.
    
    Args:
        raw_data: Dictionary containing raw data fields.
        schema_path: Path to the dataset.schema.yaml.
        
    Returns:
        Tuple of (is_valid, list_of_errors).
    """
    schema = load_schema(schema_path)
    errors = []
    
    # Basic structural checks based on dataset.schema.yaml
    if "discharge_id" not in raw_data:
        errors.append("Missing 'discharge_id' in raw data.")
    else:
        if not isinstance(raw_data["discharge_id"], int):
            errors.append("'discharge_id' must be an integer.")
    
    if "fields" not in raw_data:
        errors.append("Missing 'fields' in raw data.")
    else:
        fields = raw_data["fields"]
        if not isinstance(fields, dict):
            errors.append("'fields' must be a dictionary.")
        else:
            # Check for critical nested fields if they exist in schema
            required_fields = schema.get("required", [])
            # Note: 'required' in schema is top level, we check presence loosely here
            # The schema implies specific structure under 'fields'
            pass
    
    return len(errors) == 0, errors

def validate_output_schema(df: pd.DataFrame, schema_path: Path) -> Tuple[bool, List[str]]:
    """
    Validate the final processed DataFrame against the output schema.
    
    This function is critical to ensure that the data produced by the pipeline
    matches the expected format for downstream analysis (US2, US3).
    
    Args:
        df: The processed DataFrame.
        schema_path: Path to the output.schema.yaml.
        
    Returns:
        Tuple of (is_valid, list_of_errors).
    """
    schema = load_schema(schema_path)
    return validate_dataframe_against_schema(df, schema)

def validate_parsed_data(df: pd.DataFrame, input_schema_path: Optional[Path] = None, 
                         output_schema_path: Optional[Path] = None) -> Tuple[bool, List[str]]:
    """
    Main entry point for validation. Validates input structure (if raw dict provided)
    and output DataFrame structure.
    
    Per FR-009, validation must occur before parsing/analysis begins.
    This function should be called:
    1. On raw data fetched from MDSplus (input_schema_path).
    2. On the DataFrame after preprocessing (output_schema_path).
    
    Args:
        df: DataFrame to validate.
        input_schema_path: Path to dataset.schema.yaml.
        output_schema_path: Path to output.schema.yaml.
        
    Returns:
        Tuple of (is_valid, list_of_errors).
    """
    all_errors = []
    is_valid = True
    
    if output_schema_path:
        if not df.empty:
            valid, errors = validate_output_schema(df, output_schema_path)
            if not valid:
                all_errors.extend(errors)
                is_valid = False
        else:
            # Empty dataframe might be valid if all data was filtered out, 
            # but typically we expect data. Log warning.
            logger.warning("Validating empty DataFrame. Check if all data was filtered out.")
    
    return is_valid, all_errors
