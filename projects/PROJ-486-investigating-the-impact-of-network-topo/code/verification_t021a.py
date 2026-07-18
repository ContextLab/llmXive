"""
Verification script for Task T021a.
Verifies that data/processed/correlation_results.csv contains the required columns
and that the collinearity_warning logic is correctly applied.
"""
import pandas as pd
import os
import sys

REQUIRED_COLUMNS = [
    'raw_p', 
    'adjusted_p_value', 
    'is_significant', 
    'vif_value', 
    'collinearity_warning',
    'data_source'
]

def verify_t021a():
    file_path = "data/processed/correlation_results.csv"
    
    if not os.path.exists(file_path):
        print(f"ERROR: File {file_path} does not exist.")
        sys.exit(1)
    
    df = pd.read_csv(file_path)
    
    # 1. Verify required columns exist
    missing_cols = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing_cols:
        print(f"ERROR: Missing required columns: {missing_cols}")
        sys.exit(1)
    
    print("✓ All required columns present.")
    
    # 2. Verify data types
    if df['collinearity_warning'].dtype != bool:
        print(f"ERROR: 'collinearity_warning' must be boolean, got {df['collinearity_warning'].dtype}")
        sys.exit(1)
    
    print("✓ 'collinearity_warning' is boolean.")
    
    # 3. Verify logic: collinearity_warning is True iff vif_value > 5
    expected_warning = df['vif_value'] > 5
    if not df['collinearity_warning'].equals(expected_warning):
        mismatches = df[df['collinearity_warning'] != expected_warning]
        print(f"ERROR: 'collinearity_warning' logic mismatch. Found {len(mismatches)} rows where logic failed.")
        print(mismatches)
        sys.exit(1)
    
    print("✓ 'collinearity_warning' logic is correct (True if VIF > 5).")
    
    # 4. Verify data_source label exists (Simulated or Real)
    valid_sources = {'Simulated', 'Real'}
    invalid_sources = set(df['data_source'].unique()) - valid_sources
    if invalid_sources:
        print(f"ERROR: Invalid data_source values found: {invalid_sources}")
        sys.exit(1)
    
    print(f"✓ Data source labels are valid ({df['data_source'].unique()}).")
    
    print("\n--- T021a Verification PASSED ---")
    print(f"Total rows: {len(df)}")
    print(f"Columns: {list(df.columns)}")
    print(f"Sample VIF: {df['vif_value'].iloc[0]:.2f}, Warning: {df['collinearity_warning'].iloc[0]}")

if __name__ == "__main__":
    verify_t021a()