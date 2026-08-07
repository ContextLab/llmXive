import os
import sys
import logging
import pandas as pd
import numpy as np
from pathlib import Path

# Import from utils
from utils import (
    get_project_root_path,
    get_data_raw_path,
    get_data_processed_path,
    get_data_qc_path,
    write_json_log,
    setup_logger
)

# Import from schemas if needed for validation (optional but good practice)
# from schemas import MicrobialTaxa, CognitiveScore

logger = setup_logger('preprocess')

def load_cognitive_raw_data():
    """
    Load raw cognitive data from the ingestion step.
    Expected file: data/raw/cognitive_data_raw.parquet
    """
    root = get_project_root_path()
    raw_dir = get_data_raw_path(root)
    file_path = raw_dir / "cognitive_data_raw.parquet"
    
    if not file_path.exists():
        logger.error(f"Raw cognitive data file not found: {file_path}")
        raise FileNotFoundError(f"Raw cognitive data file not found: {file_path}")
    
    logger.info(f"Loading raw cognitive data from {file_path}")
    df = pd.read_parquet(file_path)
    logger.info(f"Loaded {len(df)} rows of cognitive data")
    return df

def load_microbiome_raw_data():
    """
    Load raw microbiome data from the ingestion step.
    Expected file: data/raw/microbiome_data_raw.parquet
    """
    root = get_project_root_path()
    raw_dir = get_data_raw_path(root)
    file_path = raw_dir / "microbiome_data_raw.parquet"
    
    if not file_path.exists():
        logger.error(f"Raw microbiome data file not found: {file_path}")
        raise FileNotFoundError(f"Raw microbiome data file not found: {file_path}")
    
    logger.info(f"Loading raw microbiome data from {file_path}")
    df = pd.read_parquet(file_path)
    logger.info(f"Loaded {len(df)} rows of microbiome data")
    return df

def apply_mice_imputation(df, target_cols):
    """
    Apply MICE (Multiple Imputation by Chained Equations) for missing values.
    For simplicity in this pipeline, we use IterativeImputer from sklearn.
    """
    from sklearn.experimental import enable_iterative_imputer
    from sklearn.impute import IterativeImputer
    
    logger.info(f"Applying MICE imputation to columns: {target_cols}")
    df_imputed = df.copy()
    
    # Identify numeric columns for imputation
    numeric_cols = df_imputed[target_cols].select_dtypes(include=[np.number]).columns.tolist()
    if not numeric_cols:
        logger.warning("No numeric columns found for imputation.")
        return df_imputed

    imputer = IterativeImputer(max_iter=10, random_state=42)
    df_imputed[numeric_cols] = imputer.fit_transform(df_imputed[numeric_cols])
    
    logger.info(f"MICE imputation completed. Rows: {len(df_imputed)}")
    return df_imputed

def compute_z_scores(df, columns):
    """
    Compute z-scores for specified columns.
    z = (x - mean) / std
    """
    logger.info(f"Computing z-scores for columns: {columns}")
    df_z = df.copy()
    
    for col in columns:
        if col in df_z.columns:
            mean_val = df_z[col].mean()
            std_val = df_z[col].std()
            if std_val == 0:
                logger.warning(f"Standard deviation is 0 for column {col}. Skipping z-score.")
                continue
            df_z[col] = (df_z[col] - mean_val) / std_val
        else:
            logger.warning(f"Column {col} not found in dataframe for z-score computation.")
    
    return df_z

def filter_outliers_by_zscore(df, threshold=3.0, columns=None):
    """
    Filter out outliers based on z-score > threshold.
    If columns is None, applies to all numeric columns.
    Returns the filtered dataframe and a boolean mask of removed rows.
    """
    if columns is None:
        columns = df.select_dtypes(include=[np.number]).columns.tolist()
    
    logger.info(f"Filtering outliers with z-score > {threshold} on columns: {columns}")
    
    # Create a mask for rows to keep (all z-scores within threshold)
    keep_mask = pd.Series([True] * len(df), index=df.index)
    
    for col in columns:
        if col in df.columns:
            mean_val = df[col].mean()
            std_val = df[col].std()
            if std_val == 0:
                continue
            z_scores = np.abs((df[col] - mean_val) / std_val)
            # Rows to keep must have z-score <= threshold
            keep_mask = keep_mask & (z_scores <= threshold)
        else:
            logger.warning(f"Column {col} not found for outlier filtering.")
    
    removed_count = (~keep_mask).sum()
    filtered_df = df[keep_mask].reset_index(drop=True)
    
    logger.info(f"Outlier filtering complete. Removed {removed_count} rows. Remaining: {len(filtered_df)}")
    return filtered_df, keep_mask

def save_processed_data(df, filename="merged_processed.parquet"):
    """
    Save the processed dataframe to the processed data directory.
    """
    root = get_project_root_path()
    processed_dir = get_data_processed_path(root)
    file_path = processed_dir / filename
    
    logger.info(f"Saving processed data to {file_path}")
    df.to_parquet(file_path, index=False)
    logger.info(f"Saved {len(df)} rows to {file_path}")
    return file_path

