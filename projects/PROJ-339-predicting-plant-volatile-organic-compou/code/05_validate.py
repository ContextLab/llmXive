import os
import sys
import json
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

# Import from local utils if available, otherwise define locally to ensure self-containment
# The API surface lists `utils.validation` but we need to ensure we can run this task independently
# or import correctly. Based on the surface:
try:
    from utils.validation import validate_data_types as utils_validate_types
except ImportError:
    utils_validate_types = None

def load_merged_dataset(file_path: str) -> pd.DataFrame:
    """
    Load the merged dataset from the specified path.
    Raises FileNotFoundError if the file does not exist.
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Merged dataset not found at {file_path}. "
                                "Please run the pipeline up to T016 first.")
    return pd.read_csv(path)

def validate_numeric_columns(df: pd.DataFrame, report: Dict[str, Any]) -> None:
    """
    Validate that all expected data columns are numeric and contain no non-numeric entries.
    Updates the report dictionary in place with validation results.
    """
    issues = []
    columns_checked = 0
    numeric_columns = 0

    # Identify potential feature/target columns (exclude ID columns)
    # Assuming 'sample_id' or similar is the ID column
    id_cols = [col for col in df.columns if 'id' in col.lower() or col == 'sample_id']
    feature_cols = [col for col in df.columns if col not in id_cols]

    report['total_columns'] = len(df.columns)
    report['feature_columns'] = len(feature_cols)

    for col in feature_cols:
        columns_checked += 1
        # Check if column is numeric
        if not pd.api.types.is_numeric_dtype(df[col]):
            # Try to convert to numeric to see if it's just a formatting issue
            try:
                converted = pd.to_numeric(df[col], errors='raise')
                # If successful, check for NaNs introduced by conversion
                if converted.isna().any() and df[col].notna().any():
                    issues.append({
                        'column': col,
                        'issue': 'Non-numeric values present',
                        'count': df[col].isna().sum(),
                        'severity': 'error'
                    })
                else:
                    # It was convertible but not originally numeric dtype
                    issues.append({
                        'column': col,
                        'issue': 'Column is not numeric dtype but convertible',
                        'severity': 'warning'
                    })
            except (ValueError, TypeError):
                issues.append({
                    'column': col,
                    'issue': 'Contains non-numeric entries',
                    'severity': 'error'
                })
        else:
            numeric_columns += 1
            # Check for infinite values which are not valid for most ML models
            if np.isinf(df[col]).any():
                issues.append({
                    'column': col,
                    'issue': 'Contains infinite values',
                    'severity': 'error'
                })
            # Check for NaNs (depending on imputation strategy, this might be allowed,
            # but T017 asks for "no non-numeric entries", implying clean data)
            if df[col].isna().any():
                issues.append({
                    'column': col,
                    'issue': 'Contains missing values (NaN)',
                    'severity': 'warning' # Warning because imputation might be expected here
                })

    report['numeric_columns_count'] = numeric_columns
    report['issues_found'] = len(issues)
    report['issues'] = issues
    report['is_valid'] = len([i for i in issues if i['severity'] == 'error']) == 0

def generate_validation_report(df: pd.DataFrame, output_path: str) -> Dict[str, Any]:
    """
    Generate a comprehensive validation report for the dataset.
    Saves the report to the specified JSON path.
    """
    report = {
        'validation_timestamp': datetime.now().isoformat(),
        'source_file': str(output_path).replace('.json', '.csv'), # The source of validation
        'status': 'unknown',
        'summary': {},
        'details': {}
    }

    # Basic stats
    report['summary']['row_count'] = len(df)
    report['summary']['column_count'] = len(df.columns)
    report['summary']['columns'] = list(df.columns)

    # Validate numeric columns
    validate_numeric_columns(df, report['details'])

    # Determine overall status
    if report['details']['is_valid']:
        report['status'] = 'passed'
    else:
        report['status'] = 'failed'

    # Save report
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w') as f:
        json.dump(report, f, indent=2, default=str)

    return report

def main():
    """
    Main entry point for T017: Validation of merged dataset.
    1. Loads data/processed/merged_dataset.csv
    2. Validates types and numeric integrity
    3. Generates data/results/data_validation_report.json
    """
    # Define paths relative to project root
    project_root = Path(__file__).resolve().parent.parent
    input_path = project_root / 'data' / 'processed' / 'merged_dataset.csv'
    output_path = project_root / 'data' / 'results' / 'data_validation_report.json'

    print(f"Starting validation for task T017...")
    print(f"Input file: {input_path}")
    print(f"Output file: {output_path}")

    if not input_path.exists():
        print(f"ERROR: Input file not found. Please ensure T016 has been completed.")
        sys.exit(1)

    try:
        df = load_merged_dataset(str(input_path))
        print(f"Loaded dataset with shape: {df.shape}")

        report = generate_validation_report(df, str(output_path))

        print(f"Validation completed. Status: {report['status']}")
        print(f"Issues found: {report['details']['issues_found']}")

        if report['status'] == 'failed':
            print("CRITICAL ERRORS DETECTED:")
            for issue in report['details']['issues']:
                if issue['severity'] == 'error':
                    print(f"  - {issue['column']}: {issue['issue']}")
            sys.exit(1)
        else:
            print("Validation passed. No critical errors found.")

    except Exception as e:
        print(f"ERROR during validation: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
