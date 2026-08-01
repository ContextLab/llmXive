import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
import yaml
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

def load_schema(schema_path: Path) -> Dict[str, Any]:
    """Load a YAML schema definition."""
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

def validate_column_schema(df: pd.DataFrame, schema: Dict[str, Any]) -> List[str]:
    """Validate DataFrame columns against a schema."""
    errors = []
    expected_cols = schema.get("columns", {})
    
    for col_name, col_spec in expected_cols.items():
        if col_name not in df.columns:
            errors.append(f"Missing column: {col_name}")
            continue
        
        col_dtype = df[col_name].dtype
        expected_type = col_spec.get("type")
        
        # Simple type checking
        if expected_type == "float" and not np.issubdtype(col_dtype, np.floating):
            if col_name not in ["ecfp4", "maccs"]: # Fingerprint columns might be object/list
                errors.append(f"Column {col_name} expected float, got {col_dtype}")
        
    return errors

def validate_fingerprint_dimensions(df: pd.DataFrame, fingerprint_col: str, expected_dim: int) -> List[str]:
    """Validate that fingerprint vectors have the expected dimension."""
    errors = []
    if fingerprint_col not in df.columns:
        return [f"Column {fingerprint_col} not found"]
    
    # Check first few rows
    sample = df[fingerprint_col].iloc[:5]
    for i, val in enumerate(sample):
        if isinstance(val, list) or isinstance(val, np.ndarray):
            if len(val) != expected_dim:
                errors.append(f"Row {i}: {fingerprint_col} has length {len(val)}, expected {expected_dim}")
        else:
            errors.append(f"Row {i}: {fingerprint_col} is not a list/array")
            
    return errors

def validate_record_content(df: pd.DataFrame, schema: Dict[str, Any]) -> List[str]:
    """Validate content of records (e.g., non-nulls, ranges)."""
    errors = []
    required_cols = schema.get("required_columns", [])
    for col in required_cols:
        if df[col].isnull().any():
            errors.append(f"Column {col} contains null values")
    return errors

def validate_dataset(df: pd.DataFrame, schema_path: Path) -> Dict[str, Any]:
    """Run all validations and return a report."""
    schema = load_schema(schema_path)
    report = {
        "valid": True,
        "errors": []
    }
    
    col_errors = validate_column_schema(df, schema)
    if col_errors:
        report["valid"] = False
        report["errors"].extend(col_errors)
        
    # Example for fingerprint validation
    if "ecfp4" in df.columns:
        fp_errors = validate_fingerprint_dimensions(df, "ecfp4", 2048)
        if fp_errors:
            report["valid"] = False
            report["errors"].extend(fp_errors)
    
    content_errors = validate_record_content(df, schema)
    if content_errors:
        report["valid"] = False
        report["errors"].extend(content_errors)
        
    return report

def save_validation_report(report: Dict[str, Any], output_path: Path) -> None:
    """Save validation report to JSON."""
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
