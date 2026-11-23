import os
import sys
from pathlib import Path
import pandas as pd

def verify_golden_set():
    """
    Verifies the presence and validity of the Golden Set file.
    
    Checks:
    1. File existence at data/processed/golden_set.csv
    2. Minimum row count (>= 50)
    3. Presence of 'expert_load_score' or required self-report columns
    
    If validation fails, prints the specific error message and exits with code 1.
    """
    project_root = Path(__file__).parent.parent
    golden_set_path = project_root / "data" / "processed" / "golden_set.csv"
    
    # Check file existence
    if not golden_set_path.exists():
        print("Validation Data Missing: Golden Set or required interaction features with concurrent self-reports not found. Cannot proceed with model training.")
        sys.exit(1)
    
    try:
        df = pd.read_csv(golden_set_path)
    except Exception as e:
        print(f"Validation Data Missing: Could not read golden_set.csv. Error: {e}")
        sys.exit(1)
    
    # Check minimum sample size
    if len(df) < 50:
        print("Validation Data Missing: Golden Set or required interaction features with concurrent self-reports not found. Cannot proceed with model training.")
        sys.exit(1)
    
    # Check for required target column
    has_expert_score = 'expert_load_score' in df.columns
    has_self_reports = all(col in df.columns for col in ['self_report_load', 'self_report_confidence'])
    
    if not has_expert_score and not has_self_reports:
        print("Validation Data Missing: Golden Set or required interaction features with concurrent self-reports not found. Cannot proceed with model training.")
        sys.exit(1)
    
    print(f"Golden Set validated: {len(df)} interactions found at {golden_set_path}")
    return True

def main():
    verify_golden_set()

if __name__ == "__main__":
    main()
