"""
Validation script for User Story 2 (T025).
Ensures no missing metric values in data/processed/features.csv.

This script validates the integrity of the generated features dataset by:
1. Loading features.csv
2. Checking for null/empty values in all required metric columns
3. Reporting any rows with missing data
4. Exiting with non-zero status if validation fails
"""
import os
import sys
import csv
import json
from pathlib import Path
from typing import List, Dict, Any, Set

# Define expected columns based on US2 requirements
REQUIRED_COLUMNS = {
    'task_id',
    'code_diff',
    'dynamic_execution_outcome',
    'dependency_depth',
    'cyclomatic_complexity',
    'semantic_complexity_score',
    'lines_of_code'
}

# Metrics that must not be null/empty
METRIC_COLUMNS = {
    'dependency_depth',
    'cyclomatic_complexity',
    'semantic_complexity_score',
    'lines_of_code'
}

def load_features_csv(file_path: Path) -> List[Dict[str, Any]]:
    """Load features.csv and return list of row dictionaries."""
    if not file_path.exists():
        raise FileNotFoundError(f"Features file not found: {file_path}")
    
    rows = []
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(row)
    return rows

def validate_columns_present(rows: List[Dict[str, Any]]) -> Set[str]:
    """Check that all required columns are present."""
    if not rows:
        return set()
    
    actual_columns = set(rows[0].keys())
    missing = REQUIRED_COLUMNS - actual_columns
    return missing

def validate_no_missing_metrics(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Check for missing/null/empty values in metric columns.
    Returns list of problematic rows.
    """
    problematic_rows = []
    
    for idx, row in enumerate(rows):
        for metric_col in METRIC_COLUMNS:
            value = row.get(metric_col)
            
            # Check for None, empty string, or whitespace-only
            if value is None or (isinstance(value, str) and value.strip() == ''):
                problematic_rows.append({
                    'row_index': idx,
                    'task_id': row.get('task_id', 'UNKNOWN'),
                    'missing_column': metric_col,
                    'value': value
                })
            # Check for non-numeric values in numeric columns
            elif metric_col in METRIC_COLUMNS:
                try:
                    float(value)
                except (ValueError, TypeError):
                    problematic_rows.append({
                        'row_index': idx,
                        'task_id': row.get('task_id', 'UNKNOWN'),
                        'missing_column': metric_col,
                        'value': value,
                        'issue': 'non-numeric'
                    })
    
    return problematic_rows

def main():
    """Main validation entry point."""
    project_root = Path(__file__).parent.parent.parent
    features_path = project_root / 'data' / 'processed' / 'features.csv'
    
    print(f"Validating features file: {features_path}")
    
    try:
        rows = load_features_csv(features_path)
        print(f"Loaded {len(rows)} rows from features.csv")
        
        if not rows:
            print("ERROR: features.csv is empty")
            sys.exit(1)
        
        # Check 1: Verify all required columns exist
        missing_columns = validate_columns_present(rows)
        if missing_columns:
            print(f"ERROR: Missing required columns: {missing_columns}")
            sys.exit(1)
        print("✓ All required columns present")
        
        # Check 2: Verify no missing metric values
        problematic = validate_no_missing_metrics(rows)
        
        if problematic:
            print(f"ERROR: Found {len(problematic)} missing/invalid metric values:")
            for issue in problematic[:10]:  # Show first 10
                print(f"  Row {issue['row_index']} (task_id={issue['task_id']}): "
                      f"{issue['missing_column']} = {issue['value']}")
            if len(problematic) > 10:
                print(f"  ... and {len(problematic) - 10} more issues")
            sys.exit(1)
        
        print("✓ All metric values are present and valid")
        
        # Write validation report
        report = {
            'status': 'valid',
            'total_rows': len(rows),
            'columns_checked': list(REQUIRED_COLUMNS),
            'metrics_validated': list(METRIC_COLUMNS),
            'issues_found': 0
        }
        
        report_path = project_root / 'data' / 'processed' / 'features_validation_report.json'
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2)
        print(f"✓ Validation report written to: {report_path}")
        
        print("\nValidation PASSED: features.csv is complete and valid")
        sys.exit(0)
        
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: Unexpected error during validation: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
