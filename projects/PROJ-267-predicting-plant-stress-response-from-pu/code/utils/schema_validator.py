import os
import csv
import json
from pathlib import Path
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field
import logging

from .logging_config import get_logger, log_warning
from .config import get_data_path, DATA_RAW_PATH, DATA_PROCESSED_PATH

logger = get_logger(__name__)

@dataclass
class ValidationResult:
    """Container for schema validation results."""
    status: str  # 'passed', 'failed', 'warning'
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    files_checked: int = 0
    total_rows: int = 0

class ValidationStatus:
    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"

# Define expected schemas based on project requirements
# These are the minimal required columns/structures for our data pipelines

RAW_SCHEMA_EXPECTATIONS = {
    # Expected columns for raw proteomic data (common across sources)
    "proteomic": {
        "required_columns": ["protein_id", "sample_id"],
        "optional_columns": ["abundance", "detection_rate", "species", "stress_condition"],
        "column_types": {
            "protein_id": str,
            "sample_id": str,
            "abundance": (int, float),
            "detection_rate": (int, float),
            "species": str,
            "stress_condition": str
        }
    },
    # Expected columns for raw transcriptomic data
    "transcriptomic": {
        "required_columns": ["gene_id", "sample_id"],
        "optional_columns": ["expression_value", "species", "stress_condition"],
        "column_types": {
            "gene_id": str,
            "sample_id": str,
            "expression_value": (int, float),
            "species": str,
            "stress_condition": str
        }
    }
}

PROCESSED_SCHEMA_EXPECTATIONS = {
    # Expected columns for merged/processed data
    "merged": {
        "required_columns": ["protein_id", "sample_id", "expression_value"],
        "optional_columns": ["species", "stress_condition", "detection_rate"],
        "column_types": {
            "protein_id": str,
            "sample_id": str,
            "expression_value": (int, float),
            "species": str,
            "stress_condition": str,
            "detection_rate": (int, float)
        },
        "constraints": {
            "expression_value": {"min": None, "max": None}  # No hard limits, but check for NaN
        }
    }
}

