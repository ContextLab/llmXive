"""
Validation Script SC001.
"""
import os
import sys
from pathlib import Path
import pandas as pd
from config import ensure_directories

def validate_sc001() -> bool:
    """Validates SC001 requirements."""
    ensure_directories()
    path = Path("data/processed/correlation_results.csv")
    if not path.exists():
        return False
    df = pd.read_csv(path)
    # Check columns
    required = ["r_value", "p_value", "n_obs"]
    return all(c in df.columns for c in required)

def main():
    if validate_sc001():
        print("SC001 Valid.")
    else:
        print("SC001 Invalid.")
        sys.exit(1)

if __name__ == "__main__":
    main()
