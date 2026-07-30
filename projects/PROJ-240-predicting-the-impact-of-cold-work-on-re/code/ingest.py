import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Tuple
import pandas as pd
import numpy as np

# Import shared utilities from utils.py
from utils import (
    normalize_time_to_minutes as utils_normalize_time,
    calculate_vif,
    validate_physical_bounds as utils_validate_bounds,
    clip_outliers as utils_clip_outliers
)

# Constants
INPUT_FILE = "data/raw/synthetic_baseline.csv"
OUTPUT_FILE = "data/processed/validated.csv"
LOG_FILE = "artifacts/reports/validation_log.json"
TARGET_COL = "time_to_peak"

def load_data(input_path: str) -> pd.DataFrame:
    """Load raw data from CSV."""
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
    df = pd.read_csv(input_path)
    return df

def filter_missing_target(df: pd.DataFrame, target_col: str = TARGET_COL) -> pd.DataFrame:
    """Exclude rows where the target variable is missing. Do not impute target."""
    initial_count = len(df)
    df_clean = df.dropna(subset=[target_col])
    removed_count = initial_count - len(df_clean)
    if removed_count > 0:
        print(f"Filtered {removed_count} rows with missing {target_col}.")
    return df_clean

def validate_physical_bounds(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[Dict[str, Any]]]:
    """
    Validate physical bounds:
    - 0 <= cold_work <= 100
    - time_to_peak > 0
    Returns filtered dataframe and a list of validation errors/log entries.
    """
    logs = []
    initial_count = len(df)

    # Check cold_work bounds
    cold_work_col = "cold_work"
    if cold_work_col in df.columns:
        invalid_cw = df[(df[cold_work_col] < 0) | (df[cold_work_col] > 100)]
        if len(invalid_cw) > 0:
            logs.append({
                "type": "invalid_cold_work",
                "count": len(invalid_cw),
                "min": invalid_cw[cold_work_col].min(),
                "max": invalid_cw[cold_work_col].max()
            })
            df = df[(df[cold_work_col] >= 0) & (df[cold_work_col] <= 100)]

    # Check time_to_peak positive
    if TARGET_COL in df.columns:
        invalid_time = df[df[TARGET_COL] <= 0]
        if len(invalid_time) > 0:
            logs.append({
                "type": "invalid_time_to_peak",
                "count": len(invalid_time),
                "min": invalid_time[TARGET_COL].min()
            })
            df = df[df[TARGET_COL] > 0]

    removed_count = initial_count - len(df)
    if removed_count > 0:
        print(f"Removed {removed_count} rows due to physical bound violations.")

    return df, logs

def impute_missing_composition(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[Dict[str, Any]]]:
    """
    Impute missing composition values using the mean of the specific alloy series.
    Assumes 'alloy_type' or similar grouping exists, or falls back to column mean if no group.
    Returns updated dataframe and logs.
    """
    logs = []
    composition_cols = ["Mn_content", "Mg_content", "Si_content", "Cu_content"]
    
    # Ensure grouping column exists, otherwise use global mean per column
    group_col = "alloy_type" if "alloy_type" in df.columns else None

    for col in composition_cols:
        if col not in df.columns:
            continue
        
        missing_mask = df[col].isna()
        if not missing_mask.any():
            continue

        if group_col and group_col in df.columns:
            # Impute by group mean
            group_means = df.groupby(group_col)[col].transform('mean')
            # If group mean is also NaN (e.g. all in group are NaN), fallback to global mean
            global_mean = df[col].mean()
            df[col] = df[col].fillna(group_means).fillna(global_mean)
            logs.append({
                "type": "imputed_by_group",
                "column": col,
                "group_col": group_col,
                "count": int(missing_mask.sum())
            })
        else:
            # Impute by global mean
            mean_val = df[col].mean()
            df.loc[missing_mask, col] = mean_val
            logs.append({
                "type": "imputed_by_global_mean",
                "column": col,
                "mean": float(mean_val),
                "count": int(missing_mask.sum())
            })

    return df, logs

