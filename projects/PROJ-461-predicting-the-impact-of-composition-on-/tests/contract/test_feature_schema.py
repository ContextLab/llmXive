"""
Contract test for feature schema in tests/contract/test_feature_schema.py.

This test verifies that the feature engineering output (data/clean_data.csv)
conforms to the expected schema defined in contracts/feature.schema.yaml.

It ensures that:
1. All required feature columns exist.
2. Data types are correct (numeric for features).
3. No missing values exist in the feature columns.
4. Values are within scientifically reasonable bounds (where applicable).
"""

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd
import numpy as np
import pytest
import yaml

# Import project utilities
import sys
from pathlib import Path

# Ensure project root is in path for imports if running from tests/
project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from config import load_config, Config
from utils.logger import get_logger
from utils.schema_validator import load_schema

# Initialize logger
logger = get_logger(__name__)


def load_feature_schema() -> Dict[str, Any]:
    """Load the feature schema from contracts/feature.schema.yaml."""
    schema_path = project_root / "contracts" / "feature.schema.yaml"
    if not schema_path.exists():
        raise FileNotFoundError(f"Feature schema not found at {schema_path}")
    
    with open(schema_path, 'r') as f:
        schema = yaml.safe_load(f)
    return schema


def validate_feature_columns(df: pd.DataFrame, schema: Dict[str, Any]) -> List[str]:
    """
    Validate that all required feature columns exist in the DataFrame.
    
    Returns a list of missing column names.
    """
    required_fields = schema.get("required", [])
    properties = schema.get("properties", {})
    
    missing_columns = []
    for field in required_fields:
        if field not in df.columns:
            missing_columns.append(field)
        elif field in properties:
            # Check if the column type matches expectations if defined
            prop_def = properties[field]
            if prop_def.get("type") == "number" and not pd.api.types.is_numeric_dtype(df[field]):
                # Log a warning but don't fail the column existence check
                logger.warning(f"Column {field} exists but is not numeric")
    
    return missing_columns


def validate_feature_values(df: pd.DataFrame, schema: Dict[str, Any]) -> List[str]:
    """
    Validate that feature values meet schema constraints (e.g., no nulls, ranges).
    
    Returns a list of validation error messages.
    """
    errors = []
    properties = schema.get("properties", {})
    
    for col_name, col_def in properties.items():
        if col_name not in df.columns:
            continue
        
        col_data = df[col_name]
        
        # Check for nulls if not allowed
        if col_def.get("nullable") is False and col_data.isna().any():
            errors.append(f"Column '{col_name}' contains null values but nullable=False")
        
        # Check numeric range if defined
        if col_def.get("type") == "number":
            minimum = col_def.get("minimum")
            maximum = col_def.get("maximum")
            
            if minimum is not None:
                if (col_data < minimum).any():
                    errors.append(f"Column '{col_name}' has values below minimum {minimum}")
            
            if maximum is not None:
                if (col_data > maximum).any():
                    errors.append(f"Column '{col_name}' has values above maximum {maximum}")
    
    return errors


def test_feature_schema_conformance():
    """
    Contract test: Verify data/clean_data.csv matches contracts/feature.schema.yaml.
    
    This test assumes T014 (preprocess) and T020/T021 (feature engineering) 
    have been run and data/clean_data.csv exists.
    """
    config = load_config()
    data_path = config.data_dir / "clean_data.csv"
    
    if not data_path.exists():
        pytest.fail(f"Data file not found: {data_path}. "
                    "Ensure T014 and feature engineering tasks (T020-T023) have run.")
    
    try:
        df = pd.read_csv(data_path)
        logger.info(f"Loaded {len(df)} rows from {data_path}")
    except Exception as e:
        pytest.fail(f"Failed to read CSV: {e}")
    
    # Load schema
    try:
        schema = load_feature_schema()
        logger.info("Feature schema loaded successfully")
    except FileNotFoundError as e:
        pytest.fail(str(e))
    
    # Validate columns
    missing_cols = validate_feature_columns(df, schema)
    if missing_cols:
        pytest.fail(f"Missing required feature columns: {missing_cols}")
    
    # Validate values
    value_errors = validate_feature_values(df, schema)
    if value_errors:
        pytest.fail(f"Feature value validation errors: {value_errors}")
    
    logger.info("Feature schema validation passed successfully.")


def test_feature_data_types():
    """
    Specific test for feature data types.
    Ensures all engineered features are numeric.
    """
    config = load_config()
    data_path = config.data_dir / "clean_data.csv"
    
    if not data_path.exists():
        pytest.skip(f"Data file not found: {data_path}")
    
    df = pd.read_csv(data_path)
    schema = load_feature_schema()
    
    non_numeric_features = []
    properties = schema.get("properties", {})
    
    for col, prop in properties.items():
        if prop.get("type") == "number":
            if col in df.columns and not pd.api.types.is_numeric_dtype(df[col]):
                non_numeric_features.append(col)
    
    if non_numeric_features:
        pytest.fail(f"Non-numeric features found where numbers expected: {non_numeric_features}")
    
    logger.info("All feature data types are correct.")


if __name__ == "__main__":
    # Allow running as a script for manual verification
    pytest.main([__file__, "-v"])
