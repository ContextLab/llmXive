import os
import sys
import json
import pandas as pd
import numpy as np
from typing import Dict, Any, List

# Ensure the code directory is in the path for imports if run as script
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

REQUIRED_COLUMNS = [
    'sample_id',
    'method',
    'prediction',
    'variance',
    'lower_50',
    'upper_50',
    'lower_90',
    'upper_90'
]

def verify_schema(file_path: str) -> Dict[str, Any]:
    """
    Verifies that the CSV file exists and matches the required schema.
    
    Args:
        file_path: Path to the CSV file to verify.
        
    Returns:
        Dictionary with 'valid' (bool), 'missing_columns' (list), 
        'unexpected_columns' (list), and 'row_count' (int).
    """
    result = {
        'valid': False,
        'missing_columns': [],
        'unexpected_columns': [],
        'row_count': 0,
        'errors': []
    }

    if not os.path.exists(file_path):
        result['errors'].append(f"File not found: {file_path}")
        return result

    try:
        df = pd.read_csv(file_path)
        result['row_count'] = len(df)
        actual_columns = list(df.columns)
        
        # Check for missing required columns
        missing = set(REQUIRED_COLUMNS) - set(actual_columns)
        if missing:
            result['missing_columns'] = list(missing)
            result['errors'].append(f"Missing columns: {missing}")
        
        # Check for unexpected columns (strict schema match)
        unexpected = set(actual_columns) - set(REQUIRED_COLUMNS)
        if unexpected:
            result['unexpected_columns'] = list(unexpected)
            result['errors'].append(f"Unexpected columns: {unexpected}")
        
        # Verify column order matches exactly
        if actual_columns != REQUIRED_COLUMNS:
            result['errors'].append(f"Column order mismatch. Expected: {REQUIRED_COLUMNS}, Got: {actual_columns}")
        
        # Verify data types for numeric columns
        numeric_cols = ['prediction', 'variance', 'lower_50', 'upper_50', 'lower_90', 'upper_90']
        for col in numeric_cols:
            if col in actual_columns:
                if not pd.api.types.is_numeric_dtype(df[col]):
                    result['errors'].append(f"Column '{col}' is not numeric. Found dtype: {df[col].dtype}")
        
        # Verify sample_id is integer
        if 'sample_id' in actual_columns:
            if not pd.api.types.is_integer_dtype(df['sample_id']):
                result['errors'].append(f"Column 'sample_id' is not integer. Found dtype: {df['sample_id'].dtype}")

        if not result['errors']:
            result['valid'] = True

    except Exception as e:
        result['errors'].append(f"Error reading file: {str(e)}")

    return result

def verify_data_integrity(file_path: str) -> Dict[str, Any]:
    """
    Verifies logical consistency of the data (e.g., lower < upper, variance >= 0).
    
    Args:
        file_path: Path to the CSV file to verify.
        
    Returns:
        Dictionary with 'valid' (bool) and 'errors' (list).
    """
    result = {
        'valid': False,
        'errors': []
    }

    if not os.path.exists(file_path):
        result['errors'].append(f"File not found: {file_path}")
        return result

    try:
        df = pd.read_csv(file_path)

        # Check variance >= 0
        if 'variance' in df.columns:
            if (df['variance'] < 0).any():
                result['errors'].append(f"Found negative variance values. Count: {(df['variance'] < 0).sum()}")

        # Check lower_50 <= upper_50
        if 'lower_50' in df.columns and 'upper_50' in df.columns:
            invalid_50 = (df['lower_50'] > df['upper_50']).sum()
            if invalid_50 > 0:
                result['errors'].append(f"Found {invalid_50} rows where lower_50 > upper_50")

        # Check lower_90 <= upper_90
        if 'lower_90' in df.columns and 'upper_90' in df.columns:
            invalid_90 = (df['lower_90'] > df['upper_90']).sum()
            if invalid_90 > 0:
                result['errors'].append(f"Found {invalid_90} rows where lower_90 > upper_90")

        # Check bounds contain prediction (within tolerance for float)
        if all(c in df.columns for c in ['prediction', 'lower_50', 'upper_50']):
            outside_50 = ((df['prediction'] < df['lower_50']) | (df['prediction'] > df['upper_50'])).sum()
            if outside_50 > 0:
                result['errors'].append(f"Found {outside_50} rows where prediction is outside 50% bounds")

        if all(c in df.columns for c in ['prediction', 'lower_90', 'upper_90']):
            outside_90 = ((df['prediction'] < df['lower_90']) | (df['prediction'] > df['upper_90'])).sum()
            if outside_90 > 0:
                result['errors'].append(f"Found {outside_90} rows where prediction is outside 90% bounds")

        if not result['errors']:
            result['valid'] = True

    except Exception as e:
        result['errors'].append(f"Error processing file: {str(e)}")

    return result

def main():
    """
    Main entry point to verify results/uq_predictions_base.csv.
    Exits with code 0 if valid, 1 if invalid or missing.
    """
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    file_path = os.path.join(base_dir, 'results', 'uq_predictions_base.csv')
    
    print(f"Verifying: {file_path}")
    
    schema_result = verify_schema(file_path)
    integrity_result = verify_data_integrity(file_path)
    
    all_valid = schema_result['valid'] and integrity_result['valid']
    
    print("\n--- Schema Verification ---")
    if schema_result['valid']:
        print("Schema: VALID")
    else:
        print("Schema: INVALID")
        for err in schema_result['errors']:
            print(f"  - {err}")
    
    print("\n--- Data Integrity Verification ---")
    if integrity_result['valid']:
        print("Integrity: VALID")
    else:
        print("Integrity: INVALID")
        for err in integrity_result['errors']:
            print(f"  - {err}")
    
    print(f"\nTotal Rows: {schema_result['row_count']}")
    
    if all_valid:
        print("\n✅ T018 VERIFICATION PASSED: results/uq_predictions_base.csv is valid.")
        sys.exit(0)
    else:
        print("\n❌ T018 VERIFICATION FAILED: results/uq_predictions_base.csv is invalid or missing.")
        sys.exit(1)

if __name__ == "__main__":
    main()