"""
T025: Generate final dataset artifact.

Loads the engineered features dataset, selects and orders the required columns,
and saves the final dataset ready for modeling.
"""
import os
import sys
from pathlib import Path
from typing import Optional
import pandas as pd
import numpy as np

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import get_project_root


def load_engineered_data(input_path: str) -> pd.DataFrame:
    """Load the engineered features dataset."""
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file {input_path} not found. Run T024 first.")
    
    print(f"Loading engineered data from {input_path}...")
    df = pd.read_csv(input_path)
    print(f"Loaded dataset with {len(df)} rows and {len(df.columns)} columns.")
    return df


def enforce_column_selection(df: pd.DataFrame) -> pd.DataFrame:
    """Select and order the required columns for the final dataset."""
    required_columns = [
        'cold_work_pct',
        'Mn_wt',
        'Mg_wt',
        'Si_wt',
        'Cu_wt',
        'annealing_temp_K',
        'time_to_peak_min',
        'cold_work_Mn_content',
        'cold_work_Mg_content',
        'cold_work_Si_content',
        'cold_work_Cu_content'
    ]
    
    # Verify all required columns exist
    missing_cols = [col for col in required_columns if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in input: {missing_cols}")
    
    # Select and order columns
    final_df = df[required_columns].copy()
    
    # Verify no extra columns
    if len(final_df.columns) != len(required_columns):
        raise ValueError(f"Unexpected column count: expected {len(required_columns)}, got {len(final_df.columns)}")
    
    print(f"Selected and ordered {len(required_columns)} columns.")
    return final_df


def save_final_dataset(df: pd.DataFrame, output_path: str) -> None:
    """Save the final dataset to CSV."""
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
    
    df.to_csv(output_path, index=False)
    print(f"Saved final dataset to {output_path} with {len(df)} rows.")


def main():
    """Main entry point for T025."""
    project_root = get_project_root()
    input_path = os.path.join(project_root, "data", "processed", "engineered_features.csv")
    output_path = os.path.join(project_root, "data", "processed", "final_dataset.csv")
    
    print("Starting T025: Generate final dataset artifact...")
    
    # Load engineered data
    df = load_engineered_data(input_path)
    
    # Enforce column selection and ordering
    final_df = enforce_column_selection(df)
    
    # Save final dataset
    save_final_dataset(final_df, output_path)
    
    # Verification
    assert os.path.exists(output_path), f"Output file {output_path} was not created."
    final_df_check = pd.read_csv(output_path)
    assert list(final_df_check.columns) == [
        'cold_work_pct', 'Mn_wt', 'Mg_wt', 'Si_wt', 'Cu_wt', 
        'annealing_temp_K', 'time_to_peak_min', 
        'cold_work_Mn_content', 'cold_work_Mg_content', 
        'cold_work_Si_content', 'cold_work_Cu_content'
    ], "Column verification failed."
    
    print("T025 completed successfully.")


if __name__ == "__main__":
    main()