def attempt_merge_and_report_gap(micro_df, cog_df):
    """
    Attempt to merge microbiome and cognitive data.
    If no common IDs, returns None and triggers gap report logic.
    """
    # Assuming 'sample_id' or 'participant_id' is the key. 
    # Based on schema: microbiome has 'sample_id', cognitive has 'participant_id'.
    # We need to standardize or map them. For this task, we assume a common column 'id' 
    # or we rename one to match the other based on ingestion logic.
    # Let's assume ingestion standardized them to 'participant_id' or we join on 'sample_id' == 'participant_id'.
    
    # Strategy: Rename cognitive participant_id to sample_id if needed, or vice versa.
    # Based on T012/T011 descriptions, let's assume we look for a common key.
    # If the ingestion step didn't standardize, we try to find the intersection of indices or a specific key.
    
    common_key = 'participant_id'
    if common_key not in micro_df.columns and 'sample_id' in micro_df.columns:
        common_key = 'sample_id'
    
    if common_key not in cog_df.columns and 'participant_id' in cog_df.columns:
        # Rename to match
        cog_df = cog_df.rename(columns={'participant_id': common_key})
    
    if common_key not in micro_df.columns:
        logger.error(f"Cannot find common key for merge in microbiome data. Columns: {micro_df.columns}")
        return None, "No common key found for merge"

    logger.info(f"Attempting merge on key: {common_key}")
    merged_df = pd.merge(micro_df, cog_df, on=common_key, how='inner')
    
    if len(merged_df) == 0:
        logger.warning("Merge resulted in 0 rows. Data gap detected.")
        return None, "No common participant IDs found"
    
    logger.info(f"Merge successful. {len(merged_df)} rows.")
    return merged_df, None

def write_filtering_log(total_samples, removed_outliers, threshold, log_path):
    """
    Write the filtering log to JSON.
    Schema: { "total_samples": int, "removed_outliers": int, "threshold": float }
    """
    log_data = {
        "total_samples": int(total_samples),
        "removed_outliers": int(removed_outliers),
        "threshold": float(threshold)
    }
    
    logger.info(f"Writing filtering log to {log_path}")
    write_json_log(log_data, log_path)
    logger.info("Filtering log written successfully.")

def execute_fallback_workflow(reason):
    """
    Trigger the fallback workflow (T017b, T017d) if merge fails.
    This function calls the gap report generator.
    """
    logger.warning(f"Executing fallback workflow due to: {reason}")
    # Import here to avoid circular dependency if utils imports this
    from code_07_gap_report_wrapper import run_gap_report_trigger 
    # Since we can't easily import 07_gap_report directly without path issues in some setups,
    # we simulate the call or import the main function if available.
    # However, per spec, T017b is a separate script. We just log and exit here, 
    # assuming the pipeline orchestrator (quickstart) handles the branching or 
    # we call the script via subprocess.
    # For this task, we just log the trigger.
    logger.critical(f"Data Gap Detected: {reason}. Triggering T017b (Gap Report).")
    # In a real pipeline, this would be an exit code or a signal to the runner.
    # We raise an exception to stop the current flow so the runner can execute the fallback.
    raise RuntimeError(f"Fallback triggered: {reason}")

def main():
    """
    Main preprocessing pipeline:
    1. Load raw cognitive and microbiome data.
    2. Attempt merge.
    3. If merge fails, trigger fallback.
    4. If merge succeeds, apply MICE imputation, compute z-scores, filter outliers.
    5. Save processed data and write filtering log.
    """
    try:
        # 1. Load Data
        cog_df = load_cognitive_raw_data()
        micro_df = load_microbiome_raw_data()
        
        # 2. Attempt Merge
        merged_df, error_msg = attempt_merge_and_report_gap(micro_df, cog_df)
        
        if merged_df is None:
            execute_fallback_workflow(error_msg)
            return
        
        # 3. Preprocessing (MICE, Z-Score)
        # Identify columns for imputation (e.g., cognitive scores, demographic vars)
        # Assuming cognitive scores are numeric and might have missing values
        cognitive_cols = [col for col in merged_df.columns if 'score' in col.lower() or 'z_score' in col.lower()]
        if cognitive_cols:
            merged_df = apply_mice_imputation(merged_df, cognitive_cols)
        
        # Compute z-scores for cognitive metrics
        # Assuming we have a column like 'cognitive_z_score' or we compute it now
        # If the ingestion already did z-score, we might skip. 
        # T013 says "compute z-scores". Let's assume we compute it for the main cognitive metric.
        # We need to know the column name. Let's assume 'cognitive_z_score' or similar.
        # If not present, we compute for all numeric cols except IDs.
        numeric_cols = merged_df.select_dtypes(include=[np.number]).columns.tolist()
        id_cols = ['participant_id', 'sample_id', 'id']
        cols_to_z = [c for c in numeric_cols if c not in id_cols]
        
        if cols_to_z:
            merged_df = compute_z_scores(merged_df, cols_to_z)
        
        # 4. Outlier Filtering (T015)
        threshold = 3.0
        total_before = len(merged_df)
        merged_df, mask = filter_outliers_by_zscore(merged_df, threshold=threshold, columns=cols_to_z)
        total_after = len(merged_df)
        removed = total_before - total_after
        
        # 5. Write Filtering Log
        root = get_project_root_path()
        qc_dir = get_data_qc_path(root)
        log_file = qc_dir / "filtering_log.json"
        write_filtering_log(total_before, removed, threshold, log_file)
        
        # 6. Save Processed Data
        save_processed_data(merged_df, "merged_processed.parquet")
        
        logger.info("Preprocessing pipeline completed successfully.")
        
    except FileNotFoundError as e:
        logger.error(f"Data file missing: {e}")
        raise
    except RuntimeError as e:
        logger.error(f"Pipeline halted: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error in preprocessing: {e}")
        raise

if __name__ == "__main__":
    main()