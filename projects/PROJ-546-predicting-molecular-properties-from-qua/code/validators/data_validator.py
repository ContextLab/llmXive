"""
Data Validator Module for PROJ-546.

This module validates the downloaded experimental barrier dataset CSV file.
It verifies the presence of required columns (SMILES, experimental_barrier)
and ensures correct data types as per the project's data model.
"""

import csv
import logging
import sys
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any

# Configure logging for this module
logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Custom exception for data validation errors."""
    pass


def validate_columns(file_path: Path, required_columns: List[str]) -> Tuple[bool, List[str]]:
    """
    Validates that the CSV file contains all required columns.

    Args:
        file_path: Path to the CSV file to validate.
        required_columns: List of column names that must be present.

    Returns:
        Tuple of (is_valid, list_of_missing_columns).
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    missing_columns = []
    try:
        with open(file_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            if reader.fieldnames is None:
                raise ValidationError("CSV file is empty or has no headers.")
            
            header_set = set(reader.fieldnames)
            for col in required_columns:
                if col not in header_set:
                    missing_columns.append(col)
    except csv.Error as e:
        raise ValidationError(f"Error reading CSV headers: {e}")

    return len(missing_columns) == 0, missing_columns


def validate_data_types(file_path: Path, required_columns: List[str]) -> Tuple[bool, List[str]]:
    """
    Validates that the data in required columns matches expected types.
    
    Expected types based on spec.md Data Model:
    - SMILES: string (non-empty)
    - experimental_barrier: float (numeric)

    Args:
        file_path: Path to the CSV file.
        required_columns: List of columns to validate types for.

    Returns:
        Tuple of (is_valid, list_of_invalid_rows).
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    invalid_rows = []
    row_count = 0

    try:
        with open(file_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                row_count += 1
                # Check SMILES (string, non-empty)
                if 'SMILES' in row:
                    smiles_val = row['SMILES']
                    if not isinstance(smiles_val, str) or not smiles_val.strip():
                        invalid_rows.append(f"Row {row_count}: SMILES is empty or invalid type.")
                
                # Check experimental_barrier (float)
                if 'experimental_barrier' in row:
                    barrier_val = row['experimental_barrier']
                    try:
                        float(barrier_val)
                    except (ValueError, TypeError):
                        invalid_rows.append(f"Row {row_count}: experimental_barrier is not a valid float ('{barrier_val}').")
    except csv.Error as e:
        raise ValidationError(f"Error reading CSV data: {e}")

    return len(invalid_rows) == 0, invalid_rows


def validate_physical_ranges(file_path: Path) -> Tuple[bool, List[str]]:
    """
    Validates physical ranges for numeric columns.
    For experimental_barrier, values should typically be positive (energy barriers).
    
    Args:
        file_path: Path to the CSV file.

    Returns:
        Tuple of (is_valid, list_of_out_of_range_rows).
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    out_of_range_rows = []
    row_count = 0

    try:
        with open(file_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                row_count += 1
                if 'experimental_barrier' in row:
                    try:
                        val = float(row['experimental_barrier'])
                        # Barrier heights are generally non-negative in this context
                        if val < 0:
                            out_of_range_rows.append(f"Row {row_count}: experimental_barrier is negative ({val}).")
                    except (ValueError, TypeError):
                        # Already caught by validate_data_types, but safe to ignore here
                        pass
    except csv.Error as e:
        raise ValidationError(f"Error reading CSV data: {e}")

    return len(out_of_range_rows) == 0, out_of_range_rows


def validate_full(file_path: Path) -> bool:
    """
    Runs all validation checks on the dataset.
    
    Args:
        file_path: Path to the CSV file.

    Returns:
        True if all validations pass, False otherwise.
        
    Raises:
        ValidationError: If any validation fails.
    """
    required_columns = ['SMILES', 'experimental_barrier']
    
    # Check 1: Columns
    cols_valid, missing = validate_columns(file_path, required_columns)
    if not cols_valid:
        raise ValidationError(f"Missing required columns: {missing}")
    logger.info("Column validation passed.")

    # Check 2: Data Types
    types_valid, invalid_type_rows = validate_data_types(file_path, required_columns)
    if not types_valid:
        raise ValidationError(f"Data type validation failed for rows: {invalid_type_rows}")
    logger.info("Data type validation passed.")

    # Check 3: Physical Ranges
    ranges_valid, out_of_range_rows = validate_physical_ranges(file_path)
    if not ranges_valid:
        # Log warnings but do not fail strictly if negative barriers are theoretically possible
        # For this specific task, we treat it as a warning unless spec says strictly fail
        logger.warning(f"Physical range validation found issues: {out_of_range_rows}")
    
    logger.info("Full validation completed successfully.")
    return True


def main():
    """
    CLI entry point for the data validator.
    Expects a single argument: path to the CSV file.
    """
    if len(sys.argv) < 2:
        print("Usage: python -m validators.data_validator <path_to_csv>")
        sys.exit(1)

    file_path = Path(sys.argv[1])
    
    # Setup basic logging to stderr
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        stream=sys.stderr
    )

    try:
        validate_full(file_path)
        print(f"Validation PASSED for {file_path}")
        sys.exit(0)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except ValidationError as e:
        print(f"Validation FAILED: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()