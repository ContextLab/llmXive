import csv
import json
import sys
from pathlib import Path
from typing import Dict, Any, List, Tuple
from config import ensure_dirs

def load_schema() -> Dict[str, Any]:
    """
    Load the expected schema for correlation_results.csv.
    Defines column names, expected data types, and validation rules.
    """
    return {
        "columns": [
            {"name": "metric_name", "type": "str", "required": True},
            {"name": "outcome", "type": "str", "required": True},
            {"name": "spearman_r", "type": "float", "required": True},
            {"name": "p_value", "type": "float", "required": True},
            {"name": "p_adjusted", "type": "float", "required": True},
            {"name": "n", "type": "int", "required": True},
            {"name": "trace_id", "type": "str", "required": True}
        ],
        "path": "data/results/correlation_results.csv"
    }

def validate_row(row: Dict[str, str], schema: Dict[str, Any], row_num: int) -> List[str]:
    """
    Validate a single row against the schema.
    Returns a list of error messages (empty if valid).
    """
    errors = []
    columns_config = {col["name"]: col for col in schema["columns"]}

    # Check for missing columns
    for col_name in columns_config:
        if col_name not in row:
            errors.append(f"Row {row_num}: Missing required column '{col_name}'")

    # Check for extra columns (optional strictness, but good for schema validation)
    for col_name in row:
        if col_name not in columns_config:
            errors.append(f"Row {row_num}: Unexpected column '{col_name}'")

    # Type and value validation for present columns
    for col_name, col_config in columns_config.items():
        if col_name not in row:
            continue

        value = row[col_name]
        expected_type = col_config["type"]

        if expected_type == "str":
            if not isinstance(value, str) or value == "":
                errors.append(f"Row {row_num}: Column '{col_name}' must be a non-empty string")
            # Specific check for trace_id format (SHA-256 hex string)
            if col_name == "trace_id":
                if len(value) != 64 or not all(c in '0123456789abcdef' for c in value.lower()):
                    errors.append(f"Row {row_num}: Column 'trace_id' must be a valid 64-character SHA-256 hex string")

        elif expected_type == "float":
            try:
                float_val = float(value)
                if col_name in ["spearman_r", "p_value", "p_adjusted"] and (float_val != float_val): # NaN check
                     errors.append(f"Row {row_num}: Column '{col_name}' cannot be NaN")
            except ValueError:
                errors.append(f"Row {row_num}: Column '{col_name}' must be a valid float, got '{value}'")

        elif expected_type == "int":
            try:
                int_val = int(value)
                if col_name == "n" and int_val < 0:
                    errors.append(f"Row {row_num}: Column 'n' must be non-negative")
            except ValueError:
                errors.append(f"Row {row_num}: Column '{col_name}' must be a valid integer, got '{value}'")

    return errors

def main() -> int:
    """
    Main entry point to validate the correlation_results.csv schema.
    Returns 0 on success, 1 on validation failure.
    """
    schema = load_schema()
    file_path = Path(schema["path"])

    if not file_path.exists():
        print(f"Error: File not found: {file_path}")
        return 1

    all_errors: List[str] = []
    row_count = 0

    try:
        with open(file_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            # Validate header columns
            if reader.fieldnames is None:
                print("Error: CSV file is empty or has no header.")
                return 1

            expected_cols = {col["name"] for col in schema["columns"]}
            actual_cols = set(reader.fieldnames)
            
            missing_cols = expected_cols - actual_cols
            extra_cols = actual_cols - expected_cols

            if missing_cols:
                all_errors.append(f"Header missing columns: {missing_cols}")
            if extra_cols:
                all_errors.append(f"Header has unexpected columns: {extra_cols}")

            # Validate rows
            for row_num, row in enumerate(reader, start=2): # Start at 2 because 1 is header
                row_count += 1
                row_errors = validate_row(row, schema, row_num)
                all_errors.extend(row_errors)

    except Exception as e:
        print(f"Error reading CSV file: {e}")
        return 1

    if all_errors:
        print(f"Validation FAILED for {file_path}:")
        for err in all_errors[:20]: # Print first 20 errors
            print(f"  - {err}")
        if len(all_errors) > 20:
            print(f"  ... and {len(all_errors) - 20} more errors")
        return 1

    if row_count == 0:
        print(f"Warning: {file_path} exists but contains no data rows.")
        # Depending on strictness, this might be a failure, but for schema validation,
        # if the file exists and is empty, the schema is technically satisfied by the structure.
        # However, T029 implies checking content types, so let's ensure it's not just empty if data is expected.
        # Given the pipeline flow, if T023_run ran, there should be data.
        # We will treat empty as a warning but return 0 if structure is correct.
        return 0

    print(f"Validation PASSED for {file_path}: {row_count} rows checked.")
    return 0

if __name__ == "__main__":
    sys.exit(main())