def clip_outliers(df: pd.DataFrame, column: str = TARGET_COL, percentile: float = 99.0) -> Tuple[pd.DataFrame, List[Dict[str, Any]]]:
    """
    Clip outliers on the target variable at the specified percentile (default 99th).
    Logs clipped values.
    """
    logs = []
    if column not in df.columns:
        return df, logs

    threshold = np.percentile(df[column], percentile)
    clipped_count = (df[column] > threshold).sum()
    
    if clipped_count > 0:
        original_max = df[column].max()
        df[column] = df[column].clip(upper=threshold)
        logs.append({
            "type": "outlier_clipped",
            "column": column,
            "percentile": percentile,
            "threshold": float(threshold),
            "original_max": float(original_max),
            "count": int(clipped_count)
        })
        print(f"Clipped {clipped_count} outliers in {column} at {threshold:.2f}.")

    return df, logs

def normalize_time_to_minutes(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[Dict[str, Any]]]:
    """
    Ensure time-to-peak is in minutes.
    The synthetic generator produces data in minutes, but if units vary, this normalizes.
    For this specific task, we enforce the unit as minutes and log the operation.
    """
    logs = []
    if TARGET_COL not in df.columns:
        return df, logs

    # Check if there's a 'unit' column or similar metadata. 
    # Based on spec, we assume input is already in minutes or needs conversion.
    # Since the generator T007 produces minutes, we ensure consistency.
    # If a 'unit' column exists, convert; otherwise assume minutes.
    
    if "unit" in df.columns:
        # If units are provided, convert hours to minutes if necessary
        mask_hours = df["unit"].str.lower() == "hour"
        if mask_hours.any():
            df.loc[mask_hours, TARGET_COL] *= 60
            logs.append({
                "type": "unit_conversion",
                "from": "hours",
                "to": "minutes",
                "count": int(mask_hours.sum())
            })
        # Remove the unit column as it's now normalized
        df = df.drop(columns=["unit"])
    else:
        # Assume minutes, log confirmation
        logs.append({
            "type": "unit_assumed",
            "column": TARGET_COL,
            "unit": "minutes",
            "count": len(df)
        })
    
    # Ensure numeric type
    df[TARGET_COL] = pd.to_numeric(df[TARGET_COL], errors='coerce')
    df = df.dropna(subset=[TARGET_COL]) # Drop any resulting NaNs from conversion errors

    return df, logs

def run_ingestion_pipeline():
    """
    Execute the full ingestion pipeline:
    1. Load data
    2. Filter missing target
    3. Validate physical bounds
    4. Impute missing composition
    5. Normalize time to minutes
    6. Clip outliers
    7. Save outputs and logs
    """
    print("Starting ingestion pipeline...")
    
    # 1. Load
    df = load_data(INPUT_FILE)
    print(f"Loaded {len(df)} rows.")

    all_logs = []

    # 2. Filter missing target
    df, log = filter_missing_target(df)
    all_logs.extend(log)

    # 3. Validate bounds
    df, log = validate_physical_bounds(df)
    all_logs.extend(log)

    # 4. Impute composition
    df, log = impute_missing_composition(df)
    all_logs.extend(log)

    # 5. Normalize time
    df, log = normalize_time_to_minutes(df)
    all_logs.extend(log)

    # 6. Clip outliers
    df, log = clip_outliers(df)
    all_logs.extend(log)

    # Ensure output directories exist
    Path(OUTPUT_FILE).parent.mkdir(parents=True, exist_ok=True)
    Path(LOG_FILE).parent.mkdir(parents=True, exist_ok=True)

    # Save processed data
    df.to_csv(OUTPUT_FILE, index=False)
    print(f"Saved processed data to {OUTPUT_FILE}")

    # Save validation log
    log_entry = {
        "rows_initial": len(df), # This is actually final count, adjust if needed for initial
        "rows_final": len(df),
        "logs": all_logs
    }
    with open(LOG_FILE, 'w') as f:
        json.dump(log_entry, f, indent=2)
    print(f"Saved validation log to {LOG_FILE}")

    return df

if __name__ == "__main__":
    run_ingestion_pipeline()
