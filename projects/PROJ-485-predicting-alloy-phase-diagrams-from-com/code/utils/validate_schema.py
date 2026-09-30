"""
Schema validation utility for processed descriptor data.
Validates that the output file matches the expected schema defined in FR-001.
"""
import os
import sys
import csv
import argparse
from typing import List, Set

# Required columns as per FR-001 and task descriptions
REQUIRED_COLUMNS: Set[str] = {
    "system_id",
    "element_a",
    "element_b",
    "composition",
    "temperature",
    "mean_atomic_radius",
    "electronegativity_variance",
    "valence_electron_count",
    "hume_rothery_concentration",
    "checksum"
}

def validate_schema(file_path: str) -> bool:
    """
    Validates that the CSV file at file_path contains all required columns.
    
    Args:
        file_path: Path to the CSV file to validate.
        
    Returns:
        True if schema is valid, False otherwise.
        
    Raises:
        FileNotFoundError: If the file does not exist.
    """
    if not os.path.exists(file_path):
        print(f"ERROR: File not found: {file_path}")
        return False

    try:
        with open(file_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            if reader.fieldnames is None:
                print("ERROR: File is empty or has no header.")
                return False
            
            actual_columns = set(reader.fieldnames)
            missing_columns = REQUIRED_COLUMNS - actual_columns
            extra_columns = actual_columns - REQUIRED_COLUMNS

            if missing_columns:
                print(f"ERROR: Missing required columns: {missing_columns}")
                return False

            if extra_columns:
                # Log warning but do not fail for extra columns
                print(f"WARNING: Extra columns found (allowed): {extra_columns}")

            # Validate a few rows to ensure data types are roughly correct
            row_count = 0
            for row in reader:
                row_count += 1
                # Check numeric columns
                try:
                    float(row['temperature'])
                    float(row['composition'])
                    float(row['mean_atomic_radius'])
                    float(row['electronegativity_variance'])
                    float(row['valence_electron_count'])
                    float(row['hume_rothery_concentration'])
                except ValueError as e:
                    print(f"ERROR: Invalid numeric data in row {row_count}: {e}")
                    return False
                
                if row_count > 5: # Check first 5 rows for performance
                    break
            
            if row_count == 0:
                print("WARNING: File has no data rows.")
            
            print(f"SUCCESS: Schema validation passed for {file_path} ({row_count} rows checked).")
            return True

    except Exception as e:
        print(f"ERROR: Failed to read file: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description="Validate schema of processed descriptor data.")
    parser.add_argument("file_path", help="Path to the CSV file to validate.")
    args = parser.parse_args()

    if validate_schema(args.file_path):
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
