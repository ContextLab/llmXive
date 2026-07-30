import os
import sys
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from sklearn.experimental import enable_iterative_imputer
from sklearn.impute import IterativeImputer
from datetime import datetime
import json

from utils import get_project_root_path, get_data_qc_path, get_data_processed_path, get_logger, write_json_log, read_json_log

# Configure logger for this module
logger = get_logger(__name__)

def load_cognitive_raw_data() -> pd.DataFrame:
    """
    Load the raw cognitive data from the ingestion step.
    Expects: data/raw/cognitive_data.parquet
    """
    root = get_project_root_path()
    raw_path = root / "data" / "raw" / "cognitive_data.parquet"
    
    if not raw_path.exists():
        raise FileNotFoundError(f"Raw cognitive data not found at {raw_path}. Run T012 first.")
    
    logger.info(f"Loading raw cognitive data from {raw_path}")
    df = pd.read_parquet(raw_path)
    logger.info(f"Loaded {len(df)} rows")
    return df

def apply_mice_imputation(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply MICE (Multiple Imputation by Chained Equations) to handle missing values.
    Per FR-002, we use IterativeImputer from scikit-learn.
    """
    logger.info("Applying MICE imputation...")
    
    # Select numeric columns for imputation
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    
    if not numeric_cols:
        logger.warning("No numeric columns found for imputation.")
        return df

    imputer = IterativeImputer(max_iter=10, random_state=42)
    
    # Fit and transform only numeric columns
    imputed_values = imputer.fit_transform(df[numeric_cols])
    df_imputed = df.copy()
    df_imputed[numeric_cols] = imputed_values
    
    logger.info(f"MICE imputation complete. Remaining missing values: {df_imputed.isnull().sum().sum()}")
    return df_imputed

def compute_z_scores(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute z-scores for cognitive metrics.
    """
    logger.info("Computing z-scores...")
    
    # Identify cognitive score columns (heuristic: contains 'score' or 'time' in name)
    # In a real spec, we'd use a specific column list from config
    cognitive_cols = [col for col in df.select_dtypes(include=[np.number]).columns 
                    if 'score' in col.lower() or 'time' in col.lower()]
    
    if not cognitive_cols:
        logger.warning("No cognitive score columns found for z-scoring.")
        return df

    df_z = df.copy()
    for col in cognitive_cols:
        mean = df_z[col].mean()
        std = df_z[col].std()
        if std == 0:
            logger.warning(f"Standard deviation is 0 for {col}, skipping z-score.")
            continue
        df_z[col] = (df_z[col] - mean) / std
        
    logger.info(f"Z-scores computed for columns: {cognitive_cols}")
    return df_z

def filter_outliers_by_zscore(df: pd.DataFrame, threshold: float = 3.0) -> tuple[pd.DataFrame, list[dict]]:
    """
    Filter outliers based on z-score > threshold (default 3.0).
    Returns the filtered DataFrame and a list of outlier records for logging.
    """
    logger.info(f"Filtering outliers with z-score threshold > {threshold}...")
    
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    outlier_records = []
    
    # We need to track original indices to report them
    df_indexed = df.reset_index(drop=False)
    
    for col in numeric_cols:
        if col in df_indexed.columns:
            mean = df_indexed[col].mean()
            std = df_indexed[col].std()
            if std == 0:
                continue
            
            z_scores = (df_indexed[col] - mean) / std
            outlier_mask = z_scores.abs() > threshold
            outliers = df_indexed[outlier_mask]
            
            for idx, row in outliers.iterrows():
                outlier_records.append({
                    "row_index": int(row['index']),
                    "column": col,
                    "value": float(row[col]),
                    "z_score": float(z_scores[idx]),
                    "reason": f"Z-score {z_scores[idx]:.4f} exceeds threshold {threshold}"
                })
    
    # Remove rows that have ANY outlier in any numeric column
    # First, identify indices to keep
    outlier_indices = set()
    for record in outlier_records:
        outlier_indices.add(record['row_index'])
    
    mask = ~df_indexed['index'].isin(outlier_indices)
    df_clean = df_indexed[mask].drop(columns=['index'])
    
    logger.info(f"Filtered {len(outlier_indices)} outlier rows out of {len(df_indexed)}. Remaining: {len(df_clean)}")
    return df_clean, outlier_records

def save_outlier_log(outlier_records: list[dict], log_path: Path):
    """
    Save the outlier filtering log to a JSON file.
    """
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "total_outliers": len(outlier_records),
        "outliers": outlier_records
    }
    
    write_json_log(log_path, log_entry)
    logger.info(f"Outlier log saved to {log_path}")

