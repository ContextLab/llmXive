"""
Verification script for T017: Verify output file data/processed/features.parquet
contains no full semantic context strings and matches dataset.schema.yaml.
"""
import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Set
import pyarrow.parquet as pq
import pandas as pd
import yaml

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from logging_config import setup_logging
from config import get_path, load_config

# Setup logging
logger = setup_logging(level="INFO")

# Constants
FEATURES_FILE = get_path("processed_features")
SCHEMA_FILE = get_path("dataset_schema")
OUTPUT_REPORT = get_path("verification_report")
CONTEXT_KEYWORDS = ["context_text", "full_context", "semantic_context", "prompt_context", "raw_context"]
MAX_STRING_LENGTH = 500  # Threshold to flag potential full context strings
MAX_COLUMN_LENGTH = 100  # Threshold for column names that might indicate context

def load_schema(schema_path: Path) -> Dict[str, Any]:
    """Load and parse the dataset schema YAML."""
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(schema_path, 'r') as f:
        schema = yaml.safe_load(f)
    return schema

def validate_schema_compliance(df: pd.DataFrame, schema: Dict[str, Any]) -> List[str]:
    """Check if DataFrame matches the schema definition."""
    errors = []
    
    expected_columns = set(schema.get("fields", {}).keys())
    actual_columns = set(df.columns)
    
    # Check for missing columns
    missing_cols = expected_columns - actual_columns
    if missing_cols:
        errors.append(f"Missing columns in DataFrame: {missing_cols}")
    
    # Check for unexpected columns
    extra_cols = actual_columns - expected_columns
    if extra_cols:
        errors.append(f"Unexpected columns in DataFrame: {extra_cols}")
    
    # Check column types if specified
    fields = schema.get("fields", {})
    for col_name, col_def in fields.items():
        if col_name in actual_columns:
            expected_dtype = col_def.get("type")
            if expected_dtype:
                actual_dtype = str(df[col_name].dtype)
                # Simple type mapping
                type_map = {
                    "integer": "int64",
                    "number": "float64",
                    "string": "object",
                    "boolean": "bool"
                }
                expected_mapped = type_map.get(expected_dtype, expected_dtype)
                if expected_mapped not in actual_dtype:
                    errors.append(f"Column '{col_name}' has dtype '{actual_dtype}', expected '{expected_mapped}'")
    
    return errors

def detect_full_context_strings(df: pd.DataFrame) -> List[str]:
    """Detect columns that might contain full semantic context strings."""
    suspicious_columns = []
    
    for col in df.columns:
        # Check column name for context indicators
        if any(keyword in col.lower() for keyword in CONTEXT_KEYWORDS):
            suspicious_columns.append(f"Column name '{col}' contains context keyword")
            continue
        
        # Check if column is string type and has long values
        if df[col].dtype == object:
            # Sample some values to check length
            sample = df[col].dropna().head(10)
            if len(sample) > 0:
                max_len = sample.str.len().max()
                if max_len > MAX_STRING_LENGTH:
                    suspicious_columns.append(
                        f"Column '{col}' contains strings longer than {MAX_STRING_LENGTH} chars (max: {max_len})"
                    )
    
    return suspicious_columns

def generate_report(
    schema_errors: List[str],
    context_errors: List[str],
    file_path: str,
    row_count: int,
    column_count: int
) -> Dict[str, Any]:
    """Generate the verification report."""
    is_valid = len(schema_errors) == 0 and len(context_errors) == 0
    
    report = {
        "task_id": "T017",
        "file_path": file_path,
        "row_count": row_count,
        "column_count": column_count,
        "is_valid": is_valid,
        "schema_compliance": {
            "passed": len(schema_errors) == 0,
            "errors": schema_errors
        },
        "context_check": {
            "passed": len(context_errors) == 0,
            "errors": context_errors
        },
        "summary": "PASSED" if is_valid else "FAILED"
    }
    
    return report

def main():
    """Main verification function."""
    logger.info(f"Starting verification for T017")
    logger.info(f"Features file: {FEATURES_FILE}")
    logger.info(f"Schema file: {SCHEMA_FILE}")
    
    try:
        # Load schema
        logger.info("Loading schema...")
        schema = load_schema(SCHEMA_FILE)
        
        # Load parquet file
        logger.info("Loading features file...")
        if not os.path.exists(FEATURES_FILE):
            raise FileNotFoundError(f"Features file not found: {FEATURES_FILE}")
        
        table = pq.read_table(FEATURES_FILE)
        df = table.to_pandas()
        
        row_count = len(df)
        column_count = len(df.columns)
        logger.info(f"Loaded {row_count} rows and {column_count} columns")
        
        # Validate schema compliance
        logger.info("Validating schema compliance...")
        schema_errors = validate_schema_compliance(df, schema)
        if schema_errors:
            logger.warning(f"Schema validation errors: {schema_errors}")
        else:
            logger.info("Schema validation passed")
        
        # Check for full context strings
        logger.info("Checking for full context strings...")
        context_errors = detect_full_context_strings(df)
        if context_errors:
            logger.warning(f"Context check errors: {context_errors}")
        else:
            logger.info("Context check passed - no full context strings detected")
        
        # Generate report
        report = generate_report(
            schema_errors=schema_errors,
            context_errors=context_errors,
            file_path=str(FEATURES_FILE),
            row_count=row_count,
            column_count=column_count
        )
        
        # Save report
        OUTPUT_REPORT.parent.mkdir(parents=True, exist_ok=True)
        with open(OUTPUT_REPORT, 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info(f"Verification report saved to: {OUTPUT_REPORT}")
        
        # Exit with appropriate code
        if report["is_valid"]:
            logger.info("VERIFICATION PASSED")
            return 0
        else:
            logger.error("VERIFICATION FAILED")
            return 1
            
    except Exception as e:
        logger.error(f"Verification failed with error: {str(e)}")
        # Create error report
        error_report = {
            "task_id": "T017",
            "is_valid": False,
            "error": str(e),
            "summary": "FAILED"
        }
        OUTPUT_REPORT.parent.mkdir(parents=True, exist_ok=True)
        with open(OUTPUT_REPORT, 'w') as f:
            json.dump(error_report, f, indent=2)
        return 1

if __name__ == "__main__":
    sys.exit(main())