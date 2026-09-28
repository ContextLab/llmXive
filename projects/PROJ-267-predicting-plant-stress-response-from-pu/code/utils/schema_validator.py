"""
Schema validation for data/raw and data/processed directories.
Implements validation for CSV and Parquet files using Pydantic-like dict checks.
"""
import os
import csv
import json
from pathlib import Path
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field
from enum import Enum

import pandas as pd

from .config import DATA_RAW_PATH, DATA_PROCESSED_PATH
from .logging_config import get_logger, log_warning

logger = get_logger(__name__)


class ValidationStatus(Enum):
    """Validation status enum."""
    SUCCESS = "success"
    WARNING = "warning"
    FAILED = "failed"


@dataclass
class ValidationResult:
    """Result of a schema validation run."""
    status: ValidationStatus
    file_path: str
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    details: Dict[str, Any] = field(default_factory=dict)

def validate_csv_schema(file_path: Path, required_columns: Optional[List[str]] = None) -> ValidationResult:
    """
    Validate CSV file schema.

    Args:
        file_path: Path to the CSV file
        required_columns: Optional list of required column names

    Returns:
        ValidationResult with status and any errors/warnings
    """
    errors = []
    warnings = []
    details = {}

    try:
        # Check file exists and is readable
        if not file_path.exists():
            errors.append(f"File does not exist: {file_path}")
            return ValidationResult(
                status=ValidationStatus.FAILED,
                file_path=str(file_path),
                errors=errors
            )

        # Read header to get columns
        with open(file_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            try:
                header = next(reader)
            except StopIteration:
                errors.append(f"Empty CSV file: {file_path}")
                return ValidationResult(
                    status=ValidationStatus.FAILED,
                    file_path=str(file_path),
                    errors=errors
                )

        columns = [col.strip() for col in header]
        details['columns'] = columns
        details['column_count'] = len(columns)

        # Check for required columns
        if required_columns:
            missing = set(required_columns) - set(columns)
            if missing:
                errors.append(f"Missing required columns: {missing}")

        # Check for duplicate columns
        seen = set()
        duplicates = set()
        for col in columns:
            if col in seen:
                duplicates.add(col)
            seen.add(col)
        if duplicates:
            warnings.append(f"Duplicate columns found: {duplicates}")

        # Check row count
        try:
            df = pd.read_csv(file_path, nrows=1000)
            details['sample_row_count'] = len(df)
            if len(df) == 0:
                warnings.append("File appears to have no data rows")
        except Exception as e:
            warnings.append(f"Could not read sample rows: {str(e)}")

        # Check for empty column names
        empty_cols = [c for c in columns if not c or c.strip() == '']
        if empty_cols:
            errors.append(f"Empty column names found: {len(empty_cols)}")

        # Determine status
        if errors:
            status = ValidationStatus.FAILED
        elif warnings:
            status = ValidationStatus.WARNING
        else:
            status = ValidationStatus.SUCCESS

        return ValidationResult(
            status=status,
            file_path=str(file_path),
            errors=errors,
            warnings=warnings,
            details=details
        )

    except Exception as e:
        logger.error(f"Error validating CSV {file_path}: {str(e)}")
        return ValidationResult(
            status=ValidationStatus.FAILED,
            file_path=str(file_path),
            errors=[f"Validation error: {str(e)}"]
        )


def validate_parquet_schema(file_path: Path, required_columns: Optional[List[str]] = None) -> ValidationResult:
    """
    Validate Parquet file schema.

    Args:
        file_path: Path to the Parquet file
        required_columns: Optional list of required column names

    Returns:
        ValidationResult with status and any errors/warnings
    """
    errors = []
    warnings = []
    details = {}

    try:
        # Check file exists
        if not file_path.exists():
            errors.append(f"File does not exist: {file_path}")
            return ValidationResult(
                status=ValidationStatus.FAILED,
                file_path=str(file_path),
                errors=errors
            )

        # Try to read schema
        try:
            df = pd.read_parquet(file_path, nrows=1000)
        except Exception as e:
            errors.append(f"Could not read Parquet file: {str(e)}")
            return ValidationResult(
                status=ValidationStatus.FAILED,
                file_path=str(file_path),
                errors=errors
            )

        columns = list(df.columns)
        details['columns'] = columns
        details['column_count'] = len(columns)
        details['dtype_summary'] = {col: str(dtype) for col, dtype in df.dtypes.items()}

        # Check for required columns
        if required_columns:
            missing = set(required_columns) - set(columns)
            if missing:
                errors.append(f"Missing required columns: {missing}")

        # Check row count
        details['sample_row_count'] = len(df)
        if len(df) == 0:
            warnings.append("File appears to have no data rows")

        # Check for empty column names
        empty_cols = [c for c in columns if not c or str(c).strip() == '']
        if empty_cols:
            errors.append(f"Empty column names found: {len(empty_cols)}")

        # Check for duplicate columns
        seen = set()
        duplicates = set()
        for col in columns:
            if col in seen:
                duplicates.add(col)
            seen.add(col)
        if duplicates:
            warnings.append(f"Duplicate columns found: {duplicates}")

        # Determine status
        if errors:
            status = ValidationStatus.FAILED
        elif warnings:
            status = ValidationStatus.WARNING
        else:
            status = ValidationStatus.SUCCESS

        return ValidationResult(
            status=status,
            file_path=str(file_path),
            errors=errors,
            warnings=warnings,
            details=details
        )

    except Exception as e:
        logger.error(f"Error validating Parquet {file_path}: {str(e)}")
        return ValidationResult(
            status=ValidationStatus.FAILED,
            file_path=str(file_path),
            errors=[f"Validation error: {str(e)}"]
        )


def validate_directory_schema(
    directory: Path,
    file_extensions: List[str],
    required_columns: Optional[Dict[str, List[str]]] = None,
    recursive: bool = False
) -> List[ValidationResult]:
    """
    Validate all files in a directory.

    Args:
        directory: Path to directory to validate
        file_extensions: List of file extensions to validate (e.g., ['.csv', '.parquet'])
        required_columns: Dict mapping filename patterns to required columns
        recursive: Whether to search subdirectories

    Returns:
        List of ValidationResult objects
    """
    results = []

    if not directory.exists():
        log_warning(f"Directory does not exist: {directory}")
        return results

    # Find all matching files
    pattern = '**/*' if recursive else '*'
    files = []
    for ext in file_extensions:
        files.extend(directory.glob(f"{pattern}{ext}"))

    # Remove duplicates
    files = list(set(files))

    for file_path in sorted(files):
        # Determine required columns for this file
        file_required_cols = None
        if required_columns:
            filename = file_path.name
            for pattern_str, cols in required_columns.items():
                if pattern_str in filename:
                    file_required_cols = cols
                    break

        # Validate based on extension
        if file_path.suffix.lower() == '.csv':
            result = validate_csv_schema(file_path, file_required_cols)
        elif file_path.suffix.lower() in ['.parquet', '.pq']:
            result = validate_parquet_schema(file_path, file_required_cols)
        else:
            continue

        results.append(result)

    return results


def main():
    """Main entry point for schema validation."""
    logger.info("Starting schema validation for data directories")

    # Define required columns for common files
    required_columns = {
        'processed': ['protein_id', 'sample_id', 'stress_condition', 'species'],
        'raw': None  # Raw files may have varying schemas
    }

    # Validate data/raw directory
    logger.info(f"Validating {DATA_RAW_PATH}")
    raw_results = validate_directory_schema(
        DATA_RAW_PATH,
        file_extensions=['.csv', '.parquet'],
        recursive=True
    )

    # Validate data/processed directory
    logger.info(f"Validating {DATA_PROCESSED_PATH}")
    processed_results = validate_directory_schema(
        DATA_PROCESSED_PATH,
        file_extensions=['.csv', '.parquet'],
        required_columns=required_columns.get('processed'),
        recursive=True
    )

    # Summarize results
    total_files = len(raw_results) + len(processed_results)
    failed = sum(1 for r in (raw_results + processed_results) if r.status == ValidationStatus.FAILED)
    warnings = sum(1 for r in (raw_results + processed_results) if r.status == ValidationStatus.WARNING)

    logger.info(f"Validation complete: {total_files} files checked, {failed} failed, {warnings} warnings")

    # Print detailed results
    for result in raw_results + processed_results:
        status_str = result.status.value.upper()
        logger.info(f"[{status_str}] {result.file_path}")
        if result.errors:
            for err in result.errors:
                logger.error(f"  Error: {err}")
        if result.warnings:
            for warn in result.warnings:
                log_warning(f"  Warning: {warn}")

    # Exit with error code if any failures
    if failed > 0:
        logger.error(f"Schema validation failed with {failed} errors")
        return 1

    logger.info("All schema validations passed")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())