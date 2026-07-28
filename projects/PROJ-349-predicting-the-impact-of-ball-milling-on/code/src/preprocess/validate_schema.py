"""
Schema validation logic for the ball milling dataset.

This module enforces the dataset schema defined in contracts/dataset.schema.yaml.
It validates field presence, types, and basic constraints without checking row counts
(row count validation is handled by T015c and T017c).
"""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

import pandas as pd
import yaml

# Import custom exceptions from the project's exception module
from src.utils.exceptions import InsufficientDataError, SchemaValidationError

# Initialize logger
logger = logging.getLogger(__name__)

# Define the expected schema based on contracts/dataset.schema.yaml
# This is a hardcoded representation of the schema to avoid file I/O during validation
# but it should ideally be loaded from the YAML file in production
EXPECTED_SCHEMA = {
    "fields": {
        "experiment_id": {"type": "str", "required": True},
        "source": {"type": "str", "required": True},
        "material_type": {"type": "str", "required": True},
        "milling_speed": {"type": "float", "required": True},
        "milling_time": {"type": "float", "required": True},
        "ball_to_powder_ratio": {"type": "float", "required": True},
        "youngs_modulus": {"type": "float", "required": True},
        "density": {"type": "float", "required": True},
        "d10": {"type": "float", "required": True},
        "d50": {"type": "float", "required": True},
        "d90": {"type": "float", "required": True},
        "process_duration": {"type": "float", "required": True}
    }
}

def load_schema(schema_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load schema definition from YAML file.
    
    Args:
        schema_path: Path to the schema YAML file. If None, uses default path.
        
    Returns:
        Dictionary containing the schema definition.
        
    Raises:
        SchemaValidationError: If the schema file cannot be loaded or is invalid.
    """
    if schema_path is None:
        schema_path = "contracts/dataset.schema.yaml"
    
    try:
        path = Path(schema_path)
        if not path.exists():
            logger.warning(f"Schema file not found at {schema_path}, using default schema.")
            return EXPECTED_SCHEMA
        
        with open(path, 'r', encoding='utf-8') as f:
            schema = yaml.safe_load(f)
            
        if not isinstance(schema, dict) or "fields" not in schema:
            logger.warning("Invalid schema format, using default schema.")
            return EXPECTED_SCHEMA
            
        return schema
        
    except Exception as e:
        logger.warning(f"Failed to load schema from {schema_path}: {e}. Using default schema.")
        return EXPECTED_SCHEMA

def validate_schema(dataframe: pd.DataFrame, schema: Optional[Dict[str, Any]] = None) -> pd.DataFrame:
    """
    Validate a DataFrame against the dataset schema.
    
    This function checks:
    1. All required fields are present in the DataFrame
    2. All required fields have non-null values
    3. Field types are compatible (basic type checking)
    
    Note: This function does NOT check row count. Row count validation is handled
    by T015c (pre-processing warning) and T017c (post-processing halt).
    
    Args:
        dataframe: The DataFrame to validate.
        schema: Optional schema definition. If None, loads from default path.
        
    Returns:
        The validated DataFrame (unchanged).
        
    Raises:
        InsufficientDataError: If required fields are missing or contain nulls.
        SchemaValidationError: If the DataFrame structure is invalid.
    """
    if dataframe is None:
        raise SchemaValidationError("Input DataFrame is None")
        
    if not isinstance(dataframe, pd.DataFrame):
        raise SchemaValidationError(f"Expected DataFrame, got {type(dataframe)}")
        
    if schema is None:
        schema = load_schema()
        
    required_fields = set()
    field_types = {}
    
    # Extract required fields and types from schema
    if "fields" in schema:
        for field_name, field_def in schema["fields"].items():
            if field_def.get("required", False):
                required_fields.add(field_name)
                field_types[field_name] = field_def.get("type", "any")
    
    # Check 1: Verify all required fields are present
    missing_fields = required_fields - set(dataframe.columns)
    if missing_fields:
        error_msg = f"Missing required fields: {sorted(missing_fields)}"
        logger.error(error_msg)
        raise InsufficientDataError(error_msg)
    
    # Check 2: Verify no null values in required fields
    for field in required_fields:
        null_count = dataframe[field].isna().sum()
        if null_count > 0:
            error_msg = f"Field '{field}' contains {null_count} null values"
            logger.error(error_msg)
            raise InsufficientDataError(error_msg)
    
    # Check 3: Basic type validation (optional but recommended)
    # This is a soft check - we allow numeric types to be represented as floats
    numeric_types = {'float', 'int', 'number'}
    str_types = {'str', 'string', 'text'}
    
    for field, expected_type in field_types.items():
        if expected_type in numeric_types:
            if not pd.api.types.is_numeric_dtype(dataframe[field]):
                # Allow conversion if possible, but log warning
                try:
                    dataframe[field] = pd.to_numeric(dataframe[field], errors='raise')
                    logger.warning(f"Converted field '{field}' to numeric type")
                except (ValueError, TypeError):
                    error_msg = f"Field '{field}' should be numeric but contains non-numeric values"
                    logger.error(error_msg)
                    raise SchemaValidationError(error_msg)
        elif expected_type in str_types:
            if not pd.api.types.is_string_dtype(dataframe[field]) and not pd.api.types.is_object_dtype(dataframe[field]):
                # Allow conversion to string
                try:
                    dataframe[field] = dataframe[field].astype(str)
                    logger.warning(f"Converted field '{field}' to string type")
                except (ValueError, TypeError):
                    error_msg = f"Field '{field}' should be string but cannot be converted"
                    logger.error(error_msg)
                    raise SchemaValidationError(error_msg)
    
    logger.info(f"Schema validation passed for {len(dataframe)} rows with {len(required_fields)} required fields")
    return dataframe

def validate_file(file_path: str, schema_path: Optional[str] = None) -> pd.DataFrame:
    """
    Validate a Parquet or CSV file against the schema.
    
    Args:
        file_path: Path to the data file (Parquet or CSV).
        schema_path: Optional path to schema YAML file.
        
    Returns:
        The validated DataFrame.
        
    Raises:
        SchemaValidationError: If the file cannot be loaded or validated.
        InsufficientDataError: If the data fails schema validation.
    """
    path = Path(file_path)
    
    if not path.exists():
        raise SchemaValidationError(f"File not found: {file_path}")
    
    # Load data based on file extension
    if path.suffix == '.parquet':
        try:
            df = pd.read_parquet(path)
        except Exception as e:
            raise SchemaValidationError(f"Failed to load Parquet file: {e}")
    elif path.suffix in ['.csv', '.tsv']:
        try:
            df = pd.read_csv(path, sep=None, engine='python')
        except Exception as e:
            raise SchemaValidationError(f"Failed to load CSV file: {e}")
    else:
        raise SchemaValidationError(f"Unsupported file format: {path.suffix}")
    
    # Validate the loaded data
    return validate_schema(df, schema_path)
