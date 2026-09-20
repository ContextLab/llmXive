import os
import sys
import logging
import json
from pathlib import Path
from typing import Dict, Any, List

import yaml
import pandas as pd

from utils.logging_config import get_logger
from utils.config import get_specs_path, get_results_path

logger = get_logger(__name__)

def load_schema(schema_path: Path) -> Dict[str, Any]:
    """Load the YAML schema definition."""
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(schema_path, 'r') as f:
        schema = yaml.safe_load(f)
    
    logger.info(f"Loaded schema from {schema_path}")
    return schema

def validate_csv_against_schema(df: pd.DataFrame, schema: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate a DataFrame against a JSON/YAML schema.
    
    Returns a report dict with:
    - valid: bool
    - errors: list of error messages
    - missing_required: list of missing required columns
    - type_errors: list of type mismatch errors
    """
    errors = []
    missing_required = []
    type_errors = []
    
    # Check required columns
    required_cols = schema.get('required', [])
    actual_cols = set(df.columns)
    
    for col in required_cols:
        if col not in actual_cols:
            missing_required.append(col)
            errors.append(f"Missing required column: {col}")
    
    # Check property types
    properties = schema.get('properties', {})
    
    for col_name, col_spec in properties.items():
        if col_name in actual_cols:
            expected_type = col_spec.get('type')
            if expected_type == 'string':
                if not all(df[col_name].apply(lambda x: isinstance(x, str) or pd.isna(x))):
                    msg = f"Column '{col_name}' contains non-string values"
                    type_errors.append(msg)
                    errors.append(msg)
            elif expected_type == 'number':
                # Check if numeric (allow NaN)
                if not all(pd.api.types.is_numeric_dtype(df[[col_name]]) or pd.isna(df[col_name]).all()):
                    # Try to coerce to numeric to be lenient
                    try:
                        pd.to_numeric(df[col_name], errors='raise')
                    except (ValueError, TypeError):
                        msg = f"Column '{col_name}' is not numeric and cannot be coerced"
                        type_errors.append(msg)
                        errors.append(msg)
    
    # Check additionalProperties constraint (all columns must be valid types)
    additional_props = schema.get('additionalProperties', {})
    if additional_props:
        allowed_types = []
        if additional_props.get('type') == 'number':
            allowed_types = ['number']
        
        for col in actual_cols:
            if col not in properties and col not in required_cols:
                # This column falls under additionalProperties
                if allowed_types == ['number']:
                    if not pd.api.types.is_numeric_dtype(df[[col]]):
                        msg = f"Additional column '{col}' is not numeric"
                        type_errors.append(msg)
                        errors.append(msg)
    
    report = {
        "valid": len(errors) == 0,
        "errors": errors,
        "missing_required": missing_required,
        "type_errors": type_errors,
        "schema_path": str(schema_path),
        "data_path": str(data_path),
        "row_count": len(df),
        "column_count": len(df.columns),
        "columns_checked": list(df.columns)
    }
    
    return report

def run_validation(input_path: Path, schema_path: Path, output_path: Path) -> Dict[str, Any]:
    """
    Main validation pipeline:
    1. Load schema
    2. Load CSV
    3. Validate
    4. Write report
    """
    logger.info(f"Starting schema validation for {input_path}")
    
    # Load schema
    schema = load_schema(schema_path)
    
    # Load data
    if not input_path.exists():
        raise FileNotFoundError(f"Input data file not found: {input_path}")
    
    df = pd.read_csv(input_path)
    logger.info(f"Loaded data with {len(df)} rows and {len(df.columns)} columns")
    
    # Validate
    report = validate_csv_against_schema(df, schema)
    
    # Write report
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Validation report written to {output_path}")
    logger.info(f"Validation result: {'PASSED' if report['valid'] else 'FAILED'}")
    
    if not report['valid']:
        for err in report['errors']:
            logger.warning(f"Validation error: {err}")
    
    return report

def main():
    """Entry point for the validation script."""
    # Define paths
    specs_path = get_specs_path()
    results_path = get_results_path()
    
    schema_path = specs_path / "001-investigating-the-correlation-between-gu" / "contracts" / "dataset.schema.yaml"
    input_path = Path("data/processed/cleared_final.csv")
    output_path = results_path / "schema_validation_report.json"
    
    try:
        report = run_validation(input_path, schema_path, output_path)
        
        # Exit with appropriate code
        if report['valid']:
            logger.info("Schema validation completed successfully.")
            sys.exit(0)
        else:
            logger.error("Schema validation failed.")
            sys.exit(1)
            
    except Exception as e:
        logger.exception(f"Validation pipeline failed with exception: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
