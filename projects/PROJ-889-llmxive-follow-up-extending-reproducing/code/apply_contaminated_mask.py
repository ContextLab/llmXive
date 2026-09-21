import os
import sys
from pathlib import Path
from typing import Optional
import pandas as pd
import numpy as np

from code.config import get_project_root
from code.utils.io_utils import load_csv, save_csv

def load_divergence_data(path: Optional[str] = None) -> pd.DataFrame:
    """Load the divergence data, defaulting to the masked version if available."""
    if path is None:
        project_root = get_project_root()
        path = str(project_root / "data" / "processed" / "trajectories_divergence_masked.csv")
    return load_csv(path)

def apply_contaminated_mask(df: pd.DataFrame, column_prefix: str = "z_score_") -> pd.DataFrame:
    """
    Apply the contaminated mask to exclude contaminated timesteps from baseline calculations.
    This function doesn't change the data itself but prepares it for downstream tasks (T021, T022)
    by ensuring the 'is_contaminated' column is present and valid.

    In the context of T021/T022, the logic will be:
    "Use is_contaminated to skip timesteps when computing the rolling standard deviation".

    This function validates the mask and returns the dataframe ready for processing.
    """
    if 'is_contaminated' not in df.columns:
        raise ValueError("DataFrame must contain 'is_contaminated' column. Run identify_contaminated_windows.py first.")

    # Ensure it's boolean
    df['is_contaminated'] = df['is_contaminated'].astype(bool)
    return df

def main():
    """
    Main entry point to validate the contaminated mask and prepare data for T021/T022.
    """
    project_root = get_project_root()
    input_path = project_root / "data" / "processed" / "trajectories_divergence_masked.csv"

    if not input_path.exists():
        print(f"Error: Input file not found: {input_path}")
        print("Run identify_contaminated_windows.py first.")
        sys.exit(1)

    print(f"Loading data from {input_path}...")
    df = load_divergence_data(str(input_path))

    print("Applying/validating contaminated mask...")
    df = apply_contaminated_mask(df)

    # Verify the mask is reasonable (optional check)
    contaminated_count = df['is_contaminated'].sum()
    total_count = len(df)
    print(f"Contaminated timesteps: {contaminated_count} / {total_count} ({100*contaminated_count/total_count:.2f}%)")

    # Save back to ensure the file is clean (though it should be already)
    output_path = project_root / "data" / "processed" / "trajectories_divergence_masked.csv"
    save_csv(df, str(output_path))

    print(f"Data validated and saved to {output_path}. Ready for T021/T022.")

if __name__ == "__main__":
    main()
