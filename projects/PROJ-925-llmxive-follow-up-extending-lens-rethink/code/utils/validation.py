"""
Validation utilities for the llmXive pipeline.

Implements schema validation for feature vectors and raw dataset availability checks.
"""
import os
import sys
import logging
import json
from pathlib import Path
from typing import List, Dict, Any, Optional

import pandas as pd
import yaml
from pydantic import BaseModel, ValidationError
from pydantic.config import ConfigDict

# Import project utilities
from config import get_project_root, get_paths
from utils.errors import DataSchemaError, create_missing_dataset_error
from utils.logging import get_logger

# Import models if needed for validation context
from models.linguistic_feature_vector import LinguisticFeatureVector

logger = get_logger(__name__)

def load_schema(schema_path: str) -> Dict[str, Any]:
    """
    Load a JSON Schema from a YAML file.
    
    Args:
        schema_path: Path to the schema file (relative to project root or absolute).
        
    Returns:
        Dictionary containing the schema definition.
        
    Raises:
        FileNotFoundError: If the schema file does not exist.
        yaml.YAMLError: If the file is not valid YAML.
    """
    path = Path(schema_path)
    if not path.is_absolute():
        project_root = get_project_root()
        path = project_root / schema_path
        
    if not path.exists():
        raise FileNotFoundError(f"Schema file not found: {path}")
        
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def validate_dataframe(df: pd.DataFrame, schema: Dict[str, Any]) -> None:
    """
    Validate a DataFrame against a JSON Schema definition.
    
    This function checks:
    1. Presence of all required columns.
    2. Data types match the schema (string, integer, number).
    3. Value constraints (minimum, maximum) where defined.
    
    Args:
        df: The DataFrame to validate.
        schema: The schema dictionary loaded from YAML.
        
    Raises:
        ValueError: If the DataFrame does not match the schema.
    """
    properties = schema.get('properties', {})
    required_cols = properties.get('required', [])
    schema_props = properties.get('properties', {})
    
    # 1. Check required columns
    missing_cols = []
    for col in required_cols:
        if col not in df.columns:
            missing_cols.append(col)
            
    if missing_cols:
        raise ValueError(f"DataFrame missing required columns: {missing_cols}")
        
    # 2. Validate each column's type and constraints
    for col_name, col_schema in schema_props.items():
        if col_name not in df.columns:
            continue
            
        col_type = col_schema.get('type')
        min_val = col_schema.get('minimum')
        max_val = col_schema.get('maximum')
        
        series = df[col_name]
        
        # Type checking
        if col_type == 'string':
            if not pd.api.types.is_string_dtype(series) and not pd.api.types.is_object_dtype(series):
                # Allow object dtype for strings in pandas
                pass 
            # Check for non-string values if strictly typed
            if not all(isinstance(x, str) or pd.isna(x) for x in series):
                raise ValueError(f"Column '{col_name}' contains non-string values.")
                
        elif col_type == 'integer':
            if not pd.api.types.is_integer_dtype(series) and not pd.api.types.is_float_dtype(series):
                # Float might be used for integer columns in some contexts, but strict check
                if not all(isinstance(x, int) or pd.isna(x) for x in series):
                    raise ValueError(f"Column '{col_name}' contains non-integer values.")
                    
        elif col_type == 'number':
            if not pd.api.types.is_numeric_dtype(series):
                raise ValueError(f"Column '{col_name}' contains non-numeric values.")
                
        # Range constraints
        if min_val is not None:
            if series.min() < min_val:
                raise ValueError(f"Column '{col_name}' has values below minimum {min_val}. Found min: {series.min()}")
                
        if max_val is not None:
            if series.max() > max_val:
                raise ValueError(f"Column '{col_name}' has values above maximum {max_val}. Found max: {series.max()}")

def validate_raw_dataset_availability(raw_data_path: str, required_columns: List[str]) -> None:
    """
    Validate that the raw dataset exists and contains required columns.
    
    Args:
        raw_data_path: Path to the raw data file (e.g., parquet).
        required_columns: List of column names that must exist.
        
    Raises:
        DataSchemaError: If the file is missing or columns are absent.
    """
    path = Path(raw_data_path)
    if not path.is_absolute():
        project_root = get_project_root()
        path = project_root / raw_data_path
        
    if not path.exists():
        # Format error message as per T004b requirement
        # Assuming source is 'pick-a-pic' based on context
        raise DataSchemaError(create_missing_dataset_error("pick-a-pic", required_columns[0]))
        
    try:
        # Try to load just the schema/columns to avoid reading full data
        if path.suffix == '.parquet':
            df_check = pd.read_parquet(path, columns=required_columns)
        elif path.suffix == '.csv':
            df_check = pd.read_csv(path, usecols=required_columns)
        else:
            # Fallback: try to read full and check
            df_check = pd.read_parquet(path) if path.suffix == '.parquet' else pd.read_csv(path)
            
        missing_cols = [col for col in required_columns if col not in df_check.columns]
        if missing_cols:
            # Determine the first missing column for the error message
            raise DataSchemaError(create_missing_dataset_error("pick-a-pic", missing_cols[0]))
            
    except Exception as e:
        # If we can't read it, it's a schema/data integrity issue
        if isinstance(e, DataSchemaError):
            raise e
        raise DataSchemaError(f"Failed to read raw dataset or validate columns: {str(e)}")

def validate_feature_vector_schema(df: pd.DataFrame, schema_path: str) -> None:
    """
    Validate a feature vector DataFrame against the specified schema.
    
    Args:
        df: The feature vector DataFrame.
        schema_path: Path to the feature_vector.schema.yaml file.
        
    Raises:
        ValueError: If validation fails.
        FileNotFoundError: If schema file is missing.
    """
    logger.info(f"Validating feature vector DataFrame against schema: {schema_path}")
    
    schema = load_schema(schema_path)
    validate_dataframe(df, schema)
    
    logger.info("Feature vector schema validation passed.")

def main():
    """
    Main entry point for standalone validation execution.
    
    Usage:
        python code/utils/validation.py --features data/processed/features.csv --schema specs/001-llmxive-follow-up-extending-lens-rethink/contracts/feature_vector.schema.yaml --raw data/raw/pick-a-pic.parquet
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Validate feature vectors and raw dataset schema.")
    parser.add_argument("--features", required=True, help="Path to the features CSV file.")
    parser.add_argument("--schema", required=True, help="Path to the feature vector schema YAML.")
    parser.add_argument("--raw", required=True, help="Path to the raw dataset file.")
    parser.add_argument("--raw-cols", nargs="+", default=["human_rating"], help="Required columns in raw dataset.")
    
    args = parser.parse_args()
    
    setup_logging()
    
    try:
        # 1. Validate Raw Dataset
        logger.info(f"Checking raw dataset availability: {args.raw}")
        validate_raw_dataset_availability(args.raw, args.raw_cols)
        logger.info(f"Raw dataset validation passed for columns: {args.raw_cols}")
        
        # 2. Load Features
        logger.info(f"Loading features from: {args.features}")
        df_features = pd.read_csv(args.features)
        logger.info(f"Loaded {len(df_features)} feature records.")
        
        # 3. Validate Features against Schema
        validate_feature_vector_schema(df_features, args.schema)
        
        logger.info("All validations passed successfully.")
        
    except DataSchemaError as e:
        logger.critical(f"Data Schema Error: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Validation Error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.exception(f"Unexpected error during validation: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()