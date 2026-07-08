"""
Schema validation utilities for dataset contracts.
Validates data against the YAML schema definitions.
"""
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
import yaml

import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

def load_schema(schema_path: str) -> Dict[str, Any]:
    """Load a YAML schema definition."""
    path = Path(schema_path)
    if not path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(path, 'r') as f:
        return yaml.safe_load(f)

def validate_column_schema(df: pd.DataFrame, schema_cols: List[Dict[str, Any]]) -> List[str]:
    """
    Validate dataframe columns against schema definition.
    Returns list of validation errors.
    """
    errors = []
    schema_map = {col['name']: col for col in schema_cols}
    
    # Check for missing columns
    for col_name, col_def in schema_map.items():
        if col_name not in df.columns:
            errors.append(f"Missing required column: {col_name}")
    
    # Check for extra columns (optional warning)
    extra_cols = set(df.columns) - set(schema_map.keys())
    if extra_cols:
        logger.warning(f"Extra columns found in data: {extra_cols}")

    # Validate types and nullability
    for col_name, col_def in schema_map.items():
        if col_name not in df.columns:
            continue
        
        dtype_str = col_def.get('dtype')
        is_nullable = col_def.get('nullable', False)
        
        # Check nullability
        if not is_nullable and df[col_name].isna().any():
            errors.append(f"Column '{col_name}' contains null values but is marked non-nullable")
        
        # Type checking (simplified)
        actual_dtype = str(df[col_name].dtype)
        if dtype_str and actual_dtype != dtype_str:
            # Allow some flexibility for object vs string, etc.
            if not (dtype_str == 'object' and actual_dtype in ['object', 'string', 'category']):
                errors.append(f"Column '{col_name}' dtype mismatch: expected {dtype_str}, got {actual_dtype}")
    
    return errors

def validate_fingerprint_dimensions(df: pd.DataFrame) -> List[str]:
    """
    Validate that fingerprint columns have correct dimensions.
    ECFP4: 2048, MACCS: 167
    """
    errors = []
    
    ecfp_col = 'fingerprint_ecfp4'
    maccs_col = 'fingerprint_maccs'
    
    if ecfp_col in df.columns:
        # Check if it's a list/array column
        sample = df[ecfp_col].iloc[0] if len(df) > 0 else None
        if isinstance(sample, (list, np.ndarray)):
            if len(sample) != 2048:
                errors.append(f"ECFP4 dimension mismatch: expected 2048, got {len(sample)}")
        else:
            errors.append(f"Column '{ecfp_col}' is not a list/array type")
    
    if maccs_col in df.columns:
        sample = df[maccs_col].iloc[0] if len(df) > 0 else None
        if isinstance(sample, (list, np.ndarray)):
            if len(sample) != 167:
                errors.append(f"MACCS dimension mismatch: expected 167, got {len(sample)}")
        else:
            errors.append(f"Column '{maccs_col}' is not a list/array type")
    
    return errors

def validate_record_content(df: pd.DataFrame, schema: Dict[str, Any]) -> List[str]:
    """
    Validate specific content constraints (e.g., yield range, SMILES format).
    """
    errors = []
    
    if 'yield_value' in df.columns:
        y = df['yield_value']
        if (y < 0).any() or (y > 100).any():
            errors.append("Yield values must be between 0 and 100")
    
    if 'reaction_smiles' in df.columns:
        # Basic check for empty strings
        if df['reaction_smiles'].str.len().min() == 0:
            errors.append("Empty SMILES strings found")
    
    return errors

def validate_dataset(df: pd.DataFrame, schema_path: str) -> bool:
    """
    Main entry point for validating a dataset against a schema.
    Returns True if valid, False otherwise.
    """
    logger.info(f"Validating dataset against schema: {schema_path}")
    
    try:
        schema = load_schema(schema_path)
    except Exception as e:
        logger.error(f"Failed to load schema: {e}")
        return False
    
    all_errors = []
    
    # Validate columns
    if 'columns' in schema:
        all_errors.extend(validate_column_schema(df, schema['columns']))
    
    # Validate fingerprints
    all_errors.extend(validate_fingerprint_dimensions(df))
    
    # Validate content
    all_errors.extend(validate_record_content(df, schema))
    
    if all_errors:
        logger.error(f"Schema validation failed with {len(all_errors)} errors:")
        for err in all_errors:
            logger.error(f"  - {err}")
        return False
    
    logger.info("Schema validation passed")
    return True

def save_validation_report(df: pd.DataFrame, schema_path: str, output_path: str) -> None:
    """
    Run validation and save a detailed JSON report.
    """
    report = {
        "schema_path": schema_path,
        "data_shape": list(df.shape),
        "columns": list(df.columns),
        "valid": True,
        "errors": []
    }
    
    try:
        schema = load_schema(schema_path)
    except Exception as e:
        report["valid"] = False
        report["errors"].append(f"Schema load error: {str(e)}")
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        return
    
    # Column validation
    if 'columns' in schema:
        report["errors"].extend(validate_column_schema(df, schema['columns']))
    
    # Dimension validation
    report["errors"].extend(validate_fingerprint_dimensions(df))
    
    # Content validation
    report["errors"].extend(validate_record_content(df, schema))
    
    report["valid"] = len(report["errors"]) == 0
    
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Validation report saved to {output_path}")