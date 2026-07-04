"""
Schema validation logic for raw Trends data (T004b).

Validates CSV data against the schema:
{
  "type": "object",
  "required": ["date", "value", "source"],
  "properties": {
    "date": {"type": "string", "format": "date"},
    "value": {"type": "number"},
    "source": {"type": "string"}
  }
}
"""
import csv
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Tuple


SCHEMA = {
    "type": "object",
    "required": ["date", "value", "source"],
    "properties": {
        "date": {"type": "string", "format": "date"},
        "value": {"type": "number"},
        "source": {"type": "string"}
    }
}


class ValidationError(Exception):
    """Raised when data fails schema validation."""
    pass


def validate_date_format(date_str: str) -> bool:
    """Check if date string matches ISO 8601 date format (YYYY-MM-DD)."""
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def validate_row(row: Dict[str, str], row_num: int) -> Tuple[bool, str]:
    """
    Validate a single row against the schema.
    
    Args:
        row: Dictionary representing a CSV row.
        row_num: Line number in the CSV (for error reporting).
        
    Returns:
        Tuple of (is_valid, error_message). If valid, error_message is empty.
    """
    errors = []
    
    # Check required fields
    for field in SCHEMA["required"]:
        if field not in row or not row[field]:
            errors.append(f"Row {row_num}: Missing required field '{field}'")
    
    if errors:
        return False, "; ".join(errors)
    
    # Validate date format
    if not validate_date_format(row["date"]):
        errors.append(f"Row {row_num}: Invalid date format '{row['date']}'. Expected YYYY-MM-DD.")
    
    # Validate value is a number
    try:
        float(row["value"])
    except ValueError:
        errors.append(f"Row {row_num}: Invalid value '{row['value']}'. Expected a number.")
    
    # Validate source is a string (already string from CSV, but check not empty)
    if not isinstance(row["source"], str) or not row["source"].strip():
        errors.append(f"Row {row_num}: Invalid source '{row['source']}'. Expected non-empty string.")
    
    if errors:
        return False, "; ".join(errors)
    
    return True, ""


def validate_csv_file(file_path: str) -> Dict[str, Any]:
    """
    Validate an entire CSV file against the schema.
    
    Args:
        file_path: Path to the CSV file.
        
    Returns:
        Dictionary with validation results:
        {
            "valid": bool,
            "total_rows": int,
            "valid_rows": int,
            "errors": List[str]
        }
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    results = {
        "valid": True,
        "total_rows": 0,
        "valid_rows": 0,
        "errors": []
    }
    
    with open(path, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        
        # Verify header contains required fields
        required_fields = set(SCHEMA["required"])
        if reader.fieldnames is None:
            raise ValidationError("CSV file is empty or has no header.")
        
        header_fields = set(reader.fieldnames)
        missing_fields = required_fields - header_fields
        if missing_fields:
            raise ValidationError(f"CSV header missing required fields: {missing_fields}")
        
        for row_num, row in enumerate(reader, start=2):  # Start at 2 (1 is header)
            results["total_rows"] += 1
            is_valid, error_msg = validate_row(row, row_num)
            
            if is_valid:
                results["valid_rows"] += 1
            else:
                results["valid"] = False
                results["errors"].append(error_msg)
    
    return results


def validate_and_save_report(input_path: str, output_path: str) -> None:
    """
    Validate a CSV file and save the validation report to a text file.
    
    Args:
        input_path: Path to the input CSV file.
        output_path: Path to save the validation report.
    """
    results = validate_csv_file(input_path)
    
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(f"Schema Validation Report for {input_path}\n")
        f.write("=" * 50 + "\n\n")
        f.write(f"Total Rows: {results['total_rows']}\n")
        f.write(f"Valid Rows: {results['valid_rows']}\n")
        f.write(f"Validation Status: {'PASSED' if results['valid'] else 'FAILED'}\n\n")
        
        if results["errors"]:
            f.write(f"Errors ({len(results['errors'])}):\n")
            for error in results["errors"]:
                f.write(f"  - {error}\n")
        else:
            f.write("No validation errors found.\n")
    
    print(f"Validation report saved to: {output_path}")
    if not results["valid"]:
        print(f"Validation FAILED with {len(results['errors'])} errors.")
        sys.exit(1)
    else:
        print("Validation PASSED.")


def main():
    """Main entry point for CLI usage."""
    if len(sys.argv) < 2:
        print("Usage: python validate_trends_schema.py <input_csv> [output_report]")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2] if len(sys.argv) > 2 else "data/processed/trends_validation_report.txt"
    
    try:
        validate_and_save_report(input_file, output_file)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except ValidationError as e:
        print(f"Validation Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
