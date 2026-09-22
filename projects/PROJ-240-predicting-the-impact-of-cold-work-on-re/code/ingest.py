"""
T017-T022: Data Ingestion Pipeline for Cold Work Recrystallization Study.

Implements:
- T017: Filter missing target
- T018: Physical bound validation
- T019: Impute missing composition
- T020: Unit normalization (minutes)
- T021: Outlier clipping
- T022: Orchestration
"""
import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
import pandas as pd
import numpy as np

from config import get_project_root, get_outlier_percentile, get_random_seed
from utils import validate_physical_bounds, normalize_time_to_minutes, impute_missing_composition, clip_outliers

# --- T020 Implementation: Unit Normalization ---
def normalize_time_units(df: pd.DataFrame) -> pd.DataFrame:
    """
    T020: Ensure 'time_to_peak_min' is in minutes.
    
    If the column contains values that appear to be in seconds (e.g., > 6000 for a 
    typical recrystallization process, or simply if a 'time_unit' column indicates 'seconds'),
    convert to minutes.
    
    For this synthetic baseline, we assume the input is already in minutes as per spec,
    but we perform a sanity check and conversion if a 'time_unit' column exists or 
    if values are suspiciously large (seconds).
    
    Args:
        df: Input DataFrame containing 'time_to_peak_min' (or similar).
    
    Returns:
        DataFrame with 'time_to_peak_min' normalized to minutes.
    """
    df = df.copy()
    
    # Check for a 'time_unit' column indicating seconds
    if 'time_unit' in df.columns:
        mask = df['time_unit'].astype(str).str.lower().str.contains('sec')
        if mask.any():
            # Convert seconds to minutes for those rows
            df.loc[mask, 'time_to_peak_min'] = df.loc[mask, 'time_to_peak_min'] / 60.0
            print(f"Converted {mask.sum()} rows from seconds to minutes.")
    
    # Fallback heuristic: If mean value > 1000, assume it might be seconds
    # (Recrystallization times are typically minutes, not thousands of minutes).
    # This is a defensive check for mixed sources.
    elif 'time_to_peak_min' in df.columns:
        mean_val = df['time_to_peak_min'].mean()
        if mean_val > 1000: 
            print(f"Warning: Mean time_to_peak is {mean_val:.2f}. Assuming input is in seconds and converting to minutes.")
            df['time_to_peak_min'] = df['time_to_peak_min'] / 60.0
    
    return df

# --- Helper Functions for Pipeline ---

def load_data(source_path: str) -> pd.DataFrame:
    """Load data from CSV."""
    if not os.path.exists(source_path):
        raise FileNotFoundError(f"Data source not found: {source_path}")
    return pd.read_csv(source_path)

def filter_missing_target(df: pd.DataFrame, target_col: str = 'time_to_peak_min') -> pd.DataFrame:
    """T017: Exclude rows with missing target."""
    initial_len = len(df)
    df = df.dropna(subset=[target_col])
    dropped = initial_len - len(df)
    if dropped > 0:
        print(f"T017: Dropped {dropped} rows with missing target.")
    return df

def validate_physical_bounds(df: pd.DataFrame) -> Tuple[pd.DataFrame, int]:
    """T018: Validate 0 <= cold_work <= 100 and time > 0."""
    initial_len = len(df)
    # Cold work
    mask_cw = (df['cold_work_pct'] >= 0) & (df['cold_work_pct'] <= 100)
    # Time
    mask_time = df['time_to_peak_min'] > 0
    
    valid_mask = mask_cw & mask_time
    dropped = initial_len - valid_mask.sum()
    
    if dropped > 0:
        print(f"T018: Dropped {dropped} rows violating physical bounds.")
        df = df[valid_mask].reset_index(drop=True)
    
    return df, dropped

def impute_missing_composition(df: pd.DataFrame) -> pd.DataFrame:
    """T019: Impute missing composition values with column mean."""
    composition_cols = ['Mn_wt', 'Mg_wt', 'Si_wt', 'Cu_wt']
    initial_nulls = df[composition_cols].isnull().sum().sum()
    
    if initial_nulls > 0:
        print(f"T019: Imputing {initial_nulls} missing composition values with column means.")
        for col in composition_cols:
            if col in df.columns:
                mean_val = df[col].mean()
                df[col] = df[col].fillna(mean_val)
    return df

def clip_outliers_target(df: pd.DataFrame, percentile: float) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """T021: Clip outliers on target variable."""
    target_col = 'time_to_peak_min'
    if target_col not in df.columns:
        raise ValueError(f"Target column '{target_col}' not found in dataset.")
    
    threshold = np.percentile(df[target_col], percentile, method='linear')
    original_max = df[target_col].max()
    
    # Identify rows to be clipped
    outlier_mask = df[target_col] > threshold
    clipped_indices = df.index[outlier_mask].tolist()
    clipped_count = len(clipped_indices)
    
    if clipped_count > 0:
        print(f"T021: Clipping {clipped_count} outliers (threshold={threshold:.2f}, max={original_max:.2f})")
        df.loc[df[target_col] > threshold, target_col] = threshold
    
    log_entry = {
        "clipped_outliers_count": clipped_count,
        "clipped_values_list": clipped_indices,
        "threshold_99th_percentile": float(threshold)
    }
    
    return df, log_entry

