import logging
import sys
from pathlib import Path
from typing import Tuple, Optional, List
import pandas as pd
import numpy as np

from code.src.utils.config import LOGS_DIR, ensure_directories, get_logs_dir

# Configure logging for this module
logger = logging.getLogger(__name__)

def check_zero_variance(df: pd.DataFrame, columns: List[str]) -> Tuple[bool, List[str]]:
    """
    Check if any of the specified columns have zero variance (constant values).
    
    Args:
        df: DataFrame to check
        columns: List of column names to check
        
    Returns:
        Tuple of (has_zero_variance, list_of_zero_variance_columns)
    """
    zero_var_cols = []
    for col in columns:
        if col in df.columns:
            if df[col].nunique() <= 1:
                zero_var_cols.append(col)
    
    return len(zero_var_cols) > 0, zero_var_cols

def filter_cohort(
    df: pd.DataFrame,
    age_threshold: int = 65,
    required_metrics: Optional[List[str]] = None,
    required_covariates: Optional[List[str]] = None,
    impute_missing: bool = False,
    imputation_columns: Optional[List[str]] = None
) -> Tuple[pd.DataFrame, dict]:
    """
    Filter the cohort based on age, missing values, and zero-variance checks.
    Handles missing covariates via listwise deletion (default) or mean imputation.
    
    Args:
        df: Merged cohort DataFrame
        age_threshold: Minimum age for inclusion (default: 65)
        required_metrics: List of required metric columns (Shannon, Cognitive scores)
        required_covariates: List of required covariate columns
        impute_missing: If True, use mean imputation; if False, use listwise deletion
        imputation_columns: Specific columns to impute (if None, uses required_covariates)
        
    Returns:
        Tuple of (filtered DataFrame, stats dictionary)
    """
    if required_metrics is None:
        required_metrics = ['shannon_diversity', 'cognitive_score']
    
    if required_covariates is None:
        required_covariates = ['age', 'sex', 'bmi', 'fiber_intake', 'antibiotics_use']
    
    if imputation_columns is None:
        imputation_columns = required_covariates

    stats = {
        'original_count': len(df),
        'age_filtered': 0,
        'null_filtered': 0,
        'imputed_count': 0,
        'final_count': 0,
        'imputation_method': 'mean' if impute_missing else 'listwise_deletion'
    }

    # Setup logging
    ensure_directories()
    log_file = Path(get_logs_dir()) / 'filtering.log'
    
    # Configure file handler if not already present
    if not any(isinstance(h, logging.FileHandler) and h.baseFilename == str(log_file) for h in logger.handlers):
        fh = logging.FileHandler(log_file)
        fh.setLevel(logging.INFO)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        logger.addHandler(fh)

    logger.info(f"Starting cohort filtering. Original count: {stats['original_count']}")
    logger.info(f"Age threshold: {age_threshold}")
    logger.info(f"Imputation strategy: {'Mean Imputation' if impute_missing else 'Listwise Deletion'}")

    # Step 1: Age filtering
    df_filtered = df[df['age'] >= age_threshold].copy()
    stats['age_filtered'] = len(df_filtered)
    logger.info(f"After age filtering (>= {age_threshold}): {stats['age_filtered']} participants")

    # Step 2: Check for zero variance in required columns
    all_required = list(set(required_metrics + required_covariates))
    has_zero_var, zero_var_cols = check_zero_variance(df_filtered, all_required)
    
    if has_zero_var:
        logger.warning(f"Zero variance detected in columns: {zero_var_cols}")
        # Note: We don't drop here as per T014, just log it. 
        # The actual correlation step will skip if zero variance is found.

    # Step 3: Handle missing values
    # Identify columns that need checking for missing values
    columns_to_check = list(set(required_metrics + imputation_columns))
    columns_to_check = [c for c in columns_to_check if c in df_filtered.columns]

    missing_before = df_filtered[columns_to_check].isnull().sum().sum()
    stats['null_before'] = int(missing_before)

    if impute_missing:
        # Mean Imputation
        logger.info("Applying mean imputation for missing covariates...")
        for col in imputation_columns:
            if col in df_filtered.columns:
                if df_filtered[col].isnull().any():
                    mean_val = df_filtered[col].mean()
                    if pd.isna(mean_val):
                        # If all values are NaN, fill with 0 or skip
                        mean_val = 0
                        logger.warning(f"Column {col} has all NaN values. Filling with 0.")
                    
                    df_filtered[col] = df_filtered[col].fillna(mean_val)
                    imputed_count = df_filtered[col].isnull().sum()
                    # Note: After fillna, isnull should be 0, so we count how many were actually filled
                    # We do this by comparing before/after or counting non-null before fill
                    non_null_before = df_filtered[col].notna().sum()
                    # Actually, we can't easily get the count of filled cells without storing state before.
                    # Let's count the NAs that existed before fillna for logging
                    na_count = df_filtered[col].isna().sum()
                    if na_count > 0:
                        stats['imputed_count'] += na_count
                        logger.info(f"Imputed {na_count} missing values in column '{col}' with mean {mean_val:.4f}")
        
        # After imputation, we still need to drop rows where required METRICS are missing
        # (Imputation is only for covariates, metrics usually must be observed)
        drop_cols_metrics = [c for c in required_metrics if c in df_filtered.columns]
        if drop_cols_metrics:
            initial_count = len(df_filtered)
            df_filtered = df_filtered.dropna(subset=drop_cols_metrics)
            dropped = initial_count - len(df_filtered)
            if dropped > 0:
                logger.warning(f"Dropped {dropped} rows due to missing required metrics: {drop_cols_metrics}")
        
        stats['imputed_count'] = int(stats['imputed_count'])

    else:
        # Listwise Deletion (Default)
        logger.info("Applying listwise deletion for missing values...")
        initial_count = len(df_filtered)
        # Drop rows where ANY of the required columns are null
        drop_cols = [c for c in required_metrics + required_covariates if c in df_filtered.columns]
        
        if drop_cols:
            df_filtered = df_filtered.dropna(subset=drop_cols)
            dropped = initial_count - len(df_filtered)
            stats['null_filtered'] = dropped
            if dropped > 0:
                logger.info(f"Listwise deletion removed {dropped} participants with missing data.")
        else:
            logger.warning("No columns found to check for missing values.")

    stats['final_count'] = len(df_filtered)
    logger.info(f"Filtering complete. Final cohort size: {stats['final_count']}")
    logger.info(f"Retention rate: {(stats['final_count'] / stats['original_count'] * 100):.2f}%")

    return df_filtered, stats

