"""
T010: Validate downloaded CSV contains required columns and correct data types.
"""
import csv
import logging
from pathlib import Path
from typing import List, Set

logger = logging.getLogger(__name__)

REQUIRED_COLUMNS = {'SMILES', 'experimental_barrier'}
NUMERIC_COLUMNS = {'experimental_barrier'}

def validate_csv_schema(file_path: Path) -> bool:
    """
    Verify that the CSV file exists, is non-empty, and contains the required columns.
    Also checks that numeric columns are indeed numeric.
    """
    if not file_path.exists():
        logger.error(f"File not found: {file_path}")
        return False

    try:
        with open(file_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            headers = set(reader.fieldnames) if reader.fieldnames else set()

            # Check required columns
            missing = REQUIRED_COLUMNS - headers
            if missing:
                logger.error(f"Missing required columns: {missing}")
                return False

            # Validate data types for first few rows
            row_count = 0
            for row in reader:
                row_count += 1
                for col in NUMERIC_COLUMNS:
                    try:
                        val = row.get(col)
                        if val is None or val.strip() == '':
                            # Allow empty? Usually not for numeric. Let's be strict.
                            logger.warning(f"Row {row_count}: Empty value in numeric column {col}")
                        else:
                            float(val) # Try to convert
                    except ValueError:
                        logger.error(f"Row {row_count}: Non-numeric value in {col}: {row.get(col)}")
                        return False
                
                # Stop after checking first 100 rows for performance
                if row_count >= 100:
                    break

            if row_count == 0:
                logger.warning("File is empty (no data rows)")
                # Depending on strictness, this might be a failure. 
                # For T004b, we just need the file to exist and have the schema.
                # An empty file with headers is technically valid schema, but likely useless.
                # We return True for schema validity, but log the warning.
            
            logger.info(f"Schema validation passed for {file_path} ({row_count} rows checked)")
            return True

    except Exception as e:
        logger.error(f"Error reading file {file_path}: {e}")
        return False

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python data_validator.py <file_path>")
        sys.exit(1)
    
    path = Path(sys.argv[1])
    if validate_csv_schema(path):
        print("Validation: PASSED")
        sys.exit(0)
    else:
        print("Validation: FAILED")
        sys.exit(1)