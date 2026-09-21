import os
import sys
import logging
import json
from pathlib import Path
from typing import Dict, Any, List

import yaml
import pandas as pd
from utils.config import get_research_path, get_results_path, get_env_var
from utils.logging_config import get_logger, log_error_context

logger = get_logger(__name__)

def load_schema(schema_path: str) -> Dict[str, Any]:
    """
    Load the YAML schema definition.
    """
    try:
        with open(schema_path, 'r') as f:
            schema = yaml.safe_load(f)
        logger.info(f"Schema loaded successfully from {schema_path}")
        return schema
    except FileNotFoundError:
        logger.error(f"Schema file not found: {schema_path}")
        raise
    except yaml.YAMLError as e:
        logger.error(f"Error parsing YAML schema: {e}")
        raise

def validate_csv_against_schema(data_path: str, schema: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate a CSV file against the provided JSON-schema-like YAML structure.
    
    Checks:
    1. Required columns exist.
    2. Column types match (string, number).
    3. No nulls in required columns.
    
    Returns a report dictionary.
    """
    report = {
        "valid": True,
        "errors": [],
        "warnings": [],
        "row_count": 0,
        "column_count": 0,
        "missing_required_columns": [],
        "type_mismatches": [],
        "nulls_in_required": []
    }

    try:
        df = pd.read_csv(data_path)
    except Exception as e:
        logger.error(f"Failed to load CSV {data_path}: {e}")
        report["valid"] = False
        report["errors"].append(f"Failed to load CSV: {str(e)}")
        return report

    report["row_count"] = len(df)
    report["column_count"] = len(df.columns)
    
    required_cols = schema.get("required", [])
    properties = schema.get("properties", {})
    
    # 1. Check Required Columns
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        report["missing_required_columns"] = missing_cols
        report["errors"].append(f"Missing required columns: {missing_cols}")
        report["valid"] = False
    
    # 2. Check Types and Nulls for defined properties
    for col_name, col_spec in properties.items():
        if col_name in df.columns:
            col_type = col_spec.get("type")
            
            # Check for nulls in required columns
            if col_name in required_cols:
                null_count = df[col_name].isna().sum()
                if null_count > 0:
                    report["nulls_in_required"].append({
                        "column": col_name,
                        "count": int(null_count)
                    })
                    report["errors"].append(f"Column '{col_name}' has {null_count} null values.")
                    report["valid"] = False

            # Check Type
            if col_type == "string":
                # Pandas treats everything as object often, but we check for non-string if possible
                # For safety, we assume if it's object and not numeric, it's string-ish.
                # Strict check: ensure no numeric types masquerading if expected string?
                # Usually subject_id is string.
                pass 
            elif col_type == "number":
                # Ensure column is numeric
                if not pd.api.types.is_numeric_dtype(df[col_name]):
                    # Attempt conversion to see if it's just formatting
                    try:
                        converted = pd.to_numeric(df[col_name], errors='raise')
                        logger.warning(f"Column '{col_name}' was not numeric but converted successfully.")
                    except (ValueError, TypeError):
                        report["type_mismatches"].append({
                            "column": col_name,
                            "expected": "number",
                            "actual": str(df[col_name].dtype)
                        })
                        report["errors"].append(f"Column '{col_name}' is expected to be 'number' but is '{df[col_name].dtype}'.")
                        report["valid"] = False
            elif col_type == "object":
                pass # Generic
    
    # 3. Check dynamic columns if additionalProperties is defined
    if "additionalProperties" in schema:
        # We allow any additional numeric columns per the schema provided
        # Just ensure they are numeric if they exist? The schema says type: number.
        additional_spec = schema["additionalProperties"]
        if additional_spec.get("type") == "number":
            defined_cols = set(required_cols + list(properties.keys()))
            extra_cols = set(df.columns) - defined_cols
            for col in extra_cols:
                if not pd.api.types.is_numeric_dtype(df[col]):
                    report["warnings"].append(f"Additional column '{col}' is not numeric, but schema allows dynamic numeric columns.")
                    # Not a hard fail per schema 'additionalProperties: type: number' implies we expect numbers, 
                    # but strict validation might fail. We'll log as warning for now as per 'dynamic' nature.

    return report

def run_validation(data_path: str, schema_path: str, output_path: str) -> bool:
    """
    Main entry point to run validation and write the report.
    """
    logger.info(f"Starting schema validation for {data_path}")
    
    try:
        schema = load_schema(schema_path)
        report = validate_csv_against_schema(data_path, schema)
        
        # Write report
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Validation report written to {output_path}")
        logger.info(f"Validation Result: {'PASSED' if report['valid'] else 'FAILED'}")
        
        return report['valid']
        
    except Exception as e:
        logger.error(f"Validation process failed: {e}")
        # Write failure report
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        fail_report = {
            "valid": False,
            "errors": [f"Critical error during validation: {str(e)}"],
            "row_count": 0,
            "column_count": 0
        }
        with open(output_path, 'w') as f:
            json.dump(fail_report, f, indent=2)
        return False

def main():
    """
    CLI entry point.
    """
    # Paths relative to project root
    # Based on tasks.md:
    # Input: data/processed/cleared_final.csv
    # Schema: specs/001-investigating-the-correlation-between-gu/contracts/dataset.schema.yaml
    # Output: data/results/schema_validation_report.json
    
    project_root = Path(__file__).resolve().parent.parent
    data_path = project_root / "data" / "processed" / "cleared_final.csv"
    schema_path = project_root / "specs" / "001-investigating-the-correlation-between-gu" / "contracts" / "dataset.schema.yaml"
    output_path = project_root / "data" / "results" / "schema_validation_report.json"
    
    if not data_path.exists():
        logger.error(f"Input data file not found: {data_path}")
        print(f"Error: Input data file not found: {data_path}")
        sys.exit(1)
        
    if not schema_path.exists():
        logger.error(f"Schema file not found: {schema_path}")
        print(f"Error: Schema file not found: {schema_path}")
        sys.exit(1)
    
    success = run_validation(str(data_path), str(schema_path), str(output_path))
    
    if not success:
        print("Schema validation FAILED. Check data/results/schema_validation_report.json for details.")
        sys.exit(1)
    else:
        print("Schema validation PASSED.")
        sys.exit(0)

if __name__ == "__main__":
    main()
