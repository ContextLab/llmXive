import os
import csv
import json
from pathlib import Path
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field
import logging

from .config import get_data_path, DATA_RAW_PATH, DATA_PROCESSED_PATH
from .logging_config import get_logger, log_warning

logger = get_logger(__name__)

@dataclass
class ValidationResult:
    status: str  # 'valid', 'invalid', 'warning'
    message: str
    file_path: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)

class ValidationStatus:
    VALID = 'valid'
    INVALID = 'invalid'
    WARNING = 'warning'

# Define expected schemas for raw and processed data
# These are simplified schemas based on the project context (proteomic/transcriptomic data)
RAW_SCHEMA_REQUIRED_COLUMNS = {
    'sample_id',
    'species',
    'stress_condition',
}

PROCESSED_SCHEMA_REQUIRED_COLUMNS = {
    'sample_id',
    'species',
    'stress_condition',
    'protein_id',  # or gene_id
}

# Allowed column prefixes for processed data (protein/gene abundance columns)
ALLOWED_COLUMN_PREFIXES = {
    'protein_',
    'gene_',
    'abundance_',
}

def validate_csv_schema(file_path: Path, schema_type: str) -> ValidationResult:
    """
    Validates a CSV file against the expected schema for raw or processed data.
    
    Args:
        file_path: Path to the CSV file
        schema_type: 'raw' or 'processed'
        
    Returns:
        ValidationResult object
    """
    if not file_path.exists():
        return ValidationResult(
            status=ValidationStatus.INVALID,
            message=f"File not found: {file_path}",
            file_path=str(file_path)
        )

    try:
        with open(file_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames
            
            if not headers:
                return ValidationResult(
                    status=ValidationStatus.INVALID,
                    message=f"File {file_path} is empty or has no headers",
                    file_path=str(file_path)
                )
            
            headers_set = set(headers)
            missing_columns = []
            invalid_columns = []
            row_count = 0
            
            # Determine required columns based on schema type
            if schema_type == 'raw':
                required = RAW_SCHEMA_REQUIRED_COLUMNS
            elif schema_type == 'processed':
                required = PROCESSED_SCHEMA_REQUIRED_COLUMNS
                # Check for valid protein/gene columns
                data_columns = [h for h in headers if h not in PROCESSED_SCHEMA_REQUIRED_COLUMNS]
                for col in data_columns:
                    is_valid = any(col.startswith(prefix) for prefix in ALLOWED_COLUMN_PREFIXES)
                    if not is_valid and col != 'sample_id':  # sample_id is allowed as is
                        invalid_columns.append(col)
            else:
                return ValidationResult(
                    status=ValidationStatus.INVALID,
                    message=f"Unknown schema type: {schema_type}",
                    file_path=str(file_path)
                )
            
            # Check for required columns
            missing_columns = list(required - headers_set)
            
            # Count rows
            for _ in reader:
                row_count += 1
                
        if missing_columns:
            return ValidationResult(
                status=ValidationStatus.INVALID,
                message=f"Missing required columns: {', '.join(missing_columns)}",
                file_path=str(file_path),
                details={'missing_columns': missing_columns}
            )
        
        if invalid_columns:
            return ValidationResult(
                status=ValidationStatus.WARNING,
                message=f"Columns with unexpected naming: {', '.join(invalid_columns)}",
                file_path=str(file_path),
                details={'invalid_columns': invalid_columns, 'row_count': row_count}
            )
        
        return ValidationResult(
            status=ValidationStatus.VALID,
            message=f"Schema validation passed",
            file_path=str(file_path),
            details={'columns': list(headers), 'row_count': row_count}
        )
        
    except Exception as e:
        logger.error(f"Error validating CSV schema for {file_path}: {e}")
        return ValidationResult(
            status=ValidationStatus.INVALID,
            message=f"Error reading file: {str(e)}",
            file_path=str(file_path)
        )

def validate_parquet_schema(file_path: Path, schema_type: str) -> ValidationResult:
    """
    Validates a Parquet file against the expected schema.
    Note: This is a simplified check. Full schema validation would require pandas.
    """
    if not file_path.exists():
        return ValidationResult(
            status=ValidationStatus.INVALID,
            message=f"File not found: {file_path}",
            file_path=str(file_path)
        )

    try:
        import pandas as pd
        df = pd.read_parquet(file_path)
        
        headers = set(df.columns)
        missing_columns = []
        
        if schema_type == 'raw':
            required = RAW_SCHEMA_REQUIRED_COLUMNS
        elif schema_type == 'processed':
            required = PROCESSED_SCHEMA_REQUIRED_COLUMNS
        else:
            return ValidationResult(
                status=ValidationStatus.INVALID,
                message=f"Unknown schema type: {schema_type}",
                file_path=str(file_path)
            )
        
        missing_columns = list(required - headers)
        
        if missing_columns:
            return ValidationResult(
                status=ValidationStatus.INVALID,
                message=f"Missing required columns: {', '.join(missing_columns)}",
                file_path=str(file_path),
                details={'missing_columns': missing_columns}
            )
        
        return ValidationResult(
            status=ValidationStatus.VALID,
            message=f"Parquet schema validation passed",
            file_path=str(file_path),
            details={'columns': list(df.columns), 'row_count': len(df)}
        )
        
    except ImportError:
        log_warning("pandas not available for Parquet validation, skipping")
        return ValidationResult(
            status=ValidationStatus.WARNING,
            message="pandas not available for Parquet validation",
            file_path=str(file_path)
        )
    except Exception as e:
        logger.error(f"Error validating Parquet schema for {file_path}: {e}")
        return ValidationResult(
            status=ValidationStatus.INVALID,
            message=f"Error reading Parquet file: {str(e)}",
            file_path=str(file_path)
        )

def validate_directory_schema(directory_path: Path) -> List[ValidationResult]:
    """
    Validates all CSV and Parquet files in a directory against the appropriate schema.
    
    Args:
        directory_path: Path to the directory to validate
        
    Returns:
        List of ValidationResult objects
    """
    results = []
    
    if not directory_path.exists():
        log_warning(f"Directory does not exist: {directory_path}")
        return results
        
    # Determine schema type based on directory name
    dir_name = directory_path.name
    if 'raw' in dir_name.lower():
        schema_type = 'raw'
    elif 'processed' in dir_name.lower():
        schema_type = 'processed'
    else:
        schema_type = 'raw'  # Default to raw for unknown directories
        
    for file_path in directory_path.iterdir():
        if file_path.is_file():
            if file_path.suffix.lower() == '.csv':
                result = validate_csv_schema(file_path, schema_type)
                results.append(result)
            elif file_path.suffix.lower() in ['.parquet', '.pq']:
                result = validate_parquet_schema(file_path, schema_type)
                results.append(result)
                
    return results

def main():
    """
    Main entry point for schema validation.
    Validates both data/raw and data/processed directories.
    """
    data_path = get_data_path()
    raw_dir = data_path / 'raw'
    processed_dir = data_path / 'processed'
    
    logger.info("Starting schema validation for data directories")
    
    # Validate raw directory
    raw_results = validate_directory_schema(raw_dir)
    logger.info(f"Validated {len(raw_results)} files in raw directory")
    
    # Validate processed directory
    processed_results = validate_directory_schema(processed_dir)
    logger.info(f"Validated {len(processed_results)} files in processed directory")
    
    # Summary
    total_valid = sum(1 for r in raw_results + processed_results if r.status == ValidationStatus.VALID)
    total_invalid = sum(1 for r in raw_results + processed_results if r.status == ValidationStatus.INVALID)
    total_warnings = sum(1 for r in raw_results + processed_results if r.status == ValidationStatus.WARNING)
    
    logger.info(f"Schema Validation Summary: {total_valid} valid, {total_invalid} invalid, {total_warnings} warnings")
    
    if total_invalid > 0:
        logger.error(f"Found {total_invalid} files with schema errors")
        for result in raw_results + processed_results:
            if result.status == ValidationStatus.INVALID:
                logger.error(f"  - {result.file_path}: {result.message}")
        return 1
        
    return 0

if __name__ == "__main__":
    exit(main())
