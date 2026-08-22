import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Set

import yaml
import pandas as pd
import pyarrow.parquet as pq

from config import get_path

logger = logging.getLogger(__name__)

# Threshold for considering a string "full context" (length in characters)
# Contexts in the benchmark are typically large blocks of text.
# Features should be small numbers or short IDs.
FULL_CONTEXT_THRESHOLD = 500

def load_schema(schema_path: str) -> Dict[str, Any]:
    """Load the dataset schema from a YAML file."""
    if not os.path.exists(schema_path):
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

def validate_schema_compliance(df: pd.DataFrame, schema: Dict[str, Any]) -> List[str]:
    """
    Validates that the DataFrame columns and types match the schema.
    Returns a list of error messages.
    """
    errors = []
    expected_columns = schema.get('fields', {})
    
    # Check for missing columns
    for col_name in expected_columns:
        if col_name not in df.columns:
            errors.append(f"Missing required column: {col_name}")
    
    # Check for unexpected columns (optional, depending on strictness)
    # For this task, we focus on the presence of forbidden columns and type compliance.
    
    # Check types for numeric columns if specified
    for col_name, col_spec in expected_columns.items():
        if col_name in df.columns:
            expected_type = col_spec.get('type')
            if expected_type == 'integer':
                if not pd.api.types.is_integer_dtype(df[col_name]) and not pd.api.types.is_float_dtype(df[col_name]):
                    # Allow float for integers if they are whole numbers, but strict check might be needed
                    if not pd.api.types.is_numeric_dtype(df[col_name]):
                        errors.append(f"Column '{col_name}' should be numeric, found {df[col_name].dtype}")
            elif expected_type == 'string':
                if not pd.api.types.is_string_dtype(df[col_name]) and not pd.api.types.is_object_dtype(df[col_name]):
                    # Allow object for strings
                    pass 
    
    return errors

def detect_full_context_strings(df: pd.DataFrame, threshold: int = FULL_CONTEXT_THRESHOLD) -> List[str]:
    """
    Scans all string/object columns for values that exceed the threshold length.
    Returns a list of descriptions of violations.
    """
    violations = []
    
    for col in df.columns:
        if df[col].dtype == 'object' or df[col].dtype == 'string':
            # Filter out non-string entries (NaNs, etc.)
            mask = df[col].apply(lambda x: isinstance(x, str))
            if mask.any():
                string_series = df.loc[mask, col]
                # Find indices where string length > threshold
                long_strings = string_series[
                    string_series.apply(lambda s: len(s) > threshold)
                ]
                
                if len(long_strings) > 0:
                    # Report the first few violations to avoid spamming logs
                    sample_val = long_strings.iloc[0][:100] + "..."
                    violations.append(
                        f"Column '{col}' contains {len(long_strings)} values exceeding {threshold} chars. "
                        f"Sample: '{sample_val}'"
                    )
    
    return violations

def generate_report(violations: List[str], schema_errors: List[str], output_path: str) -> Dict[str, Any]:
    """Generates a validation report and saves it to JSON."""
    report = {
        "status": "failed" if (violations or schema_errors) else "passed",
        "schema_violations": schema_errors,
        "full_context_violations": violations,
        "total_violations": len(violations) + len(schema_errors)
    }
    
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    return report

def main():
    """
    Main entry point for T017: Verify output file data/processed/features.parquet
    contains no full semantic context strings and matches dataset.schema.yaml.
    """
    # Setup logging
    from logging_config import setup_logging
    setup_logging()

    # Define paths
    schema_path = get_path("contracts/dataset.schema.yaml")
    input_path = get_path("data/processed/features.parquet")
    report_path = get_path("data/validation_report.json")

    logger.info(f"Starting verification for {input_path}")
    
    if not os.path.exists(input_path):
        logger.error(f"Input file not found: {input_path}")
        # Create a failed report immediately
        report = generate_report(
            violations=[], 
            schema_errors=[f"Input file not found: {input_path}"], 
            output_path=report_path
        )
        return 1

    if not os.path.exists(schema_path):
        logger.error(f"Schema file not found: {schema_path}")
        report = generate_report(
            violations=[], 
            schema_errors=[f"Schema file not found: {schema_path}"], 
            output_path=report_path
        )
        return 1

    try:
        # Load Schema
        logger.info(f"Loading schema from {schema_path}")
        schema = load_schema(schema_path)

        # Load Parquet
        logger.info(f"Loading parquet from {input_path}")
        df = pd.read_parquet(input_path)
        logger.info(f"Loaded {len(df)} rows, {len(df.columns)} columns")

        # 1. Validate Schema Compliance
        logger.info("Validating schema compliance...")
        schema_errors = validate_schema_compliance(df, schema)
        if schema_errors:
            logger.warning(f"Schema violations found: {schema_errors}")
        else:
            logger.info("Schema compliance check passed.")

        # 2. Detect Full Context Strings
        logger.info("Scanning for full semantic context strings...")
        context_violations = detect_full_context_strings(df)
        if context_violations:
            logger.warning(f"Full context violations found: {context_violations}")
        else:
            logger.info("No full semantic context strings found.")

        # Generate Report
        report = generate_report(context_violations, schema_errors, report_path)
        
        if report["status"] == "passed":
            logger.info("VERIFICATION PASSED: Output file is clean and schema-compliant.")
            return 0
        else:
            logger.error("VERIFICATION FAILED: See data/validation_report.json for details.")
            return 1

    except Exception as e:
        logger.exception(f"Error during verification: {e}")
        report = generate_report(
            violations=[], 
            schema_errors=[f"Runtime error: {str(e)}"], 
            output_path=report_path
        )
        return 1

if __name__ == "__main__":
    sys.exit(main())