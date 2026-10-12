import os
import sys
import logging
import pandas as pd
import numpy as np
from pathlib import Path
import json
from datetime import datetime

# Import shared utilities
from utils import (
    get_project_root_path,
    get_data_raw_path,
    get_data_processed_path,
    get_data_qc_path,
    ensure_directory,
    setup_logger,
    write_json_log
)

# Configure logger
logger = setup_logger('preprocess')

# Constants
OUTLIER_THRESHOLD = 3.0

def load_cognitive_raw_data():
    """Load raw cognitive data from parquet."""
    raw_path = get_data_raw_path() / "cognitive_data.parquet"
    if not raw_path.exists():
        raise FileNotFoundError(f"Raw cognitive data not found at {raw_path}")
    return pd.read_parquet(raw_path)

def load_microbiome_raw_data():
    """Load raw microbiome data from parquet."""
    raw_path = get_data_raw_path() / "microbiome_data.parquet"
    if not raw_path.exists():
        raise FileNotFoundError(f"Raw microbiome data not found at {raw_path}")
    return pd.read_parquet(raw_path)

def apply_mice_imputation(df, target_col):
    """
    Apply MICE (Multivariate Imputation by Chained Equations) for missing values.
    Simplified implementation using iterative imputer for compatibility.
    """
    if df[target_col].isnull().sum() == 0:
        return df

    from sklearn.experimental import enable_iterative_imputer
    from sklearn.impute import IterativeImputer

    imputer = IterativeImputer(max_iter=10, random_state=42)
    df[target_col] = imputer.fit_transform(df[[target_col]])
    return df

def compute_z_scores(df, column):
    """Compute z-scores for a specific column."""
    mean_val = df[column].mean()
    std_val = df[column].std()
    if std_val == 0:
        df[f"{column}_zscore"] = 0.0
    else:
        df[f"{column}_zscore"] = (df[column] - mean_val) / std_val
    return df

def filter_outliers_by_zscore(df, column, threshold=OUTLIER_THRESHOLD):
    """
    Filter outliers based on z-score > threshold.
    Returns the filtered dataframe and the count of removed outliers.
    """
    if column not in df.columns:
        raise ValueError(f"Column {column} not found in dataframe")

    # Calculate z-scores if not already present
    if f"{column}_zscore" not in df.columns:
        df = compute_z_scores(df, column)

    z_scores = df[f"{column}_zscore"].abs()
    outliers_mask = z_scores > threshold
    removed_count = outliers_mask.sum()
    filtered_df = df[~outliers_mask].copy()

    return filtered_df, removed_count

def attempt_merge_and_report_gap(microbiome_df, cognitive_df):
    """
    Attempt to merge microbiome and cognitive data.
    If merge results in 0 rows, trigger fallback workflow.
    Returns merged dataframe or None if merge fails.
    """
    # Identify a common identifier column
    common_cols = set(microbiome_df.columns) & set(cognitive_df.columns)
    merge_key = None
    for candidate in ['sample_id', 'participant_id', 'subject_id', 'id', 'UID']:
        if candidate in common_cols:
            merge_key = candidate
            break

    if merge_key is None:
        logger.error("No common identifier column found for merge.")
        # No merge possible -> treat as data gap
        execute_fallback_workflow()
        return None

    merged_df = pd.merge(microbiome_df, cognitive_df, on=merge_key, how='inner')
    if len(merged_df) == 0:
        logger.warning("Merge resulted in 0 rows. Triggering fallback workflow.")
        execute_fallback_workflow()
        return None

    logger.info(f"Merge successful: {len(merged_df)} rows.")
    return merged_df

