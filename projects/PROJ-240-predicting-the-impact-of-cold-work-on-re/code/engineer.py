import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Tuple
import pandas as pd
import numpy as np

def calculate_interaction_features(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate interaction features: cold_work * composition.
    
    Creates:
        cold_work_Mn: cold_work_pct * Mn_wt
        cold_work_Mg: cold_work_pct * Mg_wt
        cold_work_Si: cold_work_pct * Si_wt
        cold_work_Cu: cold_work_pct * Cu_wt
        
    Does NOT include cold_work * Temperature per FR-002.
    """
    df = df.copy()
    
    # Verify required columns exist
    required_cols = ['cold_work_pct', 'Mn_wt', 'Mg_wt', 'Si_wt', 'Cu_wt']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns for interaction features: {missing}")
    
    # Calculate interactions using exact column names from T007
    df['cold_work_Mn'] = df['cold_work_pct'] * df['Mn_wt']
    df['cold_work_Mg'] = df['cold_work_pct'] * df['Mg_wt']
    df['cold_work_Si'] = df['cold_work_pct'] * df['Si_wt']
    df['cold_work_Cu'] = df['cold_work_pct'] * df['Cu_wt']
    
    return df

def ensure_temperature_feature(df: pd.DataFrame) -> pd.DataFrame:
    """Ensure annealing temperature is present as a direct feature.
    
    Per T018: Include annealing temperature as a direct feature.
    Uses exact column name from T007: 'annealing_temp_K'.
    """
    if 'annealing_temp_K' not in df.columns:
        raise ValueError("annealing_temp_K column missing from input data. "
                       "Expected column name from T007 synthetic generator.")
    # Temperature is already present as a direct feature, no transformation needed
    return df

def validate_dataset_size(df: pd.DataFrame, min_rows: int = 50):
    """Raise ValueError if dataset has fewer than min_rows (FR-008)."""
    if len(df) < min_rows:
        raise ValueError(f"Dataset size {len(df)} is below minimum threshold of {min_rows}")

def run_engineering_pipeline(input_path: str, output_path: str):
    """Run the feature engineering pipeline.
    
    Loads validated data, calculates interaction features, ensures temperature
    is present, validates size, and saves to output path.
    """
    print(f"Loading data from {input_path}...")
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}. "
                              "Ensure T012 (ingest.py) has run successfully.")
    df = pd.read_csv(input_path)
    
    print(f"Loaded {len(df)} rows. Validating dataset size...")
    validate_dataset_size(df)
    
    print("Ensuring temperature feature is present...")
    df = ensure_temperature_feature(df)
    
    print("Calculating interaction features (cold_work * composition)...")
    df = calculate_interaction_features(df)
    
    # Ensure output directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    # Save output
    df.to_csv(output_path, index=False)
    print(f"Saved engineered features to {output_path}")
    print(f"Output columns: {list(df.columns)}")
    return df

def main():
    """Main entry point for engineering pipeline (T018)."""
    input_path = 'data/processed/validated.csv'
    output_path = 'data/processed/engineered_features.csv'
    run_engineering_pipeline(input_path, output_path)

if __name__ == "__main__":
    main()