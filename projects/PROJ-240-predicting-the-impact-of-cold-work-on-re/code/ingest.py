import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Tuple
import pandas as pd
import numpy as np

from config import get_project_root, get_min_rows, get_max_rows, get_outlier_percentile

def load_data(source_path: str) -> pd.DataFrame:
    """
    Load the primary data source (synthetic_baseline.csv).
    This function does NOT attempt to fetch external data.
    """
    path = Path(source_path)
    if not path.exists():
        raise FileNotFoundError(f"Primary data source not found: {source_path}. "
                                "T006 (generate_synthetic) must run first.")
    
    df = pd.read_csv(path)
    return df

def validate_dataset_size(df: pd.DataFrame) -> None:
    """
    Enforce dataset size constraints (FR-003, FR-008).
    Raises ValueError if size is out of bounds.
    """
    n_rows = len(df)
    min_rows = get_min_rows()
    max_rows = get_max_rows()
    
    if n_rows < min_rows:
        raise ValueError(f"Dataset size ({n_rows}) is below minimum threshold ({min_rows}). "
                         f"Fail-fast triggered per FR-008.")
    if n_rows > max_rows:
        raise ValueError(f"Dataset size ({n_rows}) exceeds maximum allowed ({max_rows}). "
                         f"Data cap violated.")

def filter_missing_target(df: pd.DataFrame) -> pd.DataFrame:
    """
    Exclude rows where the target variable 'time_to_peak_min' is missing.
    Do NOT impute the target.
    """
    if 'time_to_peak_min' not in df.columns:
        raise ValueError("Target column 'time_to_peak_min' is missing from dataset.")
    
    initial_count = len(df)
    df = df.dropna(subset=['time_to_peak_min'])
    filtered_count = initial_count - len(df)
    return df, filtered_count

def validate_physical_bounds(df: pd.DataFrame) -> Tuple[pd.DataFrame, int]:
    """
    Validate physical bounds:
    - 0 <= cold_work_pct <= 100
    - time_to_peak_min > 0
    Returns filtered dataframe and count of excluded rows.
    """
    initial_count = len(df)
    
    # Filter cold_work_pct
    mask_cold_work = (df['cold_work_pct'] >= 0) & (df['cold_work_pct'] <= 100)
    
    # Filter time (must be positive)
    mask_time = df['time_to_peak_min'] > 0
    
    # Combine masks
    valid_mask = mask_cold_work & mask_time
    
    df_valid = df[valid_mask].copy()
    excluded_count = initial_count - len(df_valid)
    
    return df_valid, excluded_count

def impute_missing_composition(df: pd.DataFrame) -> Tuple[pd.DataFrame, int]:
    """
    Impute missing composition values (Mn, Mg, Si, Cu) using group means.
    Since we are using synthetic data which is deterministic, groups are defined
    by ranges of cold_work or simply the overall mean if no grouping is specified.
    For robustness, we group by 'cold_work_pct' bucketed into 10 bins to simulate
    alloy series if specific alloy types aren't present.
    """
    composition_cols = ['Mn_wt', 'Mg_wt', 'Si_wt', 'Cu_wt']
    missing_cols = [c for c in composition_cols if c in df.columns]
    
    if not missing_cols:
        return df, 0
    
    initial_null_count = df[missing_cols].isnull().sum().sum()
    if initial_null_count == 0:
        return df, 0
    
    # Create a dummy group based on cold_work_pct to simulate "alloy series"
    # This ensures we don't use a global mean for everything if the spec implies series.
    # If 'cold_work_pct' is missing, fallback to global mean.
    if 'cold_work_pct' in df.columns:
        df['temp_group'] = pd.cut(df['cold_work_pct'], bins=10, labels=False)
        group_col = 'temp_group'
    else:
        df['temp_group'] = 0
        group_col = 'temp_group'
    
    # Calculate mean per group
    means = df.groupby(group_col)[missing_cols].transform('mean')
    
    # Impute
    df[missing_cols] = df[missing_cols].fillna(means)
    
    # If still null (e.g., all NaN in a group), fill with global mean of that col
    global_means = df[missing_cols].mean()
    df[missing_cols] = df[missing_cols].fillna(global_means)
    
    # Clean up temp group
    df.drop(columns=[group_col], inplace=True)
    
    final_null_count = df[missing_cols].isnull().sum().sum()
    imputed_count = initial_null_count - final_null_count
    
    return df, imputed_count