def validate_csv_schema(file_path: Path, schema_type: str = "proteomic") -> ValidationResult:
    """
    Validate a CSV file against the expected schema for its type.
    
    Args:
        file_path: Path to the CSV file to validate
        schema_type: Type of schema to validate against ('proteomic', 'transcriptomic', 'merged')
        
    Returns:
        ValidationResult with status, errors, and warnings
    """
    result = ValidationResult(status=ValidationStatus.PASSED)
    result.files_checked = 1
    
    if not file_path.exists():
        result.status = ValidationStatus.FAILED
        result.errors.append(f"File not found: {file_path}")
        return result
    
    try:
        with open(file_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames
            
            if not headers:
                result.status = ValidationStatus.FAILED
                result.errors.append(f"CSV file {file_path} has no headers")
                return result
            
            # Determine which schema to use
            if schema_type in RAW_SCHEMA_EXPECTATIONS:
                schema = RAW_SCHEMA_EXPECTATIONS[schema_type]
            elif schema_type in PROCESSED_SCHEMA_EXPECTATIONS:
                schema = PROCESSED_SCHEMA_EXPECTATIONS[schema_type]
            else:
                # Default to proteomic if unknown
                schema = RAW_SCHEMA_EXPECTATIONS["proteomic"]
                log_warning(f"Unknown schema type '{schema_type}', defaulting to proteomic for {file_path}")
                result.warnings.append(f"Unknown schema type '{schema_type}', using proteomic schema")
            
            # Check required columns
            missing_required = set(schema["required_columns"]) - set(headers)
            if missing_required:
                result.status = ValidationStatus.FAILED
                result.errors.append(f"Missing required columns in {file_path}: {missing_required}")
            
            # Check for unexpected columns (optional warning)
            expected_columns = set(schema["required_columns"]) | set(schema.get("optional_columns", []))
            unexpected_columns = set(headers) - expected_columns
            if unexpected_columns:
                result.warnings.append(f"Unexpected columns in {file_path}: {unexpected_columns}")
            
            # Validate row data types and constraints
            row_count = 0
            for row in reader:
                row_count += 1
                
                # Check column types
                for col_name, expected_type in schema.get("column_types", {}).items():
                    if col_name in row:
                        value = row[col_name]
                        if value is not None and value != '':
                            # Check if value matches expected type
                            try:
                                if expected_type == str:
                                    str(value)
                                elif expected_type == int:
                                    int(value)
                                elif expected_type == float:
                                    float(value)
                                elif isinstance(expected_type, tuple):
                                    # Handle tuple of types (e.g., (int, float))
                                    converted = False
                                    for t in expected_type:
                                        try:
                                            if t == int:
                                                int(value)
                                            elif t == float:
                                                float(value)
                                            converted = True
                                            break
                                        except ValueError:
                                            continue
                                    if not converted:
                                        result.warnings.append(
                                            f"Type mismatch for column '{col_name}' in {file_path}: expected {expected_type}, got {value}"
                                        )
                            except ValueError:
                                result.warnings.append(
                                    f"Invalid value '{value}' for column '{col_name}' in {file_path}, expected {expected_type}"
                                )
                
                # Check constraints (e.g., non-null for certain columns)
                if "constraints" in schema:
                    for col_name, constraint in schema["constraints"].items():
                        if col_name in row:
                            value = row[col_name]
                            if value is None or value == '':
                                if constraint.get("allow_null", False) is False:
                                    result.warnings.append(
                                        f"Null value for constrained column '{col_name}' in {file_path}"
                                    )
            
            result.total_rows = row_count
            
    except Exception as e:
        result.status = ValidationStatus.FAILED
        result.errors.append(f"Error reading CSV file {file_path}: {str(e)}")
    
    return result

def validate_parquet_schema(file_path: Path, schema_type: str = "merged") -> ValidationResult:
    """
    Validate a Parquet file against the expected schema.
    
    Args:
        file_path: Path to the Parquet file to validate
        schema_type: Type of schema to validate against
        
    Returns:
        ValidationResult with status, errors, and warnings
    """
    result = ValidationResult(status=ValidationStatus.PASSED)
    result.files_checked = 1
    
    if not file_path.exists():
        result.status = ValidationStatus.FAILED
        result.errors.append(f"File not found: {file_path}")
        return result
    
    try:
        import pandas as pd
        df = pd.read_parquet(file_path)
        
        headers = list(df.columns)
        
        # Determine which schema to use
        if schema_type in PROCESSED_SCHEMA_EXPECTATIONS:
            schema = PROCESSED_SCHEMA_EXPECTATIONS[schema_type]
        elif schema_type in RAW_SCHEMA_EXPECTATIONS:
            schema = RAW_SCHEMA_EXPECTATIONS[schema_type]
        else:
            schema = PROCESSED_SCHEMA_EXPECTATIONS["merged"]
            log_warning(f"Unknown schema type '{schema_type}', defaulting to merged for {file_path}")
            result.warnings.append(f"Unknown schema type '{schema_type}', using merged schema")
        
        # Check required columns
        missing_required = set(schema["required_columns"]) - set(headers)
        if missing_required:
            result.status = ValidationStatus.FAILED
            result.errors.append(f"Missing required columns in {file_path}: {missing_required}")
        
        # Check for unexpected columns
        expected_columns = set(schema["required_columns"]) | set(schema.get("optional_columns", []))
        unexpected_columns = set(headers) - expected_columns
        if unexpected_columns:
            result.warnings.append(f"Unexpected columns in {file_path}: {unexpected_columns}")
        
        # Check data types
        for col_name, expected_type in schema.get("column_types", {}).items():
            if col_name in df.columns:
                actual_dtype = df[col_name].dtype
                # Simple type checking
                if expected_type == str:
                    if not pd.api.types.is_string_dtype(actual_dtype):
                        result.warnings.append(
                            f"Column '{col_name}' in {file_path} has dtype {actual_dtype}, expected string"
                        )
                elif expected_type == int:
                    if not pd.api.types.is_integer_dtype(actual_dtype):
                        result.warnings.append(
                            f"Column '{col_name}' in {file_path} has dtype {actual_dtype}, expected integer"
                        )
                elif expected_type == float:
                    if not pd.api.types.is_float_dtype(actual_dtype):
                        result.warnings.append(
                            f"Column '{col_name}' in {file_path} has dtype {actual_dtype}, expected float"
                        )
                elif isinstance(expected_type, tuple):
                    # For (int, float), check if it's numeric
                    if not pd.api.types.is_numeric_dtype(actual_dtype):
                        result.warnings.append(
                            f"Column '{col_name}' in {file_path} has dtype {actual_dtype}, expected numeric"
                        )
        
        # Check for null values in constrained columns
        if "constraints" in schema:
            for col_name, constraint in schema["constraints"].items():
                if col_name in df.columns:
                    null_count = df[col_name].isnull().sum()
                    if null_count > 0 and constraint.get("allow_null", False) is False:
                        result.warnings.append(
                            f"Column '{col_name}' in {file_path} has {null_count} null values"
                        )
        
        result.total_rows = len(df)
        
    except Exception as e:
        result.status = ValidationStatus.FAILED
        result.errors.append(f"Error reading Parquet file {file_path}: {str(e)}")
    
    return result

def validate_directory_schema(directory_path: Path, schema_type: str = "proteomic") -> ValidationResult:
    """
    Validate all CSV and Parquet files in a directory against the expected schema.
    
    Args:
        directory_path: Path to the directory containing data files
        schema_type: Type of schema to validate against
        
    Returns:
        ValidationResult with aggregated results
    """
    result = ValidationResult(status=ValidationStatus.PASSED)
    
    if not directory_path.exists():
        result.status = ValidationStatus.FAILED
        result.errors.append(f"Directory not found: {directory_path}")
        return result
    
    if not directory_path.is_dir():
        result.status = ValidationStatus.FAILED
        result.errors.append(f"Path is not a directory: {directory_path}")
        return result
    
    # Find all CSV and Parquet files
    csv_files = list(directory_path.glob("*.csv"))
    parquet_files = list(directory_path.glob("*.parquet"))
    all_files = csv_files + parquet_files
    
    if not all_files:
        result.warnings.append(f"No CSV or Parquet files found in {directory_path}")
        return result
    
    # Validate each file
    for file_path in all_files:
        if file_path.suffix == '.csv':
            file_result = validate_csv_schema(file_path, schema_type)
        elif file_path.suffix == '.parquet':
            file_result = validate_parquet_schema(file_path, schema_type)
        else:
            continue
        
        # Aggregate results
        result.files_checked += file_result.files_checked
        result.total_rows += file_result.total_rows
        
        if file_result.status == ValidationStatus.FAILED:
            result.status = ValidationStatus.FAILED
            result.errors.extend(file_result.errors)
        elif file_result.status == ValidationStatus.WARNING:
            if result.status == ValidationStatus.PASSED:
                result.status = ValidationStatus.WARNING
            result.warnings.extend(file_result.warnings)
    
    return result

def main():
    """Main entry point for schema validation CLI."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Validate data schemas for raw and processed directories")
    parser.add_argument(
        "--directory",
        type=str,
        default=None,
        help="Directory to validate (default: DATA_RAW_PATH or DATA_PROCESSED_PATH)"
    )
    parser.add_argument(
        "--schema-type",
        type=str,
        default="proteomic",
        choices=["proteomic", "transcriptomic", "merged"],
        help="Schema type to validate against"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Output file for validation report (JSON)"
    )
    
    args = parser.parse_args()
    
    # Determine directory to validate
    if args.directory:
        directory_path = Path(args.directory)
    else:
        # Default to raw data directory
        directory_path = Path(DATA_RAW_PATH)
    
    logger.info(f"Validating schema for directory: {directory_path}")
    logger.info(f"Using schema type: {args.schema_type}")
    
    result = validate_directory_schema(directory_path, args.schema_type)
    
    # Log results
    if result.status == ValidationStatus.PASSED:
        logger.info(f"Schema validation PASSED for {result.files_checked} files, {result.total_rows} total rows")
    elif result.status == ValidationStatus.WARNING:
        logger.warning(f"Schema validation PASSED with WARNINGS for {result.files_checked} files")
        for warning in result.warnings:
            logger.warning(f"  - {warning}")
    else:
        logger.error(f"Schema validation FAILED for {result.files_checked} files")
        for error in result.errors:
            logger.error(f"  - {error}")
    
    # Save report if requested
    if args.output:
        report = {
            "status": result.status,
            "files_checked": result.files_checked,
            "total_rows": result.total_rows,
            "errors": result.errors,
            "warnings": result.warnings
        }
        with open(args.output, 'w') as f:
            json.dump(report, f, indent=2)
        logger.info(f"Validation report saved to {args.output}")
    
    # Exit with appropriate code
    if result.status == ValidationStatus.FAILED:
        return 1
    return 0

if __name__ == "__main__":
    exit(main())
