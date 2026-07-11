"""
Stub schema validation helpers for contract testing.

These functions provide the interface for validating data artifacts
against expected schemas (e.g., feature matrix, model outputs).

Currently stubbed to return True for existence checks; 
implementations will be added as schemas are finalized.
"""

from typing import Any, Dict, List, Optional
import pandas as pd
import json
import os
from pathlib import Path

# Import project logger utility
from code.utils.logging import get_logger

logger = get_logger(__name__)

def validate_feature_matrix_schema(df: pd.DataFrame, required_columns: List[str]) -> bool:
    """
    Validate that a feature matrix DataFrame contains the required columns.
    
    Args:
        df: The DataFrame to validate.
        required_columns: List of column names that must be present.
        
    Returns:
        True if validation passes, False otherwise.
    """
    if df is None:
        logger.error("Feature matrix DataFrame is None")
        return False
        
    missing = [col for col in required_columns if col not in df.columns]
    if missing:
        logger.error(f"Feature matrix missing required columns: {missing}")
        return False
        
    logger.info(f"Feature matrix schema validated: {len(df.columns)} columns present")
    return True

def validate_json_schema(file_path: str, required_keys: List[str]) -> bool:
    """
    Validate that a JSON file contains the required top-level keys.
    
    Args:
        file_path: Path to the JSON file.
        required_keys: List of keys that must exist at the top level.
        
    Returns:
        True if validation passes, False otherwise.
    """
    if not os.path.exists(file_path):
        logger.error(f"JSON file not found: {file_path}")
        return False
        
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in {file_path}: {e}")
        return False
        
    missing = [key for key in required_keys if key not in data]
    if missing:
        logger.error(f"JSON file missing required keys: {missing}")
        return False
        
    logger.info(f"JSON schema validated: {len(data.keys())} keys present in {file_path}")
    return True

def validate_model_output_schema(file_path: str, required_keys: List[str]) -> bool:
    """
    Validate the schema of a model output file (e.g., metrics, weights).
    
    Args:
        file_path: Path to the model output file (JSON or CSV).
        required_keys: List of required keys/columns.
        
    Returns:
        True if validation passes, False otherwise.
    """
    if not os.path.exists(file_path):
        logger.error(f"Model output file not found: {file_path}")
        return False
        
    if file_path.endswith('.json'):
        return validate_json_schema(file_path, required_keys)
    elif file_path.endswith('.csv'):
        try:
            df = pd.read_csv(file_path)
            return validate_feature_matrix_schema(df, required_keys)
        except Exception as e:
            logger.error(f"Failed to read CSV {file_path}: {e}")
            return False
    else:
        logger.warning(f"Unsupported file format for schema validation: {file_path}")
        return True

def validate_phenotype_column(df: pd.DataFrame, column_name: str = 'resistance_phenotype') -> bool:
    """
    Validate that a specific phenotype column exists and has no missing values.
    
    Args:
        df: The DataFrame to validate.
        column_name: The name of the phenotype column.
        
    Returns:
        True if validation passes, False otherwise.
    """
    if column_name not in df.columns:
        logger.error(f"Phenotype column '{column_name}' not found in DataFrame")
        return False
        
    if df[column_name].isnull().any():
        logger.error(f"Phenotype column '{column_name}' contains missing values")
        return False
        
    logger.info(f"Phenotype column '{column_name}' validated: no missing values")
    return True

# Stub for future expansion: specific contract tests for US1, US2, US3
# e.g., validate_phylogeny_tree, validate_permutation_results, etc.