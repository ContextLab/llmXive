"""
Finalize the dataset for modeling.

This script loads the engineered features, enforces row limits,
and saves the final dataset ready for model training.
"""
import os
import sys
from pathlib import Path
from typing import Optional
import pandas as pd
import numpy as np

from config import get_project_root, get_max_rows

def load_engineered_data() -> pd.DataFrame:
    """
    Load the engineered features dataset.
    
    Returns:
        pd.DataFrame: The engineered features dataset.
    
    Raises:
        FileNotFoundError: If the engineered features file does not exist.
    """
    project_root = get_project_root()
    input_path = project_root / "data" / "processed" / "engineered_features.csv"
    
    if not input_path.exists():
        raise FileNotFoundError(f"Engineered features file not found: {input_path}")
    
    return pd.read_csv(input_path)

def enforce_row_cap(df: pd.DataFrame, max_rows: Optional[int] = None) -> pd.DataFrame:
    """
    Enforce the maximum row cap on the dataset.
    
    Args:
        df: The input DataFrame.
        max_rows: The maximum number of rows allowed. If None, uses config value.
    
    Returns:
        pd.DataFrame: The DataFrame capped at max_rows.
    """
    if max_rows is None:
        max_rows = get_max_rows()
    
    if len(df) > max_rows:
        print(f"Dataset has {len(df)} rows, capping to {max_rows}.")
        return df.head(max_rows)
    
    return df

def save_final_dataset(df: pd.DataFrame, output_path: Optional[Path] = None) -> Path:
    """
    Save the final dataset to CSV.
    
    Args:
        df: The final dataset DataFrame.
        output_path: The output path. If None, uses default project path.
    
    Returns:
        Path: The path to the saved file.
    """
    if output_path is None:
        project_root = get_project_root()
        output_path = project_root / "data" / "processed" / "final_dataset.csv"
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    df.to_csv(output_path, index=False)
    print(f"Final dataset saved to {output_path} with {len(df)} rows.")
    return output_path

def main():
    """
    Main entry point for the finalize dataset pipeline.
    """
    try:
        # Load engineered data
        df = load_engineered_data()
        
        # Enforce row cap
        df_capped = enforce_row_cap(df)
        
        # Save final dataset
        save_final_dataset(df_capped)
        
        print("Finalize dataset pipeline completed successfully.")
        return 0
    except Exception as e:
        print(f"Error in finalize dataset pipeline: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
