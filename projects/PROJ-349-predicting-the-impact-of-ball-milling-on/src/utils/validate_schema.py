"""
Schema validation logic for the ball milling dataset.
Validates dataframes against contracts/dataset.schema.yaml.
"""
import os
import yaml
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import pandas as pd
import numpy as np

from src.exceptions import (
    SchemaValidationError,
    InsufficientDataError,
    DataFormatError
)

# Path to the schema file relative to project root
SCHEMA_PATH = Path(__file__).parent.parent.parent / "contracts" / "dataset.schema.yaml"


def load_schema(schema_path: Optional[Union[str, Path]] = None) -> Dict[str, Any]:
    """Load the JSON/YAML schema definition."""
    path = Path(schema_path) if schema_path else SCHEMA_PATH
    
    if not path.exists():
        raise FileNotFoundError(f"Schema file not found at {path}")
    
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def validate_schema(dataframe: pd.DataFrame, schema: Optional[Dict[str, Any]] = None) -> pd.DataFrame:
    """
    Validate a DataFrame against the dataset schema.
    
    Args:
        dataframe: The pandas DataFrame to validate
        schema: Optional pre-loaded schema. If None, loads from default path.
    
    Returns:
        The validated DataFrame (unchanged)
    
    Raises:
        SchemaValidationError: If schema validation fails
        InsufficientDataError: If row count is below minimum (150)
        DataFormatError: If data types are incompatible
    """
    if schema is None:
        schema = load_schema()
    
    if not isinstance(dataframe, pd.DataFrame):
        raise DataFormatError("Input must be a pandas DataFrame")
    
    # 1. Check minimum row count (FR-001, SC-004)
    min_rows = schema.get('x-min-rows', 150)
    if len(dataframe) < min_rows:
        raise InsufficientDataError(
            f"Dataset size {len(dataframe)} is below minimum viable threshold.",
            current_count=len(dataframe),
            minimum_required=min_rows
        )
    
    # 2. Check required columns
    required_fields = schema.get('required', [])
    missing_cols = [col for col in required_fields if col not in dataframe.columns]
    
    if missing_cols:
        raise SchemaValidationError(
            f"Missing required columns: {missing_cols}",
            violations=[f"Missing column: {col}" for col in missing_cols]
        )
    
    # 3. Validate data types and constraints per property
    properties = schema.get('properties', {})
    violations = []
    
    for col_name, col_schema in properties.items():
        if col_name not in dataframe.columns:
            continue
        
        col_data = dataframe[col_name]
        
        # Type checking
        expected_type = col_schema.get('type')
        
        if expected_type == 'number':
            if not pd.api.types.is_numeric_dtype(col_data):
                violations.append(f"Column '{col_name}' must be numeric, found {col_data.dtype}")
            else:
                # Check minimum constraints if defined
                if 'minimum' in col_schema:
                    min_val = col_schema['minimum']
                    if (col_data < min_val).any():
                        violations.append(
                            f"Column '{col_name}' contains values below minimum {min_val}"
                        )
        
        elif expected_type == 'string':
            if not pd.api.types.is_string_dtype(col_data):
                # Allow object dtype which is common for strings in pandas
                if not pd.api.types.is_object_dtype(col_data):
                    violations.append(f"Column '{col_name}' must be string, found {col_data.dtype}")
            
            # Check pattern constraints if defined
            if 'pattern' in col_schema:
                import re
                pattern = re.compile(col_schema['pattern'])
                # Check for non-matching values (excluding NaN)
                non_matching = col_data[
                    col_data.notna() & ~col_data.astype(str).apply(lambda x: bool(pattern.match(x)))
                ]
                if len(non_matching) > 0:
                    violations.append(
                        f"Column '{col_name}' contains values not matching pattern {col_schema['pattern']}"
                    )
        
        # Check for nulls in required fields (JSON Schema 'required' implies non-null)
        if col_schema.get('type') and col_data.isna().any():
            # Allow NaN for numeric types if imputation is expected later, 
            # but flag for required string fields
            if expected_type == 'string':
                violations.append(f"Column '{col_name}' contains null values")
    
    if violations:
        raise SchemaValidationError(
            f"Schema validation failed with {len(violations)} errors.",
            violations=violations
        )
    
    return dataframe


def validate_dataframe_size(dataframe: pd.DataFrame, min_rows: int = 150) -> None:
    """
    Standalone check for dataframe size.
    
    Args:
        dataframe: The DataFrame to check
        min_rows: Minimum required rows
    
    Raises:
        InsufficientDataError: If count is below threshold
    """
    if len(dataframe) < min_rows:
        raise InsufficientDataError(
            f"Dataset size {len(dataframe)} is below minimum viable threshold.",
            current_count=len(dataframe),
            minimum_required=min_rows
        )
