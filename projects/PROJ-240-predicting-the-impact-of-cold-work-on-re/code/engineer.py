"""
Feature Engineering Pipeline (T019).
Calculates interaction features and ensures temperature is present.
"""
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Tuple
import pandas as pd
import numpy as np

# Ensure project root is in path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from config import get_project_root

def calculate_interaction_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate interaction features: cold_work * Mn, Mg, Si, Cu.
    Do NOT include cold_work * Temperature.
    """
    df = df.copy()
    
    interaction_features = []
    
    if 'cold_work_pct' in df.columns:
        if 'Mn_wt' in df.columns:
            col_name = "cold_work_Mn_interaction"
            df[col_name] = df['cold_work_pct'] * df['Mn_wt']
            interaction_features.append(col_name)
        
        if 'Mg_wt' in df.columns:
            col_name = "cold_work_Mg_interaction"
            df[col_name] = df['cold_work_pct'] * df['Mg_wt']
            interaction_features.append(col_name)
        
        if 'Si_wt' in df.columns:
            col_name = "cold_work_Si_interaction"
            df[col_name] = df['cold_work_pct'] * df['Si_wt']
            interaction_features.append(col_name)
        
        if 'Cu_wt' in df.columns:
            col_name = "cold_work_Cu_interaction"
            df[col_name] = df['cold_work_pct'] * df['Cu_wt']
            interaction_features.append(col_name)
    else:
        print("Warning: 'cold_work_pct' not found. Skipping interaction features.")

    print(f"Added interaction features: {interaction_features}")
    return df

def ensure_temperature_feature(df: pd.DataFrame) -> pd.DataFrame:
    """
    Ensure annealing_temp_K is present as a direct feature (T019).
    """
    if 'annealing_temp_K' not in df.columns:
        # If missing, we might need to generate or raise error.
        # Assuming it exists in the input from T006.
        raise ValueError("annealing_temp_K is missing from the dataset. It must be present as a direct feature.")
    
    # If it exists, ensure it's numeric
    df['annealing_temp_K'] = pd.to_numeric(df['annealing_temp_K'], errors='coerce')
    return df

def validate_dataset_size(df: pd.DataFrame):
    """Check dataset size (T019 constraint)."""
    if len(df) > 10000:
        raise ValueError(f"Dataset size ({len(df)}) exceeds cap of 10000 rows.")

def run_engineering_pipeline():
    """
    Orchestrate engineering pipeline (T019).
    """
    project_root = get_project_root()
    input_path = project_root / "data" / "processed" / "validated.csv"
    output_path = project_root / "data" / "processed" / "engineered_features.csv"

    if not input_path.exists():
        raise FileNotFoundError(f"Input data not found: {input_path}. Run T013-T018 first.")

    # Load
    df = pd.read_csv(input_path)
    print(f"Loaded {len(df)} rows for engineering.")

    # Validate Size
    validate_dataset_size(df)

    # Ensure Temperature
    df = ensure_temperature_feature(df)

    # Calculate Interactions
    df = calculate_interaction_features(df)

    # Save
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"Saved engineered features to {output_path}")

    return df

def main():
    try:
        run_engineering_pipeline()
    except Exception as e:
        print(f"Error in engineering pipeline: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