def execute_fallback_workflow():
    """
    Execute the fallback workflow when data linkage fails.
    Generates the fallback trigger log and a Data Gap Report (FR-008).
    """
    logger.info("Executing fallback workflow...")

    # Write the trigger log
    qc_dir = get_data_qc_path()
    ensure_directory(qc_dir)
    trigger_log_path = qc_dir / "fallback_trigger.log"
    with open(trigger_log_path, 'w') as f:
        f.write("Data Linkage Failed: No common participant IDs found")
    logger.info(f"Fallback trigger log written to {trigger_log_path}")

    # Generate a minimal Data Gap Report (mirrors code/07_gap_report.py behavior)
    processed_dir = get_data_processed_path()
    ensure_directory(processed_dir)
    report_path = processed_dir / "data_gap_report.json"
    report_data = {
        "report_type": "Data Gap Report (FR-008)",
        "timestamp": datetime.now().isoformat(),
        "failure_reason": "No common participant IDs found",
        "affected_studies": ["Qiita 10313", "UK Biobank/NHANES"],
        "status": "Linkage Failed",
        "framing": "associational only - No individual-level data available",
        "message": "No individual-level linkage possible; no valid meta-analysis possible without synthetic linkage.",
        "next_steps": "Trigger meta-analysis fallback or report gap."
    }
    with open(report_path, 'w') as f:
        json.dump(report_data, f, indent=2)
    logger.info(f"Data Gap Report written to {report_path}")

def write_filtering_log(total_samples, removed_outliers, threshold, log_path):
    """
    Write the filtering log to a JSON file.
    Schema: { "total_samples": int, "removed_outliers": int, "threshold": float }
    """
    log_data = {
        "total_samples": int(total_samples),
        "removed_outliers": int(removed_outliers),
        "threshold": float(threshold)
    }
    ensure_directory(log_path.parent)
    with open(log_path, 'w') as f:
        json.dump(log_data, f, indent=2)
    logger.info(f"Filtering log written to {log_path}")

def save_processed_data(df, output_path):
    """Save the processed dataframe to parquet."""
    ensure_directory(output_path.parent)
    df.to_parquet(output_path, index=False)
    logger.info(f"Processed data saved to {output_path}")

def main():
    """Main preprocessing pipeline."""
    logger.info("Starting preprocessing pipeline...")

    # Load raw data
    try:
        cognitive_df = load_cognitive_raw_data()
        microbiome_df = load_microbiome_raw_data()
    except FileNotFoundError as e:
        logger.error(str(e))
        # If raw data is missing, we cannot proceed; trigger fallback to be explicit
        execute_fallback_workflow()
        return

    # Attempt merge (T014 logic)
    merged_df = attempt_merge_and_report_gap(microbiome_df, cognitive_df)
    if merged_df is None:
        logger.warning("Preprocessing halted due to data linkage failure.")
        return

    # Imputation (FR-002)
    target_col = None
    if 'z_score' in merged_df.columns:
        target_col = 'z_score'
    else:
        numeric_cols = merged_df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 0:
            target_col = numeric_cols[0]

    if target_col:
        merged_df = apply_mice_imputation(merged_df, target_col)
        logger.info(f"Applied MICE imputation to column '{target_col}'")

    # Compute Z-scores if not present
    if 'z_score' not in merged_df.columns:
        cognitive_cols = [c for c in merged_df.columns if 'cognitive' in c.lower() or 'score' in c.lower()]
        if cognitive_cols:
            merged_df = compute_z_scores(merged_df, cognitive_cols[0])
            logger.info(f"Computed z-scores for column '{cognitive_cols[0]}'")

    # Outlier filtering (T015 core logic)
    filter_col = 'z_score' if 'z_score' in merged_df.columns else None
    if filter_col is None:
        numeric_cols = merged_df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 0:
            filter_col = numeric_cols[0]

    if filter_col:
        initial_count = len(merged_df)
        merged_df, removed_count = filter_outliers_by_zscore(
            merged_df,
            filter_col,
            threshold=OUTLIER_THRESHOLD
        )
        qc_dir = get_data_qc_path()
        log_path = qc_dir / "filtering_log.json"
        write_filtering_log(
            total_samples=initial_count,
            removed_outliers=removed_count,
            threshold=OUTLIER_THRESHOLD,
            log_path=log_path
        )
        logger.info(f"Outlier filtering complete. Removed {removed_count} samples.")
    else:
        logger.warning("No suitable column found for outlier filtering.")

    # Save processed merged dataset
    processed_dir = get_data_processed_path()
    output_path = processed_dir / "merged_dataset.parquet"
    save_processed_data(merged_df, output_path)

    logger.info("Preprocessing pipeline completed successfully.")

if __name__ == "__main__":
    main()
