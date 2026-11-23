import logging
from pathlib import Path
from typing import List, Set, Dict, Any, Optional
import pandas as pd
import yaml
import json

from config import get_path

logger = logging.getLogger(__name__)

# Required columns for the dataset after cleaning (US1)
REQUIRED_COLUMNS = {
    "da_dN",       # Crack growth rate
    "delta_K",     # Stress intensity factor range
    "material",    # Material identifier
    "heat_treatment" # Heat treatment description (can be "Unknown/Not Specified")
}

def load_validation_schema(schema_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load the validation schema from the contracts directory.
    If schema_path is not provided, defaults to contracts/dataset.schema.yaml.
    """
    if schema_path is None:
        schema_path = str(get_path("contracts", "dataset.schema.yaml"))
    
    path = Path(schema_path)
    if not path.exists():
        logger.warning(f"Schema file not found at {schema_path}. Using default validation rules.")
        return {}
    
    with open(path, 'r') as f:
        return yaml.safe_load(f)

def validate_required_columns(df: pd.DataFrame, required_cols: Optional[Set[str]] = None) -> List[str]:
    """
    Check if the DataFrame contains all required columns.
    Returns a list of missing column names.
    """
    if required_cols is None:
        required_cols = REQUIRED_COLUMNS
    
    existing_cols = set(df.columns)
    missing = required_cols - existing_cols
    return list(missing)

def validate_data_quality(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Perform basic data quality checks:
    - Check for infinite values
    - Check for NaN values in critical columns
    - Check for negative da/dN or delta_K (physically invalid)
    
    Returns a report dictionary.
    """
    report = {
        "has_infinite": False,
        "infinite_columns": [],
        "nan_counts": {},
        "negative_values": {},
        "valid": True,
        "issues": []
    }
    
    # Check for infinite values
    if np.isinf(df).any().any():
        report["has_infinite"] = True
        for col in df.columns:
            if np.isinf(df[col]).any():
                report["infinite_columns"].append(col)
                report["issues"].append(f"Column '{col}' contains infinite values")
    
    # Check for NaN in critical columns
    critical_cols = ["da_dN", "delta_K"]
    for col in critical_cols:
        if col in df.columns:
            nan_count = df[col].isna().sum()
            report["nan_counts"][col] = int(nan_count)
            if nan_count > 0:
                report["issues"].append(f"Column '{col}' has {nan_count} NaN values")
    
    # Check for negative values in physical quantities
    physical_cols = ["da_dN", "delta_K"]
    for col in physical_cols:
        if col in df.columns:
            neg_count = (df[col] < 0).sum()
            if neg_count > 0:
                report["negative_values"][col] = int(neg_count)
                report["issues"].append(f"Column '{col}' has {neg_count} negative values")
                report["valid"] = False
    
    if not report["issues"]:
        report["issues"].append("No data quality issues detected")
    
    return report

def halt_if_invalid(df: pd.DataFrame, 
                    required_cols: Optional[Set[str]] = None,
                    raise_on_missing: bool = True) -> bool:
    """
    Validate the dataset and halt execution if required columns are missing.
    
    Args:
        df: The DataFrame to validate
        required_cols: Optional set of required columns (defaults to REQUIRED_COLUMNS)
        raise_on_missing: If True, raises ValueError when columns are missing.
                         If False, returns False without raising.
    
    Returns:
        True if validation passes, False otherwise.
    
    Raises:
        ValueError: If raise_on_missing is True and required columns are missing.
    """
    missing_cols = validate_required_columns(df, required_cols)
    
    if missing_cols:
        error_msg = (
            f"Dataset validation failed: Missing required columns: {missing_cols}. "
            f"Required columns are: {REQUIRED_COLUMNS}. "
            f"Please ensure the data pipeline (loader -> preprocessor) correctly "
            f"produces these columns."
        )
        logger.error(error_msg)
        
        if raise_on_missing:
            raise ValueError(error_msg)
        return False
    
    logger.info("Dataset validation passed: All required columns present.")
    return True

def create_validation_report(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Create a comprehensive validation report for the dataset.
    
    Returns:
        A dictionary containing:
        - schema_validation: Result of required column check
        - data_quality: Result of data quality checks
        - summary: Overall validation status
    """
    missing_cols = validate_required_columns(df)
    quality_report = validate_data_quality(df)
    
    report = {
        "schema_validation": {
            "missing_columns": missing_cols,
            "required_columns": list(REQUIRED_COLUMNS),
            "passed": len(missing_cols) == 0
        },
        "data_quality": quality_report,
        "summary": {
            "total_rows": len(df),
            "total_columns": len(df.columns),
            "is_valid": len(missing_cols) == 0 and quality_report["valid"]
        }
    }
    
    return report

def validate_and_halt(df: pd.DataFrame, context: str = "Dataset") -> None:
    """
    Convenience function to validate a dataset and halt if invalid.
    
    Args:
        df: The DataFrame to validate
        context: A string describing what is being validated (for logging)
    
    Raises:
        ValueError: If validation fails
    """
    logger.info(f"Validating {context}...")
    report = create_validation_report(df)
    
    if not report["summary"]["is_valid"]:
        error_details = []
        if not report["schema_validation"]["passed"]:
            error_details.append(
                f"Missing columns: {report['schema_validation']['missing_columns']}"
            )
        if not report["data_quality"]["valid"]:
            error_details.append("Data quality issues detected (negative values)")
        
        error_msg = (
            f"{context} validation failed:\n" + 
            "\n".join([f"  - {d}" for d in error_details])
        )
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    logger.info(f"{context} validation successful.")
    return None

# Ensure numpy is imported for isinf checks
import numpy as np
