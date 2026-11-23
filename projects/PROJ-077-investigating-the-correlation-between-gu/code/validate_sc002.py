"""
Validation Script SC002.
"""
import os
import sys
import pandas as pd
from pathlib import Path

def validate_sc002() -> bool:
    """Validates SC002 requirements."""
    path = Path("data/processed/regression_results.csv")
    if not path.exists():
        return False
    df = pd.read_csv(path)
    required = ["predictor", "coefficient", "std_err", "p_value"]
    return all(c in df.columns for c in required)

def main():
    if validate_sc002():
        print("SC002 Valid.")
    else:
        print("SC002 Invalid.")
        sys.exit(1)

if __name__ == "__main__":
    main()
