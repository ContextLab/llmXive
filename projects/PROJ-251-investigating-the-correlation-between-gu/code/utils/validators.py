import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional
from pathlib import Path
import json
import jsonschema
import yaml

from utils.logging_config import get_logger

logger = get_logger(__name__)

def load_schema(schema_path: Path) -> Dict[str, Any]:
    """Loads a YAML schema file and returns it as a dictionary."""
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(schema_path, 'r') as f:
        schema = yaml.safe_load(f)
    
    if not isinstance(schema, dict):
        raise ValueError(f"Schema file {schema_path} does not contain a valid YAML dictionary")
    
    return schema

def validate_dataset_schema(df: pd.DataFrame, schema_path: Optional[Path] = None) -> bool:
    """
    Validates a DataFrame against a JSON/YAML schema.
    
    Args:
        df: DataFrame to validate.
        schema_path: Path to the schema file. If None, uses basic checks.
        
    Returns:
        True if validation passes, False otherwise.
        
    Raises:
        FileNotFoundError: If schema_path is provided but not found.
        ValueError: If schema is invalid.
    """
    # Basic checks (fallback if no schema provided)
    if schema_path is None:
        logger.warning("No schema path provided, performing basic validation checks")
        required_cols = ["subject_id", "titer_baseline", "titer_post"]
        for col in required_cols:
            if col not in df.columns:
                logger.error(f"Missing required column: {col}")
                return False
        
        if df[required_cols].isnull().any().any():
            logger.error("Null values found in required columns")
            return False
        
        return True

    # Load schema
    schema = load_schema(schema_path)
    
    # Convert DataFrame to dictionary format expected by jsonschema
    # We validate row by row or as a whole object depending on schema structure
    # For the expected schema (object with properties), we treat the whole DF as one object
    # where columns are properties and rows are instances.
    # However, jsonschema validates a single instance. We'll validate the structure
    # and then check data types/values against schema constraints.
    
    required_fields = schema.get('required', [])
    properties = schema.get('properties', {})
    
    # Check required columns
    missing_cols = set(required_fields) - set(df.columns)
    if missing_cols:
        logger.error(f"Missing required columns: {missing_cols}")
        return False
    
    # Check for nulls in required columns
    for col in required_fields:
        if df[col].isnull().any():
            logger.error(f"Null values found in required column: {col}")
            return False
    
    # Type checking based on schema properties
    for col in df.columns:
        if col in properties:
            prop_schema = properties[col]
            expected_type = prop_schema.get('type')
            
            if expected_type == 'string':
                if not df[col].apply(lambda x: isinstance(x, str) or pd.isna(x)).all():
                    logger.warning(f"Column {col} contains non-string values")
            elif expected_type == 'number':
                if not pd.api.types.is_numeric_dtype(df[col]):
                    # Allow for NaN in numeric columns
                    numeric_col = df[col].dropna()
                    if not pd.api.types.is_numeric_dtype(numeric_col):
                        logger.warning(f"Column {col} is not numeric")
    
    return True

