import os
import sys
import logging
import json
from pathlib import Path
from typing import Dict, Any, List
import yaml

# Add project root to path if running as script
if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(project_root))

from utils.logging_config import get_logger
from utils.config import get_specs_path, get_results_path, get_processed_path

logger = get_logger(__name__)

def load_schema(schema_path: Path) -> Dict[str, Any]:
    """Load the YAML schema definition."""
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(schema_path, 'r') as f:
        schema = yaml.safe_load(f)
    
    logger.info(f"Loaded schema from {schema_path}")
    return schema

def validate_csv_against_schema(data_path: Path, schema: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate a CSV file against a YAML schema.
    
    Checks:
    1. Required columns exist.
    2. Column types match schema (string vs number).
    3. No nulls in required columns.
    
    Returns a validation report dictionary.
    """
    import pandas as pd
    import numpy as np

    if not data_path.exists():
        raise FileNotFoundError(f"Data file not found: {data_path}")

    df = pd.read_csv(data_path)
    logger.info(f"Loaded data from {data_path} with shape {df.shape}")

    report = {
        "data_file": str(data_path),
        "schema_file": str(Path(schema.get("_path", "unknown"))),
        "valid": True,
        "errors": [],
        "warnings": [],
        "row_count": len(df),
        "column_count": len(df.columns),
        "missing_required_columns": [],
        "type_mismatches": [],
        "nulls_in_required": []
    }

    # Map schema types to pandas dtypes
    type_mapping = {
        "string": ["object", "string"],
        "number": ["int64", "float64", "int32", "float32"]
    }

    required_cols = schema.get("required", [])
    properties = schema.get("properties", {})

    # 1. Check required columns
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        report["missing_required_columns"] = missing_cols
        report["errors"].append(f"Missing required columns: {missing_cols}")
        report["valid"] = False
        logger.error(f"Missing required columns: {missing_cols}")

    # 2. Check types for defined properties
    for col_name, col_spec in properties.items():
        if col_name not in df.columns:
            continue  # Optional columns not present are fine unless in 'required'

        expected_type = col_spec.get("type")
        if not expected_type:
            continue

        actual_dtype = df[col_name].dtype
        
        # Check for nulls in required columns (even if type matches)
        if col_name in required_cols:
            null_count = df[col_name].isna().sum()
            if null_count > 0:
                report["nulls_in_required"].append({
                    "column": col_name,
                    "count": int(null_count)
                })
                report["errors"].append(f"Column '{col_name}' has {null_count} null values")
                report["valid"] = False
                logger.error(f"Column '{col_name}' has {null_count} null values")

        # Type check
        if expected_type in type_mapping:
            valid_dtypes = type_mapping[expected_type]
            if str(actual_dtype) not in valid_dtypes:
                # Special handling: object can be numeric strings, but let's check content
                if expected_type == "number" and actual_dtype == "object":
                    # Try to coerce
                    try:
                        pd.to_numeric(df[col_name], errors='raise')
                        report["warnings"].append(f"Column '{col_name}' is object but contains numeric data")
                    except (ValueError, TypeError):
                        report["type_mismatches"].append({
                            "column": col_name,
                            "expected": expected_type,
                            "actual": str(actual_dtype),
                            "reason": "Contains non-numeric strings"
                        })
                        report["valid"] = False
                        logger.error(f"Column '{col_name}' type mismatch: expected {expected_type}, got {actual_dtype}")
                else:
                    report["type_mismatches"].append({
                        "column": col_name,
                        "expected": expected_type,
                        "actual": str(actual_dtype)
                    })
                    report["valid"] = False
                    logger.error(f"Column '{col_name}' type mismatch: expected {expected_type}, got {actual_dtype}")

    # 3. Check additionalProperties (dynamic columns)
    if schema.get("additionalProperties", {}).get("type") == "number":
        defined_cols = set(properties.keys())
        required_set = set(required_cols)
        
        # Find columns not in properties
        dynamic_cols = [c for c in df.columns if c not in properties]
        
        for col in dynamic_cols:
            # Check if it's a required column already checked
            if col in required_set and col not in properties:
                continue 
            
            # Check if numeric
            if not pd.api.types.is_numeric_dtype(df[col]):
                try:
                    pd.to_numeric(df[col], errors='raise')
                    report["warnings"].append(f"Dynamic column '{col}' is object but contains numeric data")
                except (ValueError, TypeError):
                    report["type_mismatches"].append({
                        "column": col,
                        "expected": "number (additionalProperties)",
                        "actual": str(df[col].dtype),
                        "reason": "Non-numeric dynamic column"
                    })
                    # Not necessarily a failure if schema allows additionalProperties to be anything, 
                    # but spec says type: number, so we flag it.
                    # Depending on strictness, this might invalidate.
                    # Let's be strict: if schema says additionalProperties: number, it must be number.
                    report["valid"] = False
                    logger.error(f"Dynamic column '{col}' is not numeric as required by additionalProperties")

    return report

def run_validation(data_path: Path, schema_path: Path, output_path: Path) -> bool:
    """Run the full validation pipeline and write results."""
    try:
        schema = load_schema(schema_path)
        # Attach path to schema for reporting
        schema["_path"] = schema_path
        
        report = validate_csv_against_schema(data_path, schema)
        
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Validation report written to {output_path}")
        
        if report["valid"]:
            logger.info("Schema validation PASSED")
            return True
        else:
            logger.warning(f"Schema validation FAILED: {len(report['errors'])} errors found")
            return False
            
    except Exception as e:
        logger.exception(f"Validation failed with exception: {e}")
        error_report = {
            "valid": False,
            "error": str(e),
            "data_file": str(data_path),
            "schema_file": str(schema_path)
        }
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(error_report, f, indent=2)
        return False

def main():
    """Main entry point for schema validation task."""
    specs_path = get_specs_path()
    results_path = get_results_path()
    processed_path = get_processed_path()
    
    schema_file = specs_path / "001-investigating-the-correlation-between-gu" / "contracts" / "dataset.schema.yaml"
    data_file = processed_path / "cleared_final.csv"
    output_file = results_path / "schema_validation_report.json"
    
    logger.info(f"Starting schema validation...")
    logger.info(f"Data file: {data_file}")
    logger.info(f"Schema file: {schema_file}")
    logger.info(f"Output file: {output_file}")
    
    success = run_validation(data_file, schema_file, output_file)
    
    if not success:
        logger.error("Schema validation failed. Please check the report.")
        sys.exit(1)
    else:
        logger.info("Schema validation completed successfully.")
        sys.exit(0)

if __name__ == "__main__":
    main()
