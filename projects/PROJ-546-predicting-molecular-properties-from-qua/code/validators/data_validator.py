"""
T010: Validate downloaded CSV contains required columns and correct data types.
Implements FR-001: Data Schema Validation.
"""
import csv
import logging
import sys
from pathlib import Path
from typing import List, Set, Tuple

logger = logging.getLogger(__name__)

REQUIRED_COLUMNS = {'SMILES', 'experimental_barrier'}
NUMERIC_COLUMNS = {'experimental_barrier'}

def validate_csv_schema(file_path: Path) -> Tuple[bool, str]:
    """
    Verify that the CSV file exists, is non-empty, and contains the required columns.
    Also checks that numeric columns are indeed numeric.
    
    Returns:
        Tuple of (success: bool, message: str)
    """
    if not file_path.exists():
        return False, f"File not found: {file_path}"

    try:
        with open(file_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            headers = set(reader.fieldnames) if reader.fieldnames else set()

            # Check required columns
            missing = REQUIRED_COLUMNS - headers
            if missing:
                return False, f"Missing required columns: {missing}"

            # Validate data types for first 100 rows
            row_count = 0
            validation_errors = []
            
            for row in reader:
                row_count += 1
                for col in NUMERIC_COLUMNS:
                    val = row.get(col)
                    if val is None or val.strip() == '':
                        validation_errors.append(f"Row {row_count}: Empty value in numeric column {col}")
                    else:
                        try:
                            float(val)
                        except ValueError:
                            validation_errors.append(f"Row {row_count}: Non-numeric value in {col}: {row.get(col)}")
                
                # Stop after checking first 100 rows for performance
                if row_count >= 100:
                    break

            if row_count == 0:
                return False, "File is empty (no data rows)"

            if validation_errors:
                return False, "Data validation errors:\n" + "\n".join(validation_errors[:5])

            return True, f"Schema validation passed for {file_path} ({row_count} rows checked)"

    except Exception as e:
        return False, f"Error reading file {file_path}: {e}"

def main():
    """
    CLI entry point for T010.
    Usage: python code/validators/data_validator.py <file_path>
    """
    if len(sys.argv) < 2:
        print("Usage: python code/validators/data_validator.py <file_path>")
        sys.exit(1)
    
    path = Path(sys.argv[1])
    success, message = validate_csv_schema(path)
    
    if success:
        print(f"PASSED: {message}")
        sys.exit(0)
    else:
        print(f"FAILED: {message}")
        sys.exit(1)

if __name__ == "__main__":
    main()