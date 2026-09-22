"""
T025: Generate final dataset artifact.

Loads the engineered dataset, enforces the row cap (if necessary),
and saves the final dataset ready for modeling to:
data/processed/final_dataset.csv
"""
import os
import sys
from pathlib import Path
from typing import Optional
import pandas as pd
import numpy as np

# Import local config utilities
from config import get_project_root, get_config_value

def load_engineered_data() -> pd.DataFrame:
    """
    Load the engineered features dataset from T024.
    Path: data/processed/engineered_features.csv
    """
    project_root = get_project_root()
    input_path = project_root / "data" / "processed" / "engineered_features.csv"
    
    if not input_path.exists():
        raise FileNotFoundError(
            f"Engineered dataset not found at {input_path}. "
            "Please ensure T024 (engineer.py) has completed successfully."
        )
    
    # Read with explicit dtype enforcement and na_filter for sanitization
    df = pd.read_csv(
        input_path,
        dtype={
            'cold_work_pct': float,
            'Mn_wt': float,
            'Mg_wt': float,
            'Si_wt': float,
            'Cu_wt': float,
            'annealing_temp_K': float,
            'time_to_peak_min': float,
            'cold_work_Mn_content': float,
            'cold_work_Mg_content': float,
            'cold_work_Si_content': float,
            'cold_work_Cu_content': float
        },
        na_filter=True
    )
    
    return df

def enforce_row_cap(df: pd.DataFrame) -> pd.DataFrame:
    """
    Enforce the maximum row count constraint if the dataset is too large.
    If rows > N_ROWS_TARGET, sample deterministically.
    """
    n_rows_target = get_config_value("N_ROWS_TARGET", default=10000)
    
    if len(df) > n_rows_target:
        # Deterministic sampling to ensure reproducibility
        seed = get_config_value("SEED", default=42)
        np.random.seed(seed)
        indices = np.random.choice(df.index, size=n_rows_target, replace=False)
        df_sampled = df.loc[indices].reset_index(drop=True)
        print(f"Dataset size {len(df)} exceeds cap {n_rows_target}. "
              f"Sampled {n_rows_target} rows deterministically.")
        return df_sampled
    
    print(f"Dataset size {len(df)} is within cap {n_rows_target}.")
    return df

def save_final_dataset(df: pd.DataFrame) -> Path:
    """
    Save the final processed dataset to the declared output path.
    Path: data/processed/final_dataset.csv
    """
    project_root = get_project_root()
    output_dir = project_root / "data" / "processed"
    output_path = output_dir / "final_dataset.csv"
    
    # Ensure directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Write to disk
    df.to_csv(output_path, index=False)
    
    print(f"Final dataset saved to: {output_path}")
    print(f"Shape: {df.shape}")
    print(f"Columns: {list(df.columns)}")
    
    return output_path

def main():
    """
    Main entry point for T025.
    """
    try:
        # 1. Load engineered data
        print("Loading engineered dataset...")
        df = load_engineered_data()
        
        # 2. Enforce row cap if necessary
        print("Checking dataset size...")
        df_final = enforce_row_cap(df)
        
        # 3. Save final dataset
        print("Saving final dataset...")
        output_path = save_final_dataset(df_final)
        
        print(f"Task T025 completed successfully. Output: {output_path}")
        
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error during finalization: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
