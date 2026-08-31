import os
import sys
from pathlib import Path
from typing import Optional
import pandas as pd
import numpy as np

def load_engineered_data(input_path: str) -> pd.DataFrame:
    """Load engineered features data."""
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
    return pd.read_csv(input_path)

def enforce_row_cap(df: pd.DataFrame, max_rows: int = 10000) -> pd.DataFrame:
    """Enforce a hard cap on the number of rows."""
    if len(df) > max_rows:
        print(f"Dataset size {len(df)} exceeds cap {max_rows}. Truncating.")
        return df.head(max_rows)
    return df

def save_final_dataset(df: pd.DataFrame, output_path: str):
    """Save the final dataset."""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"Saved final dataset to {output_path}")

def main():
    """Main entry point for finalization."""
    input_path = 'data/processed/engineered_features.csv'
    output_path = 'data/processed/final_dataset.csv'
    max_rows = 10000
    
    df = load_engineered_data(input_path)
    df = enforce_row_cap(df, max_rows)
    save_final_dataset(df, output_path)

if __name__ == "__main__":
    main()
