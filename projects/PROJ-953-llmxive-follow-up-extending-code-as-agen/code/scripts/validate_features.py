"""
Feature Validation Module.

Validates the generated features CSV for completeness and correctness.
"""
import os
import sys
import csv
import json
from pathlib import Path
from typing import List, Dict, Any, Set

from config.loader import get_config

def load_features_csv(csv_path: Path) -> List[Dict[str, Any]]:
    """Load features CSV."""
    if not csv_path.exists():
        raise FileNotFoundError(f"Features file not found: {csv_path}")
    with open(csv_path, 'r') as f:
        return list(csv.DictReader(f))

def validate_columns_present(records: List[Dict[str, Any]], required_cols: Set[str]) -> bool:
    """Check if all required columns are present."""
    if not records:
        return False
    first_row_keys = set(records[0].keys())
    missing = required_cols - first_row_keys
    if missing:
        print(f"Missing columns: {missing}")
        return False
    return True

def validate_no_missing_metrics(records: List[Dict[str, Any]], metric_cols: Set[str]) -> bool:
    """Check if any metric values are missing (empty string or NaN)."""
    for i, row in enumerate(records):
        for col in metric_cols:
            val = row.get(col, "")
            if val == "" or val is None:
                print(f"Missing metric '{col}' in row {i} (task_id: {row.get('task_id')})")
                return False
    return True

def main():
    """Main entry point for validation."""
    config = get_config()
    data_dir = Path(config.get("data_dir", "data"))
    processed_dir = data_dir / "processed"

    features_path = processed_dir / "features.csv"
    
    if not features_path.exists():
        print("Error: features.csv not found.")
        sys.exit(1)

    records = load_features_csv(features_path)
    required_cols = {"task_id", "dynamic_execution_outcome", "lines_of_code", "cyclomatic_complexity", "dependency_depth", "semantic_complexity_score"}
    metric_cols = {"lines_of_code", "cyclomatic_complexity", "dependency_depth", "semantic_complexity_score"}

    print("Validating columns...")
    if not validate_columns_present(records, required_cols):
        print("Validation FAILED: Missing required columns.")
        sys.exit(1)

    print("Validating metrics...")
    if not validate_no_missing_metrics(records, metric_cols):
        print("Validation FAILED: Missing metric values.")
        sys.exit(1)

    print("Validation PASSED.")

if __name__ == "__main__":
    main()
