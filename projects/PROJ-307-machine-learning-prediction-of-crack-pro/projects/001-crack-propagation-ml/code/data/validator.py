"""
Data validation for the crack propagation prediction pipeline.
"""
import logging
from pathlib import Path
from typing import List, Set, Dict, Any
import pandas as pd
import yaml
from code.config import ensure_dirs
from code.logging_config import get_logger

logger = get_logger(__name__)

def load_validation_schema(schema_path: str) -> Dict[str, Any]:
    """
    Load validation schema from YAML file.
    
    Args:
        schema_path: Path to schema file
        
    Returns:
        Schema dictionary
    """
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

def validate_required_columns(df: pd.DataFrame, required_cols: List[str]) -> bool:
    """
    Check if DataFrame has all required columns.
    
    Args:
        df: DataFrame to validate
        required_cols: List of required column names
        
    Returns:
        True if all required columns present, False otherwise
    """
    missing = set(required_cols) - set(df.columns)
    if missing:
        logger.error(f"Missing required columns: {missing}")
        return False
    return True

def validate_data_quality(df: pd.DataFrame) -> bool:
    """
    Validate data quality (no NaN in critical columns, positive values).
    
    Args:
        df: DataFrame to validate
        
    Returns:
        True if data quality is acceptable, False otherwise
    """
    critical_cols = ['da_dN', 'delta_K']
    
    for col in critical_cols:
        if col not in df.columns:
            continue
        if df[col].isna().any():
            logger.error(f"Column {col} contains NaN values")
            return False
        if (df[col] <= 0).any():
            logger.error(f"Column {col} contains non-positive values")
            return False
    
    return True

def halt_if_invalid(df: pd.DataFrame, required_cols: List[str]) -> None:
    """
    Halt execution if data validation fails.
    
    Args:
        df: DataFrame to validate
        required_cols: List of required column names
    """
    if not validate_required_columns(df, required_cols):
        raise ValueError("Data validation failed: missing required columns")
    if not validate_data_quality(df):
        raise ValueError("Data validation failed: data quality issues")

def create_validation_report(df: pd.DataFrame, schema: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a validation report for the dataset.
    
    Args:
        df: DataFrame to validate
        schema: Schema dictionary
        
    Returns:
        Validation report dictionary
    """
    report = {
        "total_rows": len(df),
        "columns": list(df.columns),
        "missing_values": df.isna().sum().to_dict(),
        "dtypes": df.dtypes.astype(str).to_dict(),
        "valid": True,
        "issues": []
    }
    
    required_cols = schema.get('required', [])
    missing_cols = set(required_cols) - set(df.columns)
    if missing_cols:
        report["valid"] = False
        report["issues"].append(f"Missing required columns: {missing_cols}")
    
    return report