def validate_correlation_results_schema(results: Any) -> bool:
    """
    Validates correlation results structure.
    
    Args:
        results: Dictionary or list of dictionaries containing correlation results.
        
    Returns:
        True if validation passes, False otherwise.
    """
    required_keys = ["taxon", "coefficient", "raw_pvalue", "adj_pvalue"]
    
    if isinstance(results, dict):
        # If it's a single result, check if it has the keys
        if not all(k in results for k in required_keys):
            logger.error(f"Correlation result missing required keys: {set(required_keys) - set(results.keys())}")
            return False
        return True
    elif isinstance(results, list):
        if len(results) == 0:
            logger.warning("Correlation results list is empty")
            return True  # Empty is valid, just no results
        
        for i, item in enumerate(results):
            if not isinstance(item, dict):
                logger.error(f"Item {i} in correlation results is not a dictionary")
                return False
            if not all(k in item for k in required_keys):
                missing = set(required_keys) - set(item.keys())
                logger.error(f"Correlation result item {i} missing keys: {missing}")
                return False
            
            # Validate types
            try:
                float(item['coefficient'])
                float(item['raw_pvalue'])
                float(item['adj_pvalue'])
            except (ValueError, TypeError):
                logger.error(f"Correlation result item {i} has invalid numeric values")
                return False
            
            # Validate p-value ranges
            if not (0 <= item['raw_pvalue'] <= 1):
                logger.error(f"Correlation result item {i} has raw_pvalue outside [0, 1]: {item['raw_pvalue']}")
                return False
            if not (0 <= item['adj_pvalue'] <= 1):
                logger.error(f"Correlation result item {i} has adj_pvalue outside [0, 1]: {item['adj_pvalue']}")
                return False
        
        return True
    else:
        logger.error(f"Correlation results must be a dict or list, got {type(results)}")
        return False

def validate_model_metrics_schema(metrics: Dict[str, Any]) -> bool:
    """
    Validates model metrics dictionary.
    
    Args:
        metrics: Dictionary containing model performance metrics.
        
    Returns:
        True if validation passes, False otherwise.
    """
    required_keys = ["accuracy", "precision", "recall", "f1"]
    
    if not isinstance(metrics, dict):
        logger.error(f"Model metrics must be a dictionary, got {type(metrics)}")
        return False
    
    missing_keys = set(required_keys) - set(metrics.keys())
    if missing_keys:
        logger.error(f"Model metrics missing required keys: {missing_keys}")
        return False
    
    # Validate numeric values and ranges
    for key in required_keys:
        try:
            val = float(metrics[key])
            if not (0 <= val <= 1):
                logger.error(f"Model metric '{key}' is outside [0, 1]: {val}")
                return False
        except (ValueError, TypeError):
            logger.error(f"Model metric '{key}' is not a valid number: {metrics[key]}")
            return False
    
    return True

def validate_file_exists(filepath: Path) -> bool:
    """
    Checks if a file exists.
    
    Args:
        filepath: Path to the file.
        
    Returns:
        True if file exists, False otherwise.
    """
    exists = filepath.exists()
    if not exists:
        logger.error(f"File not found: {filepath}")
    return exists

def validate_dataframe_not_empty(df: pd.DataFrame) -> bool:
    """
    Checks if a DataFrame has rows.
    
    Args:
        df: DataFrame to check.
        
    Returns:
        True if DataFrame has rows, False otherwise.
    """
    is_empty = len(df) == 0
    if is_empty:
        logger.error("DataFrame is empty")
    return not is_empty

def validate_schema_comprehensive(filepath: Path, schema_path: Path) -> Dict[str, Any]:
    """
    Comprehensive validation of a data file against a schema.
    
    Args:
        filepath: Path to the data file (CSV).
        schema_path: Path to the schema file (YAML).
        
    Returns:
        Dictionary with validation results.
    """
    result = {
        'valid': False,
        'errors': [],
        'warnings': []
    }
    
    try:
        # Check file existence
        if not validate_file_exists(filepath):
            result['errors'].append(f"Data file not found: {filepath}")
            return result
        
        # Load data
        df = pd.read_csv(filepath)
        
        # Check if empty
        if not validate_dataframe_not_empty(df):
            result['errors'].append("Data file is empty")
            return result
        
        # Load schema
        if not validate_file_exists(schema_path):
            result['errors'].append(f"Schema file not found: {schema_path}")
            return result
        
        # Validate schema
        if not validate_dataset_schema(df, schema_path):
            result['errors'].append("Schema validation failed")
            return result
        
        result['valid'] = True
        result['row_count'] = len(df)
        result['column_count'] = len(df.columns)
        
    except Exception as e:
        result['errors'].append(f"Validation error: {str(e)}")
    
    return result