def validate_dataset_size(df: pd.DataFrame, min_rows: int = 50):
    """T022: Fail-fast if dataset too small."""
    if len(df) < min_rows:
        raise ValueError(f"Dataset size ({len(df)}) is below minimum threshold ({min_rows}) required for statistical validity (FR-008).")

# --- Main Orchestration (T022) ---

def run_ingestion_pipeline(input_path: str, output_path: str, metrics_path: str, validation_log_path: str):
    """
    Orchestrates the full ingestion pipeline:
    1. Load
    2. Filter missing target (T017)
    3. Validate bounds (T018)
    4. Impute composition (T019)
    5. Normalize units (T020)
    6. Clip outliers (T021)
    7. Validate size (T022)
    8. Save
    """
    print(f"Starting ingestion pipeline from {input_path}")
    
    # T022: Load Primary Source (Fail Fast if missing)
    try:
        df = load_data(input_path)
    except FileNotFoundError as e:
        raise RuntimeError(f"Primary data source missing: {input_path}. Cannot proceed.") from e
    
    rows_ingested = len(df)
    rows_dropped_nulls = 0
    rows_dropped_other = 0
    
    # T017: Filter missing target
    df = filter_missing_target(df)
    rows_dropped_nulls = rows_ingested - len(df)
    
    # T018: Validate bounds
    df, dropped_bounds = validate_physical_bounds(df)
    rows_dropped_other += dropped_bounds
    
    # T019: Impute composition
    df = impute_missing_composition(df)
    
    # T020: Normalize units
    df = normalize_time_units(df)
    
    # T021: Clip outliers
    outlier_percentile = get_outlier_percentile()
    df, outlier_log = clip_outliers_target(df, outlier_percentile)
    
    # T022: Validate size
    validate_dataset_size(df)
    
    # Save Output
    df.to_csv(output_path, index=False)
    print(f"Ingestion complete. Saved {len(df)} rows to {output_path}")
    
    # Update Metrics
    metrics = {
        "rows_ingested": rows_ingested,
        "rows_dropped_nulls": rows_dropped_nulls,
        "rows_dropped_other": rows_dropped_other,
        "rows_output": len(df),
        "null_handling_success_rate": (rows_ingested - rows_dropped_nulls) / rows_ingested if rows_ingested > 0 else 0.0
    }
    
    # Update Validation Log (Append/Overwrite as needed)
    validation_log = {
        "rows_ingested": rows_ingested,
        "rows_dropped_nulls": rows_dropped_nulls,
        "rows_dropped_other": rows_dropped_other,
        **outlier_log
    }
    
    # Ensure directories exist
    Path(metrics_path).parent.mkdir(parents=True, exist_ok=True)
    Path(validation_log_path).parent.mkdir(parents=True, exist_ok=True)
    
    with open(validation_log_path, 'w') as f:
        json.dump(validation_log, f, indent=2)
        
    with open(metrics_path, 'w') as f:
        json.dump(metrics, f, indent=2)

def main():
    """Entry point for T020/T022 execution."""
    project_root = get_project_root()
    
    # Paths
    # T022 expects to load 'clipped.csv' which is the output of T021.
    # However, the pipeline is sequential. 
    # According to T022 description: "Load data/processed/clipped.csv (from T021)".
    # Since T021 is part of this same script (run_ingestion_pipeline), we simulate the flow.
    # In a real multi-step runner, T021 would write to 'clipped.csv' and T022 would read it.
    # Here, we run the full chain and write to 'cleaned.csv' as the final output of ingestion.
    
    # To strictly follow T022: "Load data/processed/clipped.csv... Output: data/processed/cleaned.csv"
    # We will assume the input to this function is the raw data, and we perform T017-T021 internally,
    # then write the result to 'cleaned.csv'.
    # The 'clipped.csv' intermediate is implicit in the function flow if we were to split steps.
    # For this single-file implementation, we treat the input as the raw synthetic data.
    
    raw_data_path = str(project_root / "data" / "raw" / "synthetic_baseline.csv")
    output_path = str(project_root / "data" / "processed" / "cleaned.csv")
    metrics_path = str(project_root / "artifacts" / "reports" / "ingestion_metrics.json")
    validation_log_path = str(project_root / "artifacts" / "reports" / "validation_log.json")
    
    if not os.path.exists(raw_data_path):
        print(f"Error: Raw data not found at {raw_data_path}. Run T011 first.")
        sys.exit(1)
        
    run_ingestion_pipeline(
        input_path=raw_data_path,
        output_path=output_path,
        metrics_path=metrics_path,
        validation_log_path=validation_log_path
    )

if __name__ == "__main__":
    main()
