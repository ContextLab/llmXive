import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Tuple
import pandas as pd
import numpy as np

def calculate_interaction_features(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate interaction features: cold_work * composition."""
    df = df.copy()
    interaction_cols = [
        'cold_work_Mn', 'cold_work_Mg', 'cold_work_Si', 'cold_work_Cu'
    ]
    composition_cols = ['Mn_content', 'Mg_content', 'Si_content', 'Cu_content']
    
    for int_col, comp_col in zip(interaction_cols, composition_cols):
        df[int_col] = df['cold_work'] * df[comp_col]
    
    return df

def ensure_temperature_feature(df: pd.DataFrame) -> pd.DataFrame:
    """Ensure annealing temperature is present as a feature."""
    if 'annealing_temp' not in df.columns:
        raise ValueError("annealing_temp column missing from input data")
    return df

def validate_dataset_size(df: pd.DataFrame, min_rows: int = 50):
    """Raise ValueError if dataset has fewer than min_rows."""
    if len(df) < min_rows:
        raise ValueError(f"Dataset size {len(df)} is below minimum threshold of {min_rows}")

def run_engineering_pipeline(input_path: str, output_path: str):
    """Run the feature engineering pipeline."""
    print(f"Loading data from {input_path}...")
    df = pd.read_csv(input_path)
    
    print("Validating dataset size...")
    validate_dataset_size(df)
    
    print("Ensuring temperature feature...")
    df = ensure_temperature_feature(df)
    
    print("Calculating interaction features...")
    df = calculate_interaction_features(df)
    
    # Ensure output directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    # Save output
    df.to_csv(output_path, index=False)
    print(f"Saved engineered features to {output_path}")
    return df

def main():
    """Main entry point for engineering."""
    input_path = 'data/processed/validated.csv'
    output_path = 'data/processed/engineered_features.csv'
    run_engineering_pipeline(input_path, output_path)

if __name__ == "__main__":
    main()
