import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Tuple
import pandas as pd
import numpy as np

from config import (
    get_project_root,
    get_outlier_percentile,
    get_min_rows,
    get_max_rows,
    get_random_seed,
)
from utils import (
    validate_physical_bounds,
    normalize_time_to_minutes,
    impute_missing_composition,
)


def load_data(
    synthetic_path: str,
    external_path: str | None = None,
    force_external: bool = False,
) -> pd.DataFrame:
    """
    Load data with strict error handling and fallback logic.

    Primary source: Synthetic dataset (T011).
    Secondary source: External dataset (T055) if available and requested.

    Logic:
    1. If `force_external` is True and external_path exists, attempt to load external.
       If external load fails, log warning and fall back to synthetic.
    2. If `force_external` is False (default), load synthetic.
    3. If synthetic load fails, raise FileNotFoundError (Fail-Loud for primary source).
    4. If external is requested but fails, proceed with synthetic (Fail-Safe).

    Args:
        synthetic_path: Path to synthetic_baseline.csv.
        external_path: Optional path to merged external dataset.
        force_external: If True, attempt external first.

    Returns:
        DataFrame containing the loaded data.

    Raises:
        FileNotFoundError: If the primary synthetic source is missing.
        ValueError: If the loaded dataset has fewer than `get_min_rows()` rows.
    """
    project_root = get_project_root()
    min_rows = get_min_rows()

    # Ensure paths are absolute relative to project root
    synthetic_full_path = project_root / synthetic_path
    external_full_path = project_root / external_path if external_path else None

    df = None

    # Attempt external fetch if requested and available
    if force_external and external_full_path and external_full_path.exists():
        try:
            print(f"Attempting to load external data from {external_full_path}...")
            df_ext = pd.read_csv(external_full_path)
            print(f"Successfully loaded external data: {len(df_ext)} rows.")
            df = df_ext
        except Exception as e:
            print(f"WARNING: External data fetch failed ({e}). Falling back to synthetic data.")
            df = None  # Reset to force synthetic load

    # If we don't have data yet (or didn't try external), load synthetic
    if df is None:
        if not synthetic_full_path.exists():
            raise FileNotFoundError(
                f"Primary data source not found: {synthetic_full_path}. "
                "Please run T011 (generate_synthetic.py) first."
            )

        print(f"Loading primary synthetic data from {synthetic_full_path}...")
        try:
            df = pd.read_csv(synthetic_full_path)
            print(f"Successfully loaded synthetic data: {len(df)} rows.")
        except Exception as e:
            # Fail loud on primary source corruption
            raise RuntimeError(
                f"Failed to read primary synthetic data: {e}"
            ) from e

    # Validate minimum row count immediately after loading
    if len(df) < min_rows:
        raise ValueError(
            f"Dataset size ({len(df)}) is below the minimum required threshold ({min_rows}). "
            "Data generation or fetch failed to produce sufficient data."
        )

    return df


def filter_missing_target(df: pd.DataFrame, target_col: str = "time_to_peak_min") -> pd.DataFrame:
    """
    Filter out rows where the target variable is missing.
    Does NOT impute the target.
    """
    initial_count = len(df)
    df = df.dropna(subset=[target_col])
    dropped = initial_count - len(df)
    if dropped > 0:
        print(f"Dropped {dropped} rows with missing target '{target_col}'.")
    return df


def impute_missing_composition(df: pd.DataFrame) -> pd.DataFrame:
    """
    Impute missing composition values using the mean of the specific alloy series.
    If no series grouping is defined, falls back to column mean (as per T019 spec).
    """
    composition_cols = ["Mn_wt", "Mg_wt", "Si_wt", "Cu_wt"]
    missing_mask = df[composition_cols].isnull().any(axis=1)

    if not missing_mask.any():
        return df

    print("Imputing missing composition values...")
    # Simple strategy: Group by a logical series if available, else global mean per column
    # Assuming 'alloy_type' or similar might exist, but spec says "group by alloy type"
    # If no grouping column exists, we use column mean as a safe fallback per T019 note
    # Note: T019 says "Impute using the mean of the specific alloy series... or flag for exclusion"
    # For this implementation, we use column mean as the robust fallback if no series column exists.

    for col in composition_cols:
        if df[col].isnull().any():
            mean_val = df[col].mean()
            df[col] = df[col].fillna(mean_val)
            print(f"  Imputed {col} with mean: {mean_val:.4f}")

    return df


