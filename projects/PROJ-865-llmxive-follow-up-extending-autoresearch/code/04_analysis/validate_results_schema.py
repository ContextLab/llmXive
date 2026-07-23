import csv
import json
import sys
import yaml
from pathlib import Path
from typing import List, Dict, Any, Set, Optional

def load_schema(schema_path: Path) -> Dict[str, Any]:
    """Load a YAML schema definition."""
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    with open(schema_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def validate_csv_schema(csv_path: Path, schema_path: Path) -> bool:
    """
    Validates that a CSV file's columns match the keys defined in a YAML schema.
    
    The schema is expected to have a 'properties' key containing the allowed columns.
    This function ensures:
    1. The CSV exists.
    2. The schema exists.
    3. The CSV header columns exactly match the keys in schema['properties'].
    
    Raises:
        ValueError: If the schema does not match the CSV columns.
        FileNotFoundError: If files are missing.
    """
    if not csv_path.exists():
        raise FileNotFoundError(f"Results CSV file not found: {csv_path}")
    
    schema = load_schema(schema_path)
    
    if 'properties' not in schema:
        raise ValueError(f"Invalid schema format: missing 'properties' key in {schema_path}")
    
    expected_columns = set(schema['properties'].keys())
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        try:
            header_row = next(reader)
        except StopIteration:
            raise ValueError(f"CSV file {csv_path} is empty (no header found).")
    
    actual_columns = set(header_row)
    
    if expected_columns != actual_columns:
        missing_in_csv = expected_columns - actual_columns
        extra_in_csv = actual_columns - expected_columns
        
        error_msg = "Schema validation failed for CSV columns.\n"
        if missing_in_csv:
            error_msg += f"  Missing columns in CSV: {sorted(missing_in_csv)}\n"
        if extra_in_csv:
            error_msg += f"  Extra columns in CSV: {sorted(extra_in_csv)}\n"
        error_msg += f"  Expected: {sorted(expected_columns)}\n"
        error_msg += f"  Found:    {sorted(actual_columns)}"
        
        raise ValueError(error_msg)
    
    return True

def main():
    """
    Entry point for validating data/derived/results.csv against 
    specs/001-llmxive-followup/contracts/pivot_attempt.schema.yaml.
    """
    project_root = Path(__file__).resolve().parents[2]
    
    csv_path = project_root / "data" / "derived" / "results.csv"
    schema_path = project_root / "specs" / "001-llmxive-followup" / "contracts" / "pivot_attempt.schema.yaml"
    
    try:
        print(f"Validating {csv_path} against {schema_path}...")
        validate_csv_schema(csv_path, schema_path)
        print("SUCCESS: CSV schema matches the pivot_attempt schema definition.")
        return 0
    except FileNotFoundError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        return 1
    except ValueError as e:
        print(f"VALIDATION ERROR: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"UNEXPECTED ERROR: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
