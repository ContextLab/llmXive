import os
import sys
import logging
import json
from pathlib import Path
from typing import Dict, Any, List

import yaml
import pandas as pd
from code.utils.logging_config import get_logger, log_error_context
from code.utils.config import get_processed_path, get_specs_path, get_research_path

logger = get_logger(__name__)

def load_schema(schema_path: Path) -> Dict[str, Any]:
    """Load the YAML schema definition."""
    logger.info(f"Loading schema from {schema_path}")
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(schema_path, 'r') as f:
        schema = yaml.safe_load(f)
    
    if not isinstance(schema, dict):
        raise ValueError("Schema must be a YAML object (dict)")
    
    return schema

def validate_csv_against_schema(data_path: Path, schema: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate a CSV file against the provided schema.
    
    Checks:
    1. Required columns exist (mapping schema 'required' to CSV headers).
    2. Data types for numeric columns are valid.
    3. No null values in required columns.
    """
    validation_results = {
        "data_path": str(data_path),
        "schema_path": str(schema.get("_path", "unknown")),
        "valid": True,
        "errors": [],
        "warnings": [],
        "row_count": 0,
        "column_count": 0
    }

    if not data_path.exists():
        validation_results["valid"] = False
        validation_results["errors"].append(f"Data file not found: {data_path}")
        return validation_results

    try:
        df = pd.read_csv(data_path)
    except Exception as e:
        validation_results["valid"] = False
        validation_results["errors"].append(f"Failed to read CSV: {str(e)}")
        return validation_results

    validation_results["row_count"] = len(df)
    validation_results["column_count"] = len(df.columns)

    required_fields = schema.get("required", [])
    properties = schema.get("properties", {})

    # Map schema required fields to CSV columns
    # The schema defines 'taxa_abundances' as an object, but in CSV these are flat columns.
    # We validate the explicit scalar required fields first.
    explicit_required = [f for f in required_fields if f != 'taxa_abundances']
    
    missing_cols = []
    for field in explicit_required:
        if field not in df.columns:
            missing_cols.append(field)
    
    if missing_cols:
        validation_results["valid"] = False
        validation_results["errors"].append(f"Missing required columns: {missing_cols}")

    # Check for nulls in required scalar columns
    for field in explicit_required:
        if field in df.columns:
            null_count = df[field].isnull().sum()
            if null_count > 0:
                validation_results["valid"] = False
                validation_results["errors"].append(
                    f"Column '{field}' contains {null_count} null values (required field)."
                )

    # Validate numeric types for known numeric fields
    numeric_fields = ['titer_baseline', 'titer_post', 'shannon_diversity', 'log_titer']
    for field in numeric_fields:
        if field in df.columns:
            if not pd.api.types.is_numeric_dtype(df[field]):
                validation_results["warnings"].append(
                    f"Column '{field}' is not numeric (dtype: {df[field].dtype}). "
                    "Attempting to coerce."
                )
                try:
                    df[field] = pd.to_numeric(df[field], errors='raise')
                except ValueError:
                    validation_results["valid"] = False
                    validation_results["errors"].append(
                        f"Column '{field}' contains non-numeric values that cannot be coerced."
                    )

    # Validate taxa abundances (all columns not in explicit required or known metadata)
    # Assuming any column starting with 'taxon_' or present in the schema's additionalProperties context
    # is a taxon abundance and should be numeric.
    known_metadata = set(explicit_required + ['subject_id'])
    taxon_cols = [c for c in df.columns if c not in known_metadata]
    
    for col in taxon_cols:
        if not pd.api.types.is_numeric_dtype(df[col]):
            # It's common for taxon columns to be floats. If they are objects, try to convert.
            validation_results["warnings"].append(
                f"Taxon column '{col}' is not numeric (dtype: {df[col].dtype}). "
                "Attempting to coerce."
            )
            try:
                df[col] = pd.to_numeric(df[col], errors='raise')
            except ValueError:
                validation_results["valid"] = False
                validation_results["errors"].append(
                    f"Taxon column '{col}' contains non-numeric values."
                )

    return validation_results

def run_validation() -> Dict[str, Any]:
    """Main entry point for schema validation."""
    logger.info("Starting schema validation task T013")
    
    # Determine paths
    # The schema is in specs/.../contracts/
    specs_root = get_specs_path()
    schema_path = specs_root / "contracts" / "dataset.schema.yaml"
    
    # The data is in data/processed/cleared_final.csv
    processed_path = get_processed_path()
    data_path = processed_path / "cleared_final.csv"
    
    # Output report
    results_path = get_research_path() / "results"
    results_path.mkdir(parents=True, exist_ok=True)
    output_path = results_path / "schema_validation_report.json"

    try:
        schema = load_schema(schema_path)
        schema["_path"] = str(schema_path) # Tag for report
        
        report = validate_csv_against_schema(data_path, schema)
        
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Validation complete. Report written to {output_path}")
        if report["valid"]:
            logger.info("Schema validation PASSED.")
        else:
            logger.warning("Schema validation FAILED. See errors in report.")
            
        return report

    except Exception as e:
        log_error_context(e, "Schema validation failed")
        return {
            "valid": False,
            "errors": [str(e)],
            "data_path": str(data_path),
            "schema_path": str(schema_path)
        }

def main():
    """CLI entry point."""
    result = run_validation()
    if not result.get("valid", False):
        sys.exit(1)
    sys.exit(0)

if __name__ == "__main__":
    main()
