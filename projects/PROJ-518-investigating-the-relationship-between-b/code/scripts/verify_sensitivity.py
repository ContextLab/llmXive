import os
import sys
import pandas as pd
from pathlib import Path
from config import get_config
from errors import DataMissingCreativityError

def verify_sensitivity_dataframe(df: pd.DataFrame) -> bool:
    """
    Verify the sensitivity analysis DataFrame has the required columns and structure.
    
    Args:
        df: The DataFrame to verify.
        
    Returns:
        True if valid, False otherwise.
    """
    required_columns = {"window_length", "correlation", "p_value"}
    if not required_columns.issubset(df.columns):
        return False
    
    # Check for non-empty DataFrame
    if len(df) == 0:
        return False
    
    # Check for NaN in critical columns (optional, but good practice)
    if df["correlation"].isna().all() or df["p_value"].isna().all():
        return False
        
    return True

def main():
    """
    Main function to run the sensitivity analysis and verify the output.
    This script is intended to be run after the analysis has been performed.
    """
    config = get_config()
    output_path = Path(config.DATA_PATH) / "interim" / "sensitivity_summary.csv"
    
    if not output_path.exists():
        print(f"Error: Sensitivity summary file not found at {output_path}")
        print("Please run the sensitivity analysis first.")
        sys.exit(1)
    
    try:
        df = pd.read_csv(output_path)
        if verify_sensitivity_dataframe(df):
            print("Sensitivity analysis DataFrame verification: PASSED")
            print(f"Columns: {list(df.columns)}")
            print(f"Rows: {len(df)}")
            print(df.to_string(index=False))
            sys.exit(0)
        else:
            print("Sensitivity analysis DataFrame verification: FAILED")
            print("Missing required columns or invalid data structure.")
            sys.exit(1)
    except Exception as e:
        print(f"Error reading or verifying sensitivity summary: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()