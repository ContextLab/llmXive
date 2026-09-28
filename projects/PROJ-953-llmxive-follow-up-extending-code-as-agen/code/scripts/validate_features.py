import os
import sys
import csv
import json
from pathlib import Path
from typing import List, Dict, Any, Set

# Required columns based on T021 and T024 implementation
REQUIRED_METRICS = {
    'dependency_depth',
    'cyclomatic_complexity',
    'lines_of_code',
    'semantic_complexity_score',
    'dynamic_execution_outcome',
    'task_id'
}

def load_features_csv(path: str) -> List[Dict[str, Any]]:
    """Load the features CSV file."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Features file not found: {path}")
    
    data = []
    with open(path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append(row)
    return data

def validate_columns_present(data: List[Dict[str, Any]], required: Set[str]) -> List[str]:
    """Check if all required columns are present in the data."""
    if not data:
        return ["No data rows found in features.csv"]
    
    missing = []
    first_row_keys = set(data[0].keys())
    for req in required:
        if req not in first_row_keys:
            missing.append(req)
    return missing

def validate_no_missing_metrics(data: List[Dict[str, Any]], metric_columns: Set[str]) -> List[Dict[str, Any]]:
    """
    Validate that no metric values are missing (empty string or None) in the specified columns.
    Returns a list of rows that have missing values.
    """
    problematic_rows = []
    
    for i, row in enumerate(data):
        for col in metric_columns:
            value = row.get(col)
            if value is None or str(value).strip() == '':
                problematic_rows.append({
                    'row_index': i,
                    'task_id': row.get('task_id', 'UNKNOWN'),
                    'missing_column': col,
                    'value': value
                })
                break  # Report first missing metric per row to avoid noise
    
    return problematic_rows

def main():
    """
    Main entry point for T025: Validate features.csv has no missing metric values.
    This script reads data/processed/features.csv and ensures all structural metrics
    are populated. If missing values are found, it exits with code 1 and prints details.
    """
    features_path = Path("data/processed/features.csv")
    
    if not features_path.exists():
        print(f"ERROR: {features_path} does not exist. Run T024 first.")
        sys.exit(1)

    print(f"Loading {features_path}...")
    try:
        data = load_features_csv(str(features_path))
    except Exception as e:
        print(f"ERROR: Failed to load features CSV: {e}")
        sys.exit(1)

    if not data:
        print("ERROR: features.csv is empty.")
        sys.exit(1)

    # 1. Validate columns
    missing_cols = validate_columns_present(data, REQUIRED_METRICS)
    if missing_cols:
        print(f"ERROR: Missing required columns: {missing_cols}")
        sys.exit(1)
    print("✓ All required columns present.")

    # 2. Validate no missing metric values
    # We check the numeric/structural metrics specifically
    metric_cols = {'dependency_depth', 'cyclomatic_complexity', 'lines_of_code', 'semantic_complexity_score'}
    problematic = validate_no_missing_metrics(data, metric_cols)

    if problematic:
        print(f"ERROR: Found {len(problematic)} rows with missing metric values.")
        for p in problematic[:10]:  # Show first 10
            print(f"  Row {p['row_index']} (task_id={p['task_id']}): missing '{p['missing_column']}'")
        if len(problematic) > 10:
            print(f"  ... and {len(problematic) - 10} more.")
        sys.exit(1)

    print("✓ Validation successful: No missing metric values in features.csv.")
    sys.exit(0)

if __name__ == "__main__":
    main()