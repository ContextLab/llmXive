"""
Verification script for the Golden Set.
Ensures data/processed/golden_set.csv exists with >= 50 expert-labeled interactions.
"""
import os
import sys
from pathlib import Path
import pandas as pd

# Add parent directory to path for imports if running as script
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent))

GOLDEN_SET_PATH = Path("data/processed/golden_set.csv")
MIN_INTERACTIONS = 50
REQUIRED_COLUMNS = ["expert_load_score"]

def verify_golden_set() -> bool:
    """
    Verifies the existence and validity of the Golden Set file.
    
    Returns:
        bool: True if the Golden Set is valid and meets requirements, False otherwise.
    
    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file is empty, has insufficient rows, or missing required columns.
    """
    if not GOLDEN_SET_PATH.exists():
        raise FileNotFoundError(
            f"CRITICAL: Golden Set file not found at {GOLDEN_SET_PATH}. "
            "The pipeline cannot proceed without expert-labeled data. "
            "Please fetch external data or run code/create_golden_set.py to generate a synthetic set based on the rubric."
        )

    try:
        df = pd.read_csv(GOLDEN_SET_PATH)
    except Exception as e:
        raise ValueError(f"CRITICAL: Failed to read Golden Set CSV: {e}")

    if df.empty:
        raise ValueError("CRITICAL: Golden Set file is empty.")

    # Check row count
    n_rows = len(df)
    if n_rows < MIN_INTERACTIONS:
        raise ValueError(
            f"CRITICAL: Golden Set has {n_rows} interactions, but requires at least {MIN_INTERACTIONS}. "
            "The model validation (US1) requires a minimum sample size for statistical power."
        )

    # Check required columns
    missing_cols = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing_cols:
        raise ValueError(
            f"CRITICAL: Golden Set is missing required columns: {missing_cols}. "
            f"Expected columns include: {REQUIRED_COLUMNS}"
        )

    # Verify expert_load_score is numeric and within reasonable bounds (0-100)
    score_col = df["expert_load_score"]
    if not pd.api.types.is_numeric_dtype(score_col):
        raise ValueError("CRITICAL: 'expert_load_score' column must be numeric.")
    
    # Optional: Check for NaNs in the score column
    if score_col.isna().any():
        raise ValueError("CRITICAL: 'expert_load_score' column contains missing values.")

    print(f"SUCCESS: Golden Set verified at {GOLDEN_SET_PATH}")
    print(f"  - Rows: {n_rows}")
    print(f"  - Columns: {list(df.columns)}")
    print(f"  - Expert Load Score Range: [{score_col.min():.2f}, {score_col.max():.2f}]")
    
    return True

def main():
    try:
        verify_golden_set()
        sys.exit(0)
    except (FileNotFoundError, ValueError) as e:
        print(str(e))
        sys.exit(1)
    except Exception as e:
        print(f"UNEXPECTED ERROR: {e}")
        sys.exit(2)

if __name__ == "__main__":
    main()