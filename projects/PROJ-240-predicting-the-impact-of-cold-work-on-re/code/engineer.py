"""
Feature Engineering Pipeline (T019).
Calculates interaction features and ensures temperature is present.
Implements chunked loading for large files (T044).
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
        raise ValueError("annealing_temp_K is missing from the dataset. It must be present as a direct feature.")
    
    df['annealing_temp_K'] = pd.to_numeric(df['annealing_temp_K'], errors='coerce')
    return df

def validate_dataset_size(df: pd.DataFrame):
    """Check dataset size (T019 constraint)."""
    if len(df) > 10000:
        raise ValueError(f"Dataset size ({len(df)}) exceeds cap of 10000 rows.")

def load_data_chunked(input_path: Path) -> pd.DataFrame:
    """
    Load data using chunked reading if file size > 5MB (T044).
    """
    file_size_bytes = input_path.stat().st_size
    file_size_mb = file_size_bytes / (1024 * 1024)
    
    print(f"Input file size: {file_size_mb:.2f} MB")
    
    if file_size_mb > 5.0:
        print("File size > 5MB. Using chunked loading (chunksize=1000).")
        chunks = []
        for chunk in pd.read_csv(input_path, chunksize=1000):
            chunks.append(chunk)
        df = pd.concat(chunks, ignore_index=True)
    else:
        print("File size <= 5MB. Loading directly.")
        df = pd.read_csv(input_path)
        
    return df

def run_engineering_pipeline():
    """
    Orchestrate engineering pipeline (T019).
    Implements chunked loading (T044).
    """
    project_root = get_project_root()
    input_path = project_root / "data" / "processed" / "validated.csv"
    output_path = project_root / "data" / "processed" / "engineered_features.csv"

    if not input_path.exists():
        raise FileNotFoundError(f"Input data not found: {input_path}. Run T013-T018 first.")

    # Load with chunking logic (T044)
    df = load_data_chunked(input_path)
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