def normalize_time_to_minutes(df: pd.DataFrame) -> pd.DataFrame:
    """
    Ensure time_to_peak_min is in minutes.
    If data source uses different units, conversion happens here.
    Assuming input is already in minutes per T006 schema, but we enforce type.
    """
    if 'time_to_peak_min' in df.columns:
        df['time_to_peak_min'] = pd.to_numeric(df['time_to_peak_min'], errors='coerce')
    return df

def clip_outliers(df: pd.DataFrame, percentile: float) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Clip outliers on the target variable at the specified percentile (default 99th).
    Logs clipped values and count.
    """
    if 'time_to_peak_min' not in df.columns:
        return df, {"clipped_outliers_count": 0, "clipped_values_list": []}
    
    threshold = df['time_to_peak_min'].quantile(percentile / 100.0)
    
    # Identify outliers
    outlier_mask = df['time_to_peak_min'] > threshold
    outlier_values = df.loc[outlier_mask, 'time_to_peak_min'].tolist()
    
    clipped_count = len(outlier_values)
    
    # Clip values
    df['time_to_peak_min'] = df['time_to_peak_min'].clip(upper=threshold)
    
    log_data = {
        "clipped_outliers_count": clipped_count,
        "clipped_values_list": outlier_values,
        "threshold_99th_percentile": float(threshold)
    }
    
    return df, log_data

def run_ingestion_pipeline(input_path: str, output_csv_path: str, output_json_path: str) -> None:
    """
    Orchestrate the full ingestion pipeline:
    1. Load data
    2. Validate size
    3. Filter missing target
    4. Validate physical bounds
    5. Impute composition
    6. Normalize time
    7. Clip outliers
    8. Save outputs
    """
    print(f"Starting ingestion pipeline for {input_path}...")
    
    # 1. Load
    df = load_data(input_path)
    print(f"Loaded {len(df)} rows.")
    
    # 2. Validate Size (Fail-Fast)
    validate_dataset_size(df)
    print("Dataset size validated.")
    
    # 3. Filter Missing Target
    df, filtered_count = filter_missing_target(df)
    print(f"Filtered {filtered_count} rows with missing target.")
    
    # 4. Validate Bounds
    df, bounds_excluded = validate_physical_bounds(df)
    print(f"Excluded {bounds_excluded} rows violating physical bounds.")
    
    # 5. Impute
    df, imputed_count = impute_missing_composition(df)
    print(f"Imputed {imputed_count} missing composition values.")
    
    # 6. Normalize
    df = normalize_time_to_minutes(df)
    
    # 7. Clip Outliers
    df, outlier_log = clip_outliers(df, get_outlier_percentile())
    print(f"Clipped {outlier_log['clipped_outliers_count']} outliers.")
    
    # 8. Save CSV
    Path(output_csv_path).parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_csv_path, index=False)
    print(f"Saved validated data to {output_csv_path}")
    
    # 8. Save JSON Log
    log_entry = {
        "rows_ingested": len(df) + filtered_count + bounds_excluded,
        "rows_filtered": filtered_count,
        "rows_excluded_by_bounds": bounds_excluded,
        "null_counts": 0, # Should be 0 after imputation
        "clipped_outliers_count": outlier_log['clipped_outliers_count'],
        "clipped_values_list": outlier_log['clipped_values_list'],
        "threshold_99th_percentile": outlier_log['threshold_99th_percentile']
    }
    
    Path(output_json_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_json_path, 'w') as f:
        json.dump(log_entry, f, indent=2)
    print(f"Saved validation log to {output_json_path}")

def main():
    """
    Entry point for the ingestion step.
    """
    root = get_project_root()
    input_file = root / "data" / "raw" / "synthetic_baseline.csv"
    output_csv = root / "data" / "processed" / "validated.csv"
    output_json = root / "artifacts" / "reports" / "validation_log.json"
    
    if not input_file.exists():
        print(f"Error: Input file {input_file} does not exist. Run T006 first.")
        sys.exit(1)
    
    try:
        run_ingestion_pipeline(str(input_file), str(output_csv), str(output_json))
    except ValueError as e:
        print(f"Validation Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Pipeline Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
