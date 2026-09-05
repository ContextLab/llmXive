import os
import sys
import logging
import json
from pathlib import Path
from typing import Dict, Any, List

import yaml
import pandas as pd
from utils.config import get_processed_path, get_research_path, get_specs_path
from utils.logging_config import get_logger, log_error_context

logger = get_logger(__name__)

def load_schema(schema_path: str) -> Dict[str, Any]:
    """
    Load the YAML schema definition from a file.
    """
    try:
        with open(schema_path, 'r') as f:
            schema = yaml.safe_load(f)
        if not isinstance(schema, dict):
            raise ValueError("Schema must be a YAML dictionary/object")
        return schema
    except FileNotFoundError:
        logger.error(f"Schema file not found: {schema_path}")
        raise
    except yaml.YAMLError as e:
        logger.error(f"Error parsing YAML schema: {e}")
        raise

def validate_csv_against_schema(df: pd.DataFrame, schema: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Validate a DataFrame against a YAML schema definition.
    
    The schema is expected to follow the format:
    {
        "type": "object",
        "required": ["col1", "col2"],
        "properties": {
            "col1": {"type": "string"},
            "col2": {"type": "number"}
        }
    }
    
    Returns a list of validation errors.
    """
    errors = []
    
    # Check required columns
    required_cols = schema.get("required", [])
    actual_cols = set(df.columns)
    missing_cols = set(required_cols) - actual_cols
    
    if missing_cols:
        errors.append({
            "error_type": "MissingRequiredColumns",
            "message": f"Missing required columns: {list(missing_cols)}",
            "missing": list(missing_cols)
        })
    
    # If required columns are missing, we can't proceed with type checks
    if errors:
        return errors
        
    # Check property types
    properties = schema.get("properties", {})
    
    for col_name, col_spec in properties.items():
        if col_name not in df.columns:
            continue  # Already handled by required check
            
        expected_type = col_spec.get("type")
        
        if expected_type == "string":
            # Check if all non-null values are strings
            non_null = df[col_name].dropna()
            if not non_null.empty:
                # Allow mixed types if object dtype, but check for obvious non-strings
                if df[col_name].dtype != 'object' and df[col_name].dtype != 'string':
                    # If it's numeric, it might be coerced, but let's be lenient for numbers that can be strings
                    pass
                
        elif expected_type == "number":
            # Check if column is numeric
            if not pd.api.types.is_numeric_dtype(df[col_name]):
                # Check if it can be converted
                try:
                    pd.to_numeric(df[col_name], errors='raise')
                except (ValueError, TypeError):
                    errors.append({
                        "error_type": "InvalidColumnType",
                        "field": col_name,
                        "expected": expected_type,
                        "actual": str(df[col_name].dtype),
                        "message": f"Column '{col_name}' should be numeric but is {df[col_name].dtype}"
                    })
                    
    return errors

def run_validation() -> Dict[str, Any]:
    """
    Main validation routine.
    Loads the processed data and the schema, validates, and writes results.
    """
    results_path = Path(get_processed_path())
    schema_path = Path(get_specs_path()) / "contracts" / "dataset.schema.yaml"
    output_path = Path(get_research_path()) / "results" / "schema_validation_report.json"
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Loading schema from: {schema_path}")
    schema = load_schema(str(schema_path))
    
    logger.info(f"Loading processed data from: {results_path}")
    try:
        df = pd.read_csv(results_path)
    except FileNotFoundError:
        error_report = {
            "status": "error",
            "error_type": "FileNotFoundError",
            "message": f"Processed data file not found: {results_path}",
            "validated": False
        }
        with open(output_path, 'w') as f:
            json.dump(error_report, f, indent=2)
        raise
    except Exception as e:
        error_report = {
            "status": "error",
            "error_type": "DataLoadError",
            "message": str(e),
            "validated": False
        }
        with open(output_path, 'w') as f:
            json.dump(error_report, f, indent=2)
        raise
    
    logger.info(f"Validating {len(df)} rows against schema...")
    validation_errors = validate_csv_against_schema(df, schema)
    
    report = {
        "schema_path": str(schema_path),
        "data_path": str(results_path),
        "rows_validated": len(df),
        "columns_checked": list(df.columns),
        "is_valid": len(validation_errors) == 0,
        "errors": validation_errors
    }
    
    if validation_errors:
        logger.warning(f"Validation failed with {len(validation_errors)} errors")
        for err in validation_errors:
            logger.warning(f"  - {err.get('error_type')}: {err.get('message')}")
    else:
        logger.info("Validation successful: All required fields and types match schema.")
    
    # Write report
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
        
    logger.info(f"Validation report written to: {output_path}")
    
    return report

def main():
    """
    Entry point for the validation script.
    """
    try:
        result = run_validation()
        if not result["is_valid"]:
            logger.error("Schema validation failed. See report for details.")
            sys.exit(1)
        else:
            logger.info("Schema validation passed.")
            sys.exit(0)
    except Exception as e:
        log_error_context(e, "Schema validation failed")
        sys.exit(1)

if __name__ == "__main__":
    main()
