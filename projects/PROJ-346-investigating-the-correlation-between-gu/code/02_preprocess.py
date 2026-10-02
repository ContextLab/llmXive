import os
import sys
import logging
import pandas as pd
import numpy as np
from pathlib import Path
import json

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
    Returns merged dataframe or triggers fallback if no common IDs.
    """
    # Determine common key (assuming 'sample_id' or 'participant_id' mapping)
    # For this implementation, we assume a common 'sample_id' exists in both
    # or a mapping table is used. Here we attempt a direct merge on 'sample_id'.
    
    common_cols = set(microbiome_df.columns) & set(cognitive_df.columns)
    if 'sample_id' in common_cols:
        merge_key = 'sample_id'
    elif 'participant_id' in common_cols:
        merge_key = 'participant_id'
    else:
        # Fallback: try to find a common identifier column
        merge_key = None
        for col in ['subject_id', 'id', 'UID']:
            if col in common_cols:
                merge_key = col
                break
        
        if merge_key is None:
            logger.error("No common identifier column found for merge.")
            return None

    merged_df = pd.merge(microbiome_df, cognitive_df, on=merge_key, how='inner')
    
    if len(merged_df) == 0:
        logger.warning("Merge resulted in 0 rows. Triggering fallback workflow.")
        execute_fallback_workflow()
        return None
    
    logger.info(f"Merge successful. {len(merged_df)} rows found.")
    return merged_df

def execute_fallback_workflow():
    """
    Execute the fallback workflow when data linkage fails.
    This triggers the gap report generation.
    """
    logger.info("Executing fallback workflow...")
    # Import and call the gap report trigger
    # We assume the gap report script is in the same package
    try:
        from code_07_gap_report import generate_gap_report
        generate_gap_report(reason="No common participant IDs found")
    except ImportError:
        # Fallback if direct import fails
        logger.error("Could not import gap report generator.")
    # Write the trigger log
    qc_dir = get_data_qc_path()
    ensure_directory(qc_dir)
    trigger_log_path = qc_dir / "fallback_trigger.log"
    with open(trigger_log_path, 'w') as f:
        f.write("Data Linkage Failed: No common participant IDs found")
    logger.info(f"Fallback trigger log written to {trigger_log_path}")

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
    
    # 1. Load raw data
    try:
        cognitive_df = load_cognitive_raw_data()
        microbiome_df = load_microbiome_raw_data()
    except FileNotFoundError as e:
        logger.error(str(e))
        # If raw data is missing, we cannot proceed.
        # The gap report should have been triggered by T014 if this is the case,
        # but we handle it here for robustness.
        return

    # 2. Attempt Merge (T014 logic included here as per task dependency)
    # If T014 already ran and failed, this script should not run or should detect the gap.
    # However, T015 depends on T014 success. We re-check here.
    merged_df = attempt_merge_and_report_gap(microbiome_df, cognitive_df)
    
    if merged_df is None:
        logger.warning("Preprocessing halted due to data linkage failure.")
        return

    # 3. Imputation (FR-002)
    # Identify target column for imputation (e.g., z_score or cognitive score)
    target_col = 'z_score' if 'z_score' in merged_df.columns else None
    if target_col is None:
        # Try to find a numeric column that might need imputation
        numeric_cols = merged_df.select_dtypes(include=[np.number]).columns
        if len(numeric_cols) > 0:
            target_col = numeric_cols[0]
    
    if target_col:
        merged_df = apply_mice_imputation(merged_df, target_col)
        logger.info(f"Applied MICE imputation to {target_col}")

    # 4. Compute Z-scores (if not already done during imputation or merge)
    # We compute z-scores for the cognitive metric if it exists
    if 'z_score' not in merged_df.columns:
        # Assume there is a cognitive score column
        cognitive_cols = [c for c in merged_df.columns if 'cognitive' in c.lower() or 'score' in c.lower()]
        if cognitive_cols:
            merged_df = compute_z_scores(merged_df, cognitive_cols[0])
            logger.info(f"Computed z-scores for {cognitive_cols[0]}")

    # 5. OUTLIER FILTERING (T015 Core Logic)
    # Identify the column to filter on. Usually the cognitive z-score or the main metric.
    filter_col = 'z_score' if 'z_score' in merged_df.columns else None
    if filter_col is None:
        # Fallback to first numeric column if 'z_score' is missing
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
        
        # Log the filtering results
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

    # 6. Save processed data
    processed_dir = get_data_processed_path()
    output_path = processed_dir / "merged_dataset.parquet"
    save_processed_data(merged_df, output_path)

    logger.info("Preprocessing pipeline completed successfully.")

if __name__ == "__main__":
    main()
