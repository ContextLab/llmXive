"""
T025: Generate final dataset artifact data/processed/final_dataset.csv ready for modeling.
Dependency: T024 (engineer.py)

This script loads the engineered features, enforces any row caps defined in config,
and saves the final dataset to data/processed/final_dataset.csv.
"""
import os
import sys
from pathlib import Path
from typing import Optional
import pandas as pd
import numpy as np

# Import shared config
from config import get_project_root, get_max_rows

def load_engineered_data(input_path: Optional[str] = None) -> pd.DataFrame:
    """Load the engineered features dataset."""
    project_root = get_project_root()
    if input_path is None:
        input_path = project_root / "data" / "processed" / "engineered_features.csv"
    
    if not os.path.exists(input_path):
        raise FileNotFoundError(
            f"Engineered features file not found at {input_path}. "
            "Please ensure T024 (engineer.py) has been executed successfully."
        )
    
    # Use chunked loading if file is large, though for final dataset we assume it fits in memory
    # unless specified otherwise. We use na_filter=True for safety.
    df = pd.read_csv(input_path, na_filter=True)
    return df

def enforce_row_cap(df: pd.DataFrame, max_rows: Optional[int] = None) -> pd.DataFrame:
    """
    Enforce a hard cap on the number of rows if specified.
    Returns the capped DataFrame.
    """
    if max_rows is None:
        max_rows = get_max_rows()
    
    if df.shape[0] > max_rows:
        print(f"Dataset size ({df.shape[0]}) exceeds cap ({max_rows}). Capping...")
        # Deterministic slicing based on index to ensure reproducibility
        df = df.iloc[:max_rows].reset_index(drop=True)
    return df

def save_final_dataset(df: pd.DataFrame, output_path: Optional[str] = None) -> str:
    """Save the final dataset to CSV."""
    project_root = get_project_root()
    if output_path is None:
        output_path = project_root / "data" / "processed" / "final_dataset.csv"
    
    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save to CSV
    df.to_csv(output_path, index=False)
    print(f"Final dataset saved to {output_path} with {len(df)} rows.")
    return str(output_path)

def main():
    """Main entry point for T025."""
    print("Starting T025: Generate final dataset artifact...")
    
    try:
        # 1. Load engineered data (from T024)
        df = load_engineered_data()
        print(f"Loaded {len(df)} rows from engineered features.")
        
        # 2. Enforce row cap (FR-003 compliance)
        max_rows = get_max_rows()
        df = enforce_row_cap(df, max_rows)
        
        # 3. Validate no nulls in critical columns (optional safety check)
        # The spec implies data should be clean by this stage, but we check.
        critical_cols = ['cold_work_pct', 'Mn_wt', 'Mg_wt', 'Si_wt', 'Cu_wt', 
                         'annealing_temp_K', 'time_to_peak_min',
                         'cold_work_Mn_content', 'cold_work_Mg_content', 
                         'cold_work_Si_content', 'cold_work_Cu_content']
        
        missing_cols = [c for c in critical_cols if c not in df.columns]
        if missing_cols:
            raise ValueError(f"Missing critical columns in final dataset: {missing_cols}")
        
        null_counts = df[critical_cols].isnull().sum()
        if null_counts.any():
            raise ValueError(f"Null values found in critical columns:\n{null_counts[null_counts > 0]}")
        
        # 4. Save final dataset
        output_path = save_final_dataset(df)
        
        print("T025 completed successfully.")
        
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except ValueError as e:
        print(f"Validation Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