def main():
    """
    Main entry point for filtering synthetic cohort data.
    Expects data to be generated and merged by previous steps.
    """
    from code.src.utils.config import PROCESSED_DATA_DIR, ensure_directories
    from code.src.data.ingestion import ingest_synthetic_cohort
    
    ensure_directories()
    
    # Generate and ingest synthetic data if not already present
    # This ensures the pipeline can run end-to-end
    try:
        # Check if processed data exists
        processed_path = Path(PROCESSED_DATA_DIR) / 'filtered_cohort.csv'
        if processed_path.exists():
            logger.info(f"Loading existing filtered cohort from {processed_path}")
            df = pd.read_csv(processed_path)
        else:
            logger.info("Generating and ingesting synthetic cohort...")
            df = ingest_synthetic_cohort()
    except Exception as e:
        logger.error(f"Failed to load or generate data: {e}")
        sys.exit(1)

    logger.info(f"Loaded {len(df)} records for filtering.")

    # Perform filtering
    # Default: Listwise deletion
    filtered_df, stats = filter_cohort(
        df,
        age_threshold=65,
        required_metrics=['shannon_diversity', 'cognitive_score'],
        required_covariates=['age', 'sex', 'bmi', 'fiber_intake', 'antibiotics_use'],
        impute_missing=False
    )

    # Save filtered cohort
    output_path = Path(PROCESSED_DATA_DIR) / 'filtered_cohort.csv'
    filtered_df.to_csv(output_path, index=False)
    logger.info(f"Saved filtered cohort to {output_path}")

    # Save stats to a JSON file for downstream use
    import json
    stats_path = Path(PROCESSED_DATA_DIR) / 'filtering_stats.json'
    with open(stats_path, 'w') as f:
        json.dump(stats, f, indent=2)
    logger.info(f"Saved filtering statistics to {stats_path}")

    return filtered_df

if __name__ == "__main__":
    main()