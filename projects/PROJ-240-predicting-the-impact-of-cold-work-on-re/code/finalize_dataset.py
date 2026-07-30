"""
T020: Generate final dataset artifact ready for modeling.

This script loads the engineered features from data/processed/engineered_features.csv,
enforces a hard row cap (max 10,000 rows as per FR-003), and writes the final
dataset to data/processed/final_dataset.csv.

Prerequisites:
- T018 (engineer.py) must have generated data/processed/engineered_features.csv
- T019 (engineer.py) must have validated dataset size >= 50 rows
"""
import os
import sys
from pathlib import Path
from typing import Optional
import pandas as pd
import numpy as np

# Constants
MAX_ROWS = 10000
INPUT_PATH = Path("data/processed/engineered_features.csv")
OUTPUT_PATH = Path("data/processed/final_dataset.csv")
MIN_ROWS = 50  # Enforced by T019, but good to re-check

def load_engineered_data() -> pd.DataFrame:
    """Load the engineered features dataset."""
    if not INPUT_PATH.exists():
        raise FileNotFoundError(
            f"Input file not found: {INPUT_PATH}. "
            "Please run code/engineer.py first to generate engineered features."
        )
    
    df = pd.read_csv(INPUT_PATH)
    return df

def enforce_row_cap(df: pd.DataFrame, max_rows: int) -> pd.DataFrame:
    """
    Enforce a hard cap on the number of rows.
    
    If the dataset exceeds max_rows, we take the first max_rows rows.
    Since the synthetic data is deterministic (seed=42), taking the first
    N rows is a valid sampling strategy that preserves the distribution.
    
    Args:
        df: Input DataFrame
        max_rows: Maximum number of rows allowed
        
    Returns:
        DataFrame with at most max_rows rows
    """
    if len(df) > max_rows:
        print(f"Dataset has {len(df)} rows. Truncating to {max_rows} rows.")
        return df.head(max_rows).reset_index(drop=True)
    
    if len(df) < MIN_ROWS:
        raise ValueError(
            f"Dataset has {len(df)} rows, which is below the minimum required "
            f"({MIN_ROWS}) for statistical validity."
        )
        
    return df

def save_final_dataset(df: pd.DataFrame, output_path: Path) -> None:
    """Save the final dataset to CSV."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"Final dataset saved to: {output_path}")
    print(f"Final dataset shape: {df.shape}")
    print(f"Columns: {list(df.columns)}")

def main() -> int:
    """Main entry point for the final dataset generation."""
    print("Starting T020: Final Dataset Generation")
    print("=" * 50)
    
    # Load engineered data
    print(f"Loading engineered data from: {INPUT_PATH}")
    df = load_engineered_data()
    print(f"Loaded {len(df)} rows")
    
    # Enforce row cap
    print(f"Enforcing row cap of {MAX_ROWS} rows...")
    df_final = enforce_row_cap(df, MAX_ROWS)
    
    # Ensure no nulls (should have been handled in earlier steps, but verify)
    null_counts = df_final.isnull().sum()
    if null_counts.any():
        raise ValueError(
            f"Final dataset contains null values:\n{null_counts[null_counts > 0]}"
        )
    
    # Save final dataset
    print(f"Saving final dataset to: {OUTPUT_PATH}")
    save_final_dataset(df_final, OUTPUT_PATH)
    
    print("=" * 50)
    print("T020 completed successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())