"""
T024: Interaction feature engineering.
Calculates cold_work * Mn_content, etc., and saves engineered_features.csv.
Implements T050: Chunked data loading for large files (>5MB).
"""
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Tuple
import pandas as pd
import numpy as np

from config import get_project_root, get_max_rows

def load_data_chunked(input_path: str, chunksize: int = 1000) -> pd.DataFrame:
    """
    Load data, optionally in chunks if file size > 5MB to reduce memory peak.
    T050 Implementation:
    1. Check file size.
    2. If > 5MB, read in chunks and concatenate.
    3. If <= 5MB, read directly.
    """
    file_path = Path(input_path)
    if not file_path.exists():
        raise FileNotFoundError(f"Input file {input_path} not found.")
    
    file_size_bytes = file_path.stat().st_size
    file_size_mb = file_size_bytes / (1024 * 1024)
    
    if file_size_mb > 5.0:
        print(f"File size ({file_size_mb:.2f} MB) > 5MB. Loading in chunks of {chunksize}...")
        chunks = []
        for chunk in pd.read_csv(input_path, chunksize=chunksize):
            chunks.append(chunk)
        df = pd.concat(chunks, ignore_index=True)
        print(f"Loaded {len(df)} rows in chunks.")
    else:
        print(f"File size ({file_size_mb:.2f} MB) <= 5MB. Loading directly.")
        df = pd.read_csv(input_path)
    
    return df

def calculate_interaction_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate interaction features: cold_work * Mn, Mg, Si, Cu.
    Does NOT include cold_work * Temperature.
    """
    df = df.copy()
    
    # Interaction terms
    df['cold_work_Mn_content'] = df['cold_work_pct'] * df['Mn_wt']
    df['cold_work_Mg_content'] = df['cold_work_pct'] * df['Mg_wt']
    df['cold_work_Si_content'] = df['cold_work_pct'] * df['Si_wt']
    df['cold_work_Cu_content'] = df['cold_work_pct'] * df['Cu_wt']
    
    return df

def ensure_temperature_feature(df: pd.DataFrame) -> pd.DataFrame:
    """Ensure annealing_temp_K is present as a standalone feature."""
    if 'annealing_temp_K' not in df.columns:
        raise ValueError("Missing 'annealing_temp_K' column. Required as standalone feature.")
    return df

def validate_dataset_size(df: pd.DataFrame) -> pd.DataFrame:
    """Enforce max rows cap."""
    max_rows = get_max_rows()
    if len(df) > max_rows:
        print(f"Warning: Dataset size ({len(df)}) exceeds cap ({max_rows}). Truncating.")
        df = df.iloc[:max_rows].reset_index(drop=True)
    return df

def run_engineering_pipeline():
    """Main orchestration for T024."""
    project_root = get_project_root()
    input_path = project_root / "data" / "processed" / "validated.csv"
    output_path = project_root / "data" / "processed" / "engineered_features.csv"
    
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file {input_path} not found. Run T022 first.")
    
    print("Starting engineering pipeline...")
    
    # Load with T050 chunked logic
    df = load_data_chunked(str(input_path))
    
    # Validate size
    df = validate_dataset_size(df)
    
    # Ensure temperature
    df = ensure_temperature_feature(df)
    
    # Calculate interactions
    df = calculate_interaction_features(df)
    
    # Save
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"Engineered features saved to {output_path}")

def main():
    run_engineering_pipeline()

if __name__ == "__main__":
    main()
