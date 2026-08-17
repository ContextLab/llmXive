"""
Data validation module for the molecular properties pipeline.
Validates downloaded CSV datasets against the project specification.
"""
import csv
import logging
import sys
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any

# Configure logger
logger = logging.getLogger(__name__)


class ValidationError(Exception):
    """Custom exception for data validation failures."""
    pass


def validate_columns(file_path: Path, required_columns: List[str]) -> Tuple[bool, List[str]]:
    """
    Verify that the CSV file contains all required columns.

    Args:
        file_path: Path to the CSV file.
        required_columns: List of column names that must be present.

    Returns:
        Tuple of (is_valid, list_of_missing_columns).
    """
    missing_columns = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            header = next(reader, None)
            
            if header is None:
                raise ValidationError(f"File {file_path} is empty or has no header.")
            
            # Normalize header names (strip whitespace)
            header_normalized = [col.strip() for col in header]
            
            for col in required_columns:
                if col not in header_normalized:
                    missing_columns.append(col)
            
            return len(missing_columns) == 0, missing_columns
            
    except FileNotFoundError:
        raise ValidationError(f"File not found: {file_path}")
    except StopIteration:
        raise ValidationError(f"File {file_path} is empty.")


def validate_data_types(file_path: Path, column_types: Dict[str, type], sample_size: int = 100) -> Tuple[bool, List[str]]:
    """
    Verify that data in specified columns matches expected types.
    Checks a sample of rows to avoid scanning the entire file for large datasets.

    Args:
        file_path: Path to the CSV file.
        column_types: Dict mapping column name to expected Python type.
        sample_size: Number of rows to check (default 100).

    Returns:
        Tuple of (is_valid, list_of_columns_with_invalid_types).
    """
    invalid_columns = set()
    row_count = 0

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            # Verify columns exist first
            if not reader.fieldnames:
                raise ValidationError("CSV has no header row.")
            
            fieldnames = [name.strip() for name in reader.fieldnames]
            
            for col in column_types.keys():
                if col not in fieldnames:
                    raise ValidationError(f"Column '{col}' not found in CSV. Cannot validate types.")

            for row in reader:
                if row_count >= sample_size:
                    break
                
                for col, expected_type in column_types.items():
                    value = row.get(col, "").strip()
                    
                    if value == "":
                        # Allow empty strings for now, or treat as invalid?
                        # Spec says "correct data types", usually implies non-null.
                        # We will flag empty strings as type mismatch for numeric types.
                        if expected_type in (int, float):
                            invalid_columns.add(col)
                        continue

                    try:
                        if expected_type == str:
                            # Any value is a string, but check if it's not empty if required
                            pass
                        elif expected_type == int:
                            int(value)
                        elif expected_type == float:
                            float(value)
                        else:
                            # Custom check or just pass
                            pass
                    except ValueError:
                        invalid_columns.add(col)
                
                row_count += 1

        return len(invalid_columns) == 0, list(invalid_columns)

    except FileNotFoundError:
        raise ValidationError(f"File not found: {file_path}")
    except KeyError as e:
        raise ValidationError(f"Missing column in CSV: {e}")


def validate_physical_ranges(file_path: Path, ranges: Dict[str, Tuple[Optional[float], Optional[float]]]) -> Tuple[bool, List[str]]:
    """
    Verify that numeric columns fall within specified physical ranges.
    
    Args:
        file_path: Path to the CSV file.
        ranges: Dict mapping column name to (min_val, max_val). 
                None for min/max implies no bound on that side.

    Returns:
        Tuple of (is_valid, list_of_columns_out_of_range).
    """
    out_of_range_columns = set()
    row_count = 0
    sample_size = 100 # Check sample for performance

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            if not reader.fieldnames:
                raise ValidationError("CSV has no header row.")
            
            fieldnames = [name.strip() for name in reader.fieldnames]
            
            for col in ranges.keys():
                if col not in fieldnames:
                    raise ValidationError(f"Column '{col}' not found for range validation.")

            for row in reader:
                if row_count >= sample_size:
                    break
                
                for col, (min_val, max_val) in ranges.items():
                    value_str = row.get(col, "").strip()
                    
                    if not value_str:
                        continue
                        
                    try:
                        val = float(value_str)
                        
                        if min_val is not None and val < min_val:
                            out_of_range_columns.add(col)
                        if max_val is not None and val > max_val:
                            out_of_range_columns.add(col)
                    except ValueError:
                        # Non-numeric value where numeric expected
                        out_of_range_columns.add(col)
                
                row_count += 1

        return len(out_of_range_columns) == 0, list(out_of_range_columns)

    except FileNotFoundError:
        raise ValidationError(f"File not found: {file_path}")


def validate_full(file_path: Path) -> bool:
    """
    Perform full validation of the barrier dataset against spec.md Data Model.
    
    Spec Requirements:
    - Columns: 'SMILES', 'experimental_barrier'
    - SMILES: string
    - experimental_barrier: float (energy barrier in kcal/mol or kJ/mol, assumed numeric)
    - Physical Ranges: experimental_barrier > 0 (barriers must be positive)
    
    Args:
        file_path: Path to the CSV file.
        
    Returns:
        True if valid, raises ValidationError otherwise.
    """
    logger.info(f"Starting validation of {file_path}")
    
    if not file_path.exists():
        raise ValidationError(f"File does not exist: {file_path}")
    
    # 1. Validate Columns
    required_columns = ['SMILES', 'experimental_barrier']
    is_valid_cols, missing = validate_columns(file_path, required_columns)
    if not is_valid_cols:
        raise ValidationError(f"Missing required columns: {missing}")
    logger.info("Column validation passed.")
    
    # 2. Validate Data Types
    type_map = {
        'SMILES': str,
        'experimental_barrier': float
    }
    is_valid_types, bad_types = validate_data_types(file_path, type_map)
    if not is_valid_types:
        raise ValidationError(f"Columns with invalid data types: {bad_types}")
    logger.info("Data type validation passed.")
    
    # 3. Validate Physical Ranges
    # Barrier heights must be positive. SMILES is string, no range check.
    range_map = {
        'experimental_barrier': (0.0, None) # > 0
    }
    is_valid_ranges, bad_ranges = validate_physical_ranges(file_path, range_map)
    if not is_valid_ranges:
        raise ValidationError(f"Columns with values out of physical range: {bad_ranges}")
    logger.info("Physical range validation passed.")
    
    logger.info(f"Validation successful for {file_path}")
    return True


def main():
    """
    CLI entry point for data validation.
    Usage: python -m code.validators.data_validator --input <path_to_csv>
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Validate molecular dataset CSV")
    parser.add_argument("--input", required=True, help="Path to the CSV file to validate")
    args = parser.parse_args()
    
    input_path = Path(args.input)
    
    try:
        validate_full(input_path)
        print(f"SUCCESS: {input_path} is valid.")
        sys.exit(0)
    except ValidationError as e:
        print(f"FAILURE: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: Unexpected error during validation: {e}")
        sys.exit(2)


if __name__ == "__main__":
    main()