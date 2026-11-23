"""
Task T020: Validate output schema for network metrics.

Validates that data/results/network_metrics.csv exists and contains the required columns
with correct data types as specified in the task description.

Required columns:
- participant_id (string)
- age (integer)
- global_efficiency (float)
- local_efficiency (float)
- clustering_coeff (float)
- modularity (float)
- trace_id (string, SHA-256 hex)
- signal_quality_flag (string)
"""
import csv
import json
import sys
from pathlib import Path
from typing import Dict, Any, List, Tuple
from config import ensure_dirs

# Expected schema definition
EXPECTED_COLUMNS = [
    "participant_id",
    "age",
    "global_efficiency",
    "local_efficiency",
    "clustering_coeff",
    "modularity",
    "trace_id",
    "signal_quality_flag"
]

# Expected data types for each column
EXPECTED_TYPES = {
    "participant_id": str,
    "age": int,
    "global_efficiency": float,
    "local_efficiency": float,
    "clustering_coeff": float,
    "modularity": float,
    "trace_id": str,
    "signal_quality_flag": str
}

# Validation patterns
TRACE_ID_PATTERN = r'^[a-f0-9]{64}$'  # SHA-256 hex string

def load_schema() -> Dict[str, Any]:
    """Load the expected schema definition."""
    return {
        "columns": EXPECTED_COLUMNS,
        "types": EXPECTED_TYPES
    }

def validate_trace_id_format(trace_id: str) -> bool:
    """Validate that trace_id is a valid SHA-256 hex string."""
    import re
    return bool(re.match(TRACE_ID_PATTERN, trace_id))

def validate_row(row: Dict[str, str], row_num: int) -> List[str]:
    """
    Validate a single row against the expected schema.
    Returns a list of error messages if validation fails.
    """
    errors = []
    
    # Check for missing columns
    for col in EXPECTED_COLUMNS:
        if col not in row:
            errors.append(f"Row {row_num}: Missing required column '{col}'")
    
    if errors:
        return errors

    # Validate types and values
    for col in EXPECTED_COLUMNS:
        value = row[col]
        expected_type = EXPECTED_TYPES[col]
        
        # Special handling for trace_id validation
        if col == "trace_id":
            if not validate_trace_id_format(value):
                errors.append(f"Row {row_num}: Invalid trace_id format '{value}'")
            continue
        
        # Type conversion and validation
        try:
            if expected_type == int:
                int(value)
            elif expected_type == float:
                # Check for NaN or Inf
                val = float(value)
                if val != val or val == float('inf') or val == float('-inf'):
                    errors.append(f"Row {row_num}: Invalid float value for '{col}': '{value}'")
            elif expected_type == str:
                if not isinstance(value, str):
                    errors.append(f"Row {row_num}: Expected string for '{col}', got {type(value)}")
        except ValueError as e:
            errors.append(f"Row {row_num}: Type conversion failed for '{col}': {e}")
    
    return errors

def main():
    """Main validation function for T020."""
    ensure_dirs()
    
    metrics_path = Path("data/results/network_metrics.csv")
    output_path = Path("data/results/schema_validation_report.json")
    
    report = {
        "task_id": "T020",
        "file_validated": str(metrics_path),
        "status": "unknown",
        "errors": [],
        "summary": {}
    }
    
    # Check if file exists
    if not metrics_path.exists():
        report["status"] = "failed"
        report["errors"].append(f"File not found: {metrics_path}")
        report["summary"] = {
            "total_rows": 0,
            "valid_rows": 0,
            "invalid_rows": 0,
            "column_check": "skipped"
        }
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"Validation failed: {metrics_path} not found")
        sys.exit(0)  # Exit 0 as per T019 requirement - do not block pipeline
    
    # Read and validate CSV
    valid_rows = 0
    invalid_rows = 0
    total_rows = 0
    column_errors = []
    type_errors = []
    
    try:
        with open(metrics_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            # Check header columns
            if reader.fieldnames is None:
                report["status"] = "failed"
                report["errors"].append("CSV file is empty or has no header")
            else:
                header_columns = list(reader.fieldnames)
                missing_cols = [col for col in EXPECTED_COLUMNS if col not in header_columns]
                extra_cols = [col for col in header_columns if col not in EXPECTED_COLUMNS]
                
                if missing_cols:
                    column_errors.append(f"Missing columns: {missing_cols}")
                if extra_cols:
                    column_errors.append(f"Extra columns (not in schema): {extra_cols}")
                
                # Validate each row
                for row_num, row in enumerate(reader, start=2):  # Start at 2 (1 is header)
                    total_rows += 1
                    row_errors = validate_row(row, row_num)
                    
                    if row_errors:
                        invalid_rows += 1
                        type_errors.extend(row_errors)
                    else:
                        valid_rows += 1
    
    except Exception as e:
        report["status"] = "failed"
        report["errors"].append(f"Error reading CSV: {str(e)}")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(report, f, indent=2)
        sys.exit(0)
    
    # Determine final status
    if column_errors:
        report["status"] = "failed"
        report["errors"].extend(column_errors)
    elif type_errors:
        report["status"] = "failed"
        report["errors"].extend(type_errors)
    else:
        report["status"] = "passed"
    
    report["summary"] = {
        "total_rows": total_rows,
        "valid_rows": valid_rows,
        "invalid_rows": invalid_rows,
        "column_check": "passed" if not column_errors else "failed",
        "type_check": "passed" if not type_errors else "failed"
    }
    
    # Write report
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"Schema validation complete: {report['status']}")
    print(f"File: {metrics_path}")
    print(f"Total rows: {total_rows}, Valid: {valid_rows}, Invalid: {invalid_rows}")
    if column_errors:
        print(f"Column errors: {column_errors}")
    if type_errors:
        print(f"Type errors: {type_errors[:5]}...")  # Show first 5
    
    # Exit 0 regardless of result to avoid blocking pipeline
    sys.exit(0)

if __name__ == "__main__":
    main()
