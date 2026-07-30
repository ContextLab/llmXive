import os
import sys
import logging
import yaml
from pathlib import Path
import pandas as pd
from typing import Dict, Any, List, Tuple

# Add project root to path if running as script
if __name__ == "__main__":
    project_root = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(project_root / "code"))
else:
    project_root = Path(__file__).resolve().parents[2]

from utils import get_contracts_path, get_data_raw_path, get_data_processed_path, setup_logger, get_logger
from config import load_dataset_urls

logger = setup_logger("validate_schema")

def load_schema(schema_path: Path) -> Dict[str, Any]:
    """Load the YAML schema definition."""
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(schema_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def validate_microbiome_schema(df: pd.DataFrame, schema: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate a microbiome dataframe against the schema.
    Returns (is_valid, list_of_errors).
    """
    errors = []
    
    # Check required columns
    required_cols = schema.get("required_columns", [])
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        errors.append(f"Missing required columns: {missing_cols}")
    
    # Check column types if specified
    column_types = schema.get("column_types", {})
    for col, expected_type in column_types.items():
        if col in df.columns:
            actual_type = str(df[col].dtype)
            # Simple type mapping check
            if expected_type == "numeric" and not pd.api.types.is_numeric_dtype(df[col]):
                errors.append(f"Column '{col}' should be numeric, got {actual_type}")
            elif expected_type == "string" and not pd.api.types.is_string_dtype(df[col]) and not pd.api.types.is_categorical_dtype(df[col]):
                # Allow categorical as string-like
                pass 
            elif expected_type == "integer" and not pd.api.types.is_integer_dtype(df[col]):
                errors.append(f"Column '{col}' should be integer, got {actual_type}")

    # Check for null values in required columns
    for col in required_cols:
        if col in df.columns and df[col].isnull().any():
            errors.append(f"Column '{col}' contains null values")

    return len(errors) == 0, errors

def validate_cognitive_schema(df: pd.DataFrame, schema: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate a cognitive dataframe against the schema.
    Returns (is_valid, list_of_errors).
    """
    errors = []
    
    # Check required columns
    required_cols = schema.get("required_columns", [])
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        errors.append(f"Missing required columns: {missing_cols}")
    
    # Check column types
    column_types = schema.get("column_types", {})
    for col, expected_type in column_types.items():
        if col in df.columns:
            actual_type = str(df[col].dtype)
            if expected_type == "numeric" and not pd.api.types.is_numeric_dtype(df[col]):
                errors.append(f"Column '{col}' should be numeric, got {actual_type}")
            elif expected_type == "string" and not pd.api.types.is_string_dtype(df[col]):
                pass

    # Check for null values in required columns
    for col in required_cols:
        if col in df.columns and df[col].isnull().any():
            errors.append(f"Column '{col}' contains null values")

    return len(errors) == 0, errors

def validate_file_against_schema(file_path: Path, schema_type: str, schema: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate a parquet file against the schema.
    Returns a validation report dictionary.
    """
    report = {
        "file": str(file_path),
        "schema_type": schema_type,
        "valid": False,
        "errors": [],
        "row_count": 0,
        "column_count": 0
    }
    
    try:
        df = pd.read_parquet(file_path)
        report["row_count"] = len(df)
        report["column_count"] = len(df.columns)
        
        if schema_type == "microbiome":
            is_valid, errors = validate_microbiome_schema(df, schema)
        elif schema_type == "cognitive":
            is_valid, errors = validate_cognitive_schema(df, schema)
        elif schema_type == "merged":
            # For merged, we might have a combined schema or just check presence of key columns
            required_cols = schema.get("required_columns", [])
            missing_cols = [col for col in required_cols if col not in df.columns]
            if missing_cols:
                errors = [f"Missing required columns in merged data: {missing_cols}"]
                is_valid = False
            else:
                is_valid = True
                errors = []
        else:
            errors = [f"Unknown schema type: {schema_type}"]
            is_valid = False
        
        report["valid"] = is_valid
        report["errors"] = errors
        
    except Exception as e:
        report["errors"].append(f"Failed to read or validate file: {str(e)}")
    
    return report

def main():
    """
    Main entry point to validate all output parquet files against the schema.
    """
    contracts_path = get_contracts_path()
    schema_path = contracts_path / "dataset.schema.yaml"
    
    if not schema_path.exists():
        logger.error(f"Schema file not found at {schema_path}. Please run T005 first.")
        sys.exit(1)
    
    logger.info(f"Loading schema from {schema_path}")
    schema = load_schema(schema_path)
    
    raw_dir = get_data_raw_path()
    processed_dir = get_data_processed_path()
    
    files_to_validate = []
    
    # Identify files based on naming conventions or explicit schema definitions
    # Assuming standard naming from T011-T015
    microbiome_raw = raw_dir / "microbiome_raw.parquet"
    cognitive_raw = raw_dir / "cognitive_raw.parquet"
    cognitive_processed = processed_dir / "cognitive_processed.parquet"
    merged_data = processed_dir / "merged_dataset.parquet"
    
    if microbiome_raw.exists():
        files_to_validate.append((microbiome_raw, "microbiome"))
    if cognitive_raw.exists():
        files_to_validate.append((cognitive_raw, "cognitive"))
    if cognitive_processed.exists():
        files_to_validate.append((cognitive_processed, "cognitive"))
    if merged_data.exists():
        files_to_validate.append((merged_data, "merged"))
    
    if not files_to_validate:
        logger.warning("No parquet files found to validate.")
        return
    
    all_valid = True
    validation_reports = []
    
    for file_path, schema_type in files_to_validate:
        logger.info(f"Validating {file_path} against {schema_type} schema")
        report = validate_file_against_schema(file_path, schema_type, schema)
        validation_reports.append(report)
        
        if not report["valid"]:
            all_valid = False
            logger.error(f"Validation failed for {file_path}: {report['errors']}")
        else:
            logger.info(f"Validation passed for {file_path}")
    
    # Save validation report
    qc_dir = get_data_processed_path().parent / "qc" # Or specific validation dir
    qc_dir.mkdir(parents=True, exist_ok=True)
    report_path = qc_dir / "schema_validation_report.json"
    
    import json
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(validation_reports, f, indent=2, default=str)
    
    logger.info(f"Validation report saved to {report_path}")
    
    if not all_valid:
        logger.error("One or more files failed schema validation.")
        sys.exit(1)
    else:
        logger.info("All files passed schema validation.")
        sys.exit(0)

if __name__ == "__main__":
    main()
