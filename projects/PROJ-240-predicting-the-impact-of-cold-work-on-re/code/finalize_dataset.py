"""
Finalize the dataset for modeling.

This script loads the engineered features, enforces the row cap,
and saves the final dataset artifact.
"""
import os
import sys
from pathlib import Path
from typing import Optional
import pandas as pd
import numpy as np

from config import get_project_root, get_max_rows, get_random_seed

def load_engineered_data(input_path: str) -> pd.DataFrame:
    """
    Load the engineered features dataset.

    Args:
        input_path: Path to the engineered features CSV.

    Returns:
        DataFrame with engineered features.
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Engineered features file not found: {input_path}")
    
    df = pd.read_csv(input_path)
    return df

def enforce_row_cap(df: pd.DataFrame, max_rows: Optional[int] = None) -> pd.DataFrame:
    """
    Enforce the maximum row cap on the dataset.

    Args:
        df: Input DataFrame.
        max_rows: Maximum number of rows allowed.

    Returns:
        DataFrame with enforced row cap.
    """
    if max_rows is None:
        max_rows = get_max_rows()
    
    if len(df) > max_rows:
        print(f"Dataset has {len(df)} rows. Applying cap of {max_rows} rows.")
        # Use a deterministic seed for reproducibility
        np.random.seed(get_random_seed())
        indices = np.random.choice(len(df), max_rows, replace=False)
        df = df.iloc[indices].reset_index(drop=True)
    
    return df

def save_final_dataset(df: pd.DataFrame, output_path: str) -> None:
    """
    Save the final dataset to CSV.

    Args:
        df: DataFrame to save.
        output_path: Path to save the final dataset.
    """
    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    df.to_csv(output_path, index=False)
    print(f"Final dataset saved to {output_path} with {len(df)} rows.")

def main():
    """Main entry point for finalizing the dataset."""
    project_root = get_project_root()
    
    # Define paths
    input_path = project_root / "data" / "processed" / "engineered_features.csv"
    output_path = project_root / "data" / "processed" / "final_dataset.csv"
    
    # Load engineered data
    print(f"Loading engineered features from {input_path}...")
    df = load_engineered_data(str(input_path))
    
    # Enforce row cap
    df = enforce_row_cap(df)
    
    # Save final dataset
    save_final_dataset(df, str(output_path))
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