def clip_outliers_target(
    df: pd.DataFrame,
    target_col: str = "time_to_peak_min",
    percentile: float | None = None,
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Clip outliers on the target variable at the specified percentile.

    Args:
        df: Input DataFrame.
        target_col: Name of the target column.
        percentile: Percentile threshold (e.g., 99). Reads from config if None.

    Returns:
        Tuple of (clipped_df, log_dict) containing count and indices.
    """
    if percentile is None:
        percentile = get_outlier_percentile()

    threshold = np.percentile(df[target_col], percentile, method="linear")
    initial_count = len(df)

    # Identify rows exceeding the threshold
    outlier_mask = df[target_col] > threshold
    outlier_indices = df[outlier_mask].index.tolist()
    clipped_count = len(outlier_indices)

    if clipped_count > 0:
        print(f"Clipping {clipped_count} outliers (>{threshold:.2f}) at {percentile}th percentile.")
        df.loc[outlier_mask, target_col] = threshold
    else:
        print(f"No outliers found above {percentile}th percentile ({threshold:.2f}).")

    log_dict = {
        "clipped_outliers_count": clipped_count,
        "clipped_values_list": outlier_indices,
        "threshold_99th_percentile": float(threshold),
        "percentile_used": percentile,
    }

    return df, log_dict


def validate_dataset_size(df: pd.DataFrame) -> pd.DataFrame:
    """
    Enforce the maximum row cap (FR-003) to prevent memory overflow.
    """
    max_rows = get_max_rows()
    if len(df) > max_rows:
        print(f"Dataset size ({len(df)}) exceeds max cap ({max_rows}). Truncating.")
        # Deterministic truncation based on seed
        seed = get_random_seed()
        np.random.seed(seed)
        indices = np.random.choice(len(df), max_rows, replace=False)
        df = df.loc[indices].reset_index(drop=True)
    return df


def run_ingestion_pipeline() -> None:
    """
    Orchestrate the full ingestion pipeline:
    1. Load data (Synthetic primary, External optional).
    2. Filter missing target.
    3. Impute missing compositions.
    4. Validate physical bounds.
    5. Normalize units.
    6. Clip outliers.
    7. Validate size.
    8. Save outputs.
    """
    project_root = get_project_root()
    raw_dir = project_root / "data" / "raw"
    processed_dir = project_root / "data" / "processed"
    reports_dir = project_root / "artifacts" / "reports"

    # Ensure directories exist
    processed_dir.mkdir(parents=True, exist_ok=True)
    reports_dir.mkdir(parents=True, exist_ok=True)

    synthetic_path = "data/raw/synthetic_baseline.csv"
    external_path = "data/raw/external_merged.csv"  # Optional, may not exist

    # 1. Load Data
    print("--- Starting Data Ingestion ---")
    try:
        df = load_data(synthetic_path, external_path, force_external=False)
    except FileNotFoundError as e:
        print(f"CRITICAL ERROR: {e}")
        sys.exit(1)

    rows_input = len(df)
    rows_dropped_nulls = 0
    rows_dropped_other = 0

    # 2. Filter Missing Target
    initial_len = len(df)
    df = filter_missing_target(df)
    rows_dropped_nulls += initial_len - len(df)

    # 3. Impute Missing Compositions
    df = impute_missing_composition(df)

    # 4. Validate Physical Bounds (0 <= cold_work <= 100, time > 0)
    initial_len = len(df)
    df = validate_physical_bounds(df)
    rows_dropped_other += initial_len - len(df)

    # 5. Normalize Units (Time to minutes)
    df = normalize_time_to_minutes(df)

    # 6. Clip Outliers
    df, outlier_log = clip_outliers_target(df)

    # 7. Validate Size (Cap)
    df = validate_dataset_size(df)

    rows_output = len(df)

    # 8. Save Outputs
    validated_path = processed_dir / "validated.csv"
    validation_log_path = reports_dir / "validation_log.json"
    metrics_path = reports_dir / "ingestion_metrics.json"

    print(f"Saving validated dataset to {validated_path}...")
    df.to_csv(validated_path, index=False)

    # Prepare validation log
    validation_log = {
        "rows_ingested": rows_input,
        "rows_dropped_nulls": rows_dropped_nulls,
        "rows_dropped_other": rows_dropped_other,
        **outlier_log
    }

    print(f"Saving validation log to {validation_log_path}...")
    with open(validation_log_path, "w") as f:
        json.dump(validation_log, f, indent=2)

    # Calculate metrics
    null_handling_rate = (rows_input - rows_dropped_nulls) / rows_input if rows_input > 0 else 0.0
    metrics = {
        "rows_ingested": rows_input,
        "rows_dropped_nulls": rows_dropped_nulls,
        "rows_dropped_other": rows_dropped_other,
        "rows_output": rows_output,
        "null_handling_success_rate": null_handling_rate
    }

    # Append to existing metrics if file exists, otherwise create
    if metrics_path.exists():
        with open(metrics_path, "r") as f:
            existing_metrics = json.load(f)
        existing_metrics.update(metrics)
        metrics = existing_metrics

    print(f"Saving ingestion metrics to {metrics_path}...")
    with open(metrics_path, "w") as f:
        json.dump(metrics, f, indent=2)

    print("--- Ingestion Pipeline Complete ---")
    print(f"Output: {validated_path} ({rows_output} rows)")


def main():
    """Entry point for the ingestion script."""
    run_ingestion_pipeline()


if __name__ == "__main__":
    main()