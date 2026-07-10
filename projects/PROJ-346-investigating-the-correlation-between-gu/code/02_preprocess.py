import os
import sys
import logging
import pandas as pd
import numpy as np
from pathlib import Path
import json
from datetime import datetime

# Ensure we can import from the project root
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils import (
    get_data_processed_path,
    get_data_qc_path,
    setup_logger,
    get_logger,
    write_json_log
)

logger = setup_logger("preprocess")

# Constants for outlier detection
OUTLIER_ZSCORE_THRESHOLD = 3.0

def load_cognitive_raw_data(raw_path: str) -> pd.DataFrame:
    """
    Load raw cognitive data from a Parquet file.
    """
    logger.info(f"Loading raw cognitive data from {raw_path}")
    if not os.path.exists(raw_path):
        raise FileNotFoundError(f"Raw cognitive data file not found: {raw_path}")
    
    df = pd.read_parquet(raw_path)
    logger.info(f"Loaded {len(df)} rows from {raw_path}")
    return df

def apply_mice_imputation(df: pd.DataFrame, numeric_cols: list) -> pd.DataFrame:
    """
    Apply MICE (Multiple Imputation by Chained Equations) imputation for missing values.
    Uses sklearn's IterativeImputer as a proxy for MICE.
    """
    logger.info("Applying MICE imputation for missing values")
    
    if df[numeric_cols].isnull().sum().sum() == 0:
        logger.info("No missing values found in numeric columns, skipping imputation")
        return df

    from sklearn.experimental import enable_iterative_imputer
    from sklearn.impute import IterativeImputer
    
    imputer = IterativeImputer(max_iter=10, random_state=42)
    
    # Only impute numeric columns
    imputed_data = imputer.fit_transform(df[numeric_cols])
    df[numeric_cols] = imputed_data
    
    logger.info("MICE imputation completed")
    return df

def compute_z_scores(df: pd.DataFrame, columns: list) -> pd.DataFrame:
    """
    Compute z-scores for specified columns.
    """
    logger.info(f"Computing z-scores for columns: {columns}")
    
    for col in columns:
        if col not in df.columns:
            logger.warning(f"Column {col} not found in dataframe, skipping z-score computation")
            continue
        
        mean_val = df[col].mean()
        std_val = df[col].std()
        
        if std_val == 0:
            logger.warning(f"Standard deviation for {col} is 0, setting z-scores to 0")
            df[f"{col}_zscore"] = 0.0
        else:
            df[f"{col}_zscore"] = (df[col] - mean_val) / std_val
    
    logger.info("Z-score computation completed")
    return df

def filter_outliers_by_zscore(df: pd.DataFrame, columns: list, threshold: float = OUTLIER_ZSCORE_THRESHOLD) -> tuple[pd.DataFrame, list]:
    """
    Filter out rows where any of the specified columns have a z-score > threshold.
    Returns the filtered dataframe and a list of removed row indices.
    """
    logger.info(f"Filtering outliers with z-score > {threshold}")
    
    if not columns:
        logger.warning("No columns provided for outlier filtering")
        return df, []
    
    # Identify rows to keep
    mask = pd.Series(True, index=df.index)
    
    for col in columns:
        zscore_col = f"{col}_zscore"
        if zscore_col not in df.columns:
            logger.warning(f"Z-score column {zscore_col} not found, skipping")
            continue
        
        # Create mask for this column
        col_mask = df[zscore_col].abs() <= threshold
        mask = mask & col_mask
        
        removed_count = (~col_mask).sum()
        if removed_count > 0:
            logger.info(f"Removed {removed_count} rows based on {zscore_col} (threshold={threshold})")
    
    removed_indices = df[~mask].index.tolist()
    filtered_df = df[mask].copy()
    
    logger.info(f"Outlier filtering complete. Removed {len(removed_indices)} rows. Remaining: {len(filtered_df)}")
    return filtered_df, removed_indices

def save_outlier_log(removed_indices: list, columns: list, threshold: float, output_path: str):
    """
    Save the outlier filtering log to a JSON file.
    """
    log_entry = {
        "timestamp": datetime.now().isoformat(),
        "operation": "outlier_filtering",
        "threshold": threshold,
        "columns_checked": columns,
        "rows_removed": len(removed_indices),
        "removed_indices": removed_indices
    }
    
    # Load existing log if it exists
    qc_dir = Path(output_path).parent
    qc_dir.mkdir(parents=True, exist_ok=True)
    
    existing_log = []
    if os.path.exists(output_path):
        try:
            with open(output_path, 'r') as f:
                existing_log = json.load(f)
        except (json.JSONDecodeError, IOError):
            existing_log = []
    
    existing_log.append(log_entry)
    
    with open(output_path, 'w') as f:
        json.dump(existing_log, f, indent=2)
    
    logger.info(f"Outlier filtering log saved to {output_path}")

def save_processed_data(df: pd.DataFrame, output_path: str):
    """
    Save the processed dataframe to a Parquet file.
    """
    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    df.to_parquet(output_path, index=False)
    logger.info(f"Processed data saved to {output_path}")

def main():
    """
    Main execution function for preprocessing cognitive data.
    1. Load raw cognitive data
    2. Apply MICE imputation
    3. Compute z-scores
    4. Filter outliers (z-score > 3)
    5. Save processed data and filtering log
    """
    # Paths
    raw_data_path = str(get_data_processed_path().parent / "raw" / "cognitive_raw.parquet")
    processed_output_path = str(get_data_processed_path() / "cognitive_processed.parquet")
    qc_log_path = str(get_data_qc_path() / "filtering_log.json")
    
    # Ensure directories exist
    get_data_processed_path().mkdir(parents=True, exist_ok=True)
    get_data_qc_path().mkdir(parents=True, exist_ok=True)
    
    try:
        # 1. Load raw data
        if not os.path.exists(raw_data_path):
            logger.error(f"Raw data file not found at {raw_data_path}. "
                         "Please run 01_ingest.py first to generate the raw cognitive data.")
            sys.exit(1)
        
        df = load_cognitive_raw_data(raw_data_path)
        
        # Identify numeric columns for imputation and z-score
        # Assuming cognitive scores are numeric columns
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        
        if not numeric_cols:
            logger.error("No numeric columns found in the dataset for processing.")
            sys.exit(1)
        
        # 2. Apply MICE imputation
        df = apply_mice_imputation(df, numeric_cols)
        
        # 3. Compute z-scores
        df = compute_z_scores(df, numeric_cols)
        
        # 4. Filter outliers
        zscore_cols = [f"{col}_zscore" for col in numeric_cols if f"{col}_zscore" in df.columns]
        df_filtered, removed_indices = filter_outliers_by_zscore(df, zscore_cols, threshold=OUTLIER_ZSCORE_THRESHOLD)
        
        # 5. Save outlier log
        save_outlier_log(removed_indices, zscore_cols, OUTLIER_ZSCORE_THRESHOLD, qc_log_path)
        
        # 6. Save processed data
        save_processed_data(df_filtered, processed_output_path)
        
        logger.info("Preprocessing pipeline completed successfully.")
        
    except Exception as e:
        logger.exception(f"Error during preprocessing: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()