def save_processed_data(df: pd.DataFrame, filename: str):
    """
    Save the processed dataframe to the processed directory.
    """
    processed_dir = get_data_processed_path()
    output_path = processed_dir / filename
    df.to_parquet(output_path, index=False)
    logger.info(f"Processed data saved to {output_path}")

def attempt_merge_and_report_gap(df_microbiome: pd.DataFrame, df_cognitive: pd.DataFrame) -> pd.DataFrame | None:
    """
    Attempt to merge microbiome and cognitive data at the individual level.
    If merge fails (no common IDs), return None to trigger gap report.
    """
    # Assuming 'subject_id' is the common key based on typical study designs
    common_cols = set(df_microbiome.columns) & set(df_cognitive.columns)
    merge_keys = [col for col in common_cols if 'id' in col.lower() or 'subject' in col.lower()]
    
    if not merge_keys:
        logger.error("No common ID columns found for merge.")
        return None
    
    try:
        merged = pd.merge(df_microbiome, df_cognitive, on=merge_keys, how='inner')
        if len(merged) == 0:
            logger.warning("Merge resulted in 0 rows. No individual-level linkage found.")
            return None
        
        logger.info(f"Merge successful. {len(merged)} individual records linked.")
        return merged
    except Exception as e:
        logger.error(f"Merge failed: {e}")
        return None

def main():
    """
    Main execution flow for User Story 1: Preprocessing.
    1. Load raw cognitive data.
    2. Apply MICE imputation.
    3. Compute z-scores.
    4. Filter outliers (z-score > 3) and log to data/qc/filtering_log.json.
    5. Save processed data.
    6. Attempt merge with microbiome data (if available) or trigger gap report.
    """
    logger.info("Starting preprocessing pipeline...")
    
    # 1. Load Data
    try:
        df_cog = load_cognitive_raw_data()
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)
    
    # 2. Imputation
    df_cog = apply_mice_imputation(df_cog)
    
    # 3. Z-scores
    df_cog = compute_z_scores(df_cog)
    
    # 4. Outlier Filtering & Logging (T015)
    df_clean, outlier_records = filter_outliers_by_zscore(df_cog, threshold=3.0)
    
    qc_dir = get_data_qc_path()
    log_path = qc_dir / "filtering_log.json"
    save_outlier_log(outlier_records, log_path)
    
    # 5. Save Processed Data
    save_processed_data(df_clean, "cognitive_processed.parquet")
    
    # 6. Attempt Merge
    # Load microbiome data if it exists (from T011)
    root = get_project_root_path()
    microbe_path = root / "data" / "raw" / "microbiome_data.parquet"
    
    if microbe_path.exists():
        logger.info("Attempting merge with microbiome data...")
        df_micro = pd.read_parquet(microbe_path)
        merged_df = attempt_merge_and_report_gap(df_micro, df_clean)
        
        if merged_df is not None:
            save_processed_data(merged_df, "merged_dataset.parquet")
        else:
            logger.warning("Merge failed. Gap report will be triggered in T017.")
    else:
        logger.info("Microbiome data not found. Skipping merge.")

    logger.info("Preprocessing pipeline completed.")

if __name__ == "__main__":
    main()
