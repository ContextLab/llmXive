"""
Script to verify that the sensitivity analysis DataFrame includes the required
'correlation' and 'p_value' columns for each window length (SC-005).
"""
import os
import sys
import pandas as pd
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from config import get_config
from errors import DataMissingCreativityError

REQUIRED_COLUMNS = ['window_length', 'correlation', 'p_value']
SENSITIVITY_FILE = 'data/interim/sensitivity_summary.csv'

def verify_sensitivity_dataframe(file_path: str) -> bool:
    """
    Verifies that the sensitivity analysis CSV file exists and contains
    the required columns: 'window_length', 'correlation', 'p_value'.

    Args:
        file_path: Relative path to the sensitivity summary CSV.

    Returns:
        True if verification passes, False otherwise.

    Raises:
        DataMissingCreativityError: If file is missing or columns are absent.
    """
    config = get_config()
    full_path = Path(config.DATA_PATH) / file_path

    if not full_path.exists():
        raise DataMissingCreativityError(
            f"Sensitivity analysis file not found: {full_path}"
        )

    try:
        df = pd.read_csv(full_path)
    except Exception as e:
        raise DataMissingCreativityError(
            f"Failed to read sensitivity analysis CSV: {e}"
        )

    missing_cols = [col for col in REQUIRED_COLUMNS if col not in df.columns]

    if missing_cols:
        raise DataMissingCreativityError(
            f"Sensitivity DataFrame missing required columns: {missing_cols}. "
            f"Found columns: {list(df.columns)}"
        )

    # Verify data integrity: check for NaN in critical columns
    if df['correlation'].isna().any() or df['p_value'].isna().any():
        raise DataMissingCreativityError(
            "Sensitivity DataFrame contains NaN values in 'correlation' or 'p_value'."
        )

    # Verify we have data for multiple window lengths (at least 1)
    if df.empty:
        raise DataMissingCreativityError(
            "Sensitivity DataFrame is empty."
        )

    return True

def main():
    """Main entry point for verification script."""
    print(f"Verifying sensitivity analysis at: {SENSITIVITY_FILE}")
    
    try:
        verify_sensitivity_dataframe(SENSITIVITY_FILE)
        print("SUCCESS: Sensitivity DataFrame verification passed.")
        print("Required columns 'correlation' and 'p_value' are present.")
        return 0
    except DataMissingCreativityError as e:
        print(f"VERIFICATION FAILED: {e}")
        return 1
    except Exception as e:
        print(f"UNEXPECTED ERROR: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())