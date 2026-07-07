import logging
from pathlib import Path
from typing import Tuple, Optional, List
import pandas as pd
import numpy as np
from code.src.utils.config import DATA_DIR, LOGS_DIR

# Ensure logs directory exists
LOGS_DIR.mkdir(parents=True, exist_ok=True)

# Configure logger for this module
logger = logging.getLogger("filtering")
logger.setLevel(logging.DEBUG)

# Remove existing handlers to avoid duplicates
if not logger.handlers:
    fh = logging.FileHandler(LOGS_DIR / "filtering.log")
    fh.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    logger.addHandler(fh)
    
    # Also log to console for immediate feedback
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

def check_zero_variance(df: pd.DataFrame, columns: List[str]) -> Tuple[bool, List[str]]:
    """
    Check if any of the specified columns have zero variance.
    
    Args:
        df: Input DataFrame
        columns: List of column names to check
        
    Returns:
        Tuple of (has_zero_variance, list of zero-variance columns)
    """
    logger.debug(f"Checking zero variance for columns: {columns}")
    zero_var_cols = []
    
    for col in columns:
        if col in df.columns:
            if df[col].nunique() <= 1:
                zero_var_cols.append(col)
                logger.warning(f"Column '{col}' has zero variance (unique values: {df[col].nunique()})")
        else:
            logger.warning(f"Column '{col}' not found in DataFrame")
            
    has_zero = len(zero_var_cols) > 0
    if has_zero:
        logger.warning(f"Zero variance detected in columns: {zero_var_cols}")
    else:
        logger.info("No zero variance columns detected")
        
    return has_zero, zero_var_cols

def filter_cohort(
    df: pd.DataFrame,
    min_age: int = 65,
    handle_missing: str = "listwise",
    score_columns: List[str] = None,
    covariate_columns: List[str] = None
) -> pd.DataFrame:
    """
    Filter the cohort based on age, non-null scores, and missing covariates.
    
    Args:
        df: Input DataFrame containing participant data
        min_age: Minimum age threshold (default: 65)
        handle_missing: Strategy for missing covariates: "listwise" (delete) or "mean" (impute)
        score_columns: List of score columns that must be non-null (Shannon, Cognitive scores)
        covariate_columns: List of covariate columns to check for missingness
        
    Returns:
        Filtered DataFrame
    """
    if score_columns is None:
        score_columns = ["shannon_diversity", "cognitive_score"]
        
    if covariate_columns is None:
        covariate_columns = ["age", "sex", "bmi", "fiber_intake", "antibiotics_use"]
        
    logger.info(f"Starting cohort filtering with strategy: {handle_missing}")
    initial_count = len(df)
    logger.info(f"Initial cohort size: {initial_count}")
    
    # Step 1: Filter by age
    logger.info(f"Filtering for age >= {min_age}")
    df = df[df["age"] >= min_age].copy()
    after_age_count = len(df)
    logger.info(f"Cohort size after age filter: {after_age_count} (removed {initial_count - after_age_count})")
    
    # Step 2: Filter by non-null scores
    logger.info(f"Filtering for non-null scores in: {score_columns}")
    for col in score_columns:
        if col in df.columns:
            null_count = df[col].isnull().sum()
            if null_count > 0:
                logger.info(f"Column '{col}' has {null_count} null values")
        else:
            logger.warning(f"Score column '{col}' not found, skipping null check")
            
    valid_score_mask = pd.Series(True, index=df.index)
    for col in score_columns:
        if col in df.columns:
            valid_score_mask &= df[col].notnull()
            
    df = df[valid_score_mask].copy()
    after_score_count = len(df)
    logger.info(f"Cohort size after score filter: {after_score_count} (removed {after_age_count - after_score_count})")
    
    # Step 3: Handle missing covariates
    logger.info(f"Handling missing covariates with strategy: {handle_missing}")
    missing_covariates = []
    for col in covariate_columns:
        if col in df.columns:
            null_count = df[col].isnull().sum()
            if null_count > 0:
                missing_covariates.append((col, null_count))
                logger.info(f"Covariate '{col}' has {null_count} missing values")
        else:
            logger.warning(f"Covariate '{col}' not found in dataset")
            
    if not missing_covariates:
        logger.info("No missing covariates found. No imputation or deletion needed.")
        return df
        
    if handle_missing == "listwise":
        logger.info("Applying listwise deletion for missing covariates")
        initial_missing = len(df)
        df = df.dropna(subset=covariate_columns)
        final_count = len(df)
        deleted_count = initial_missing - final_count
        logger.info(f"Listwise deletion: removed {deleted_count} rows due to missing covariates")
        logger.info(f"Covariates with missing values: {dict(missing_covariates)}")
        
    elif handle_missing == "mean":
        logger.info("Applying mean imputation for missing covariates")
        for col, null_count in missing_covariates:
            if col in df.columns:
                mean_val = df[col].mean()
                df[col] = df[col].fillna(mean_val)
                logger.info(f"Imputed {null_count} missing values in '{col}' with mean: {mean_val:.4f}")
        logger.info("Mean imputation completed for all missing covariates")
        
    else:
        raise ValueError(f"Invalid handle_missing strategy: {handle_missing}. Must be 'listwise' or 'mean'")
        
    final_count = len(df)
    logger.info(f"Final cohort size: {final_count}")
    logger.info(f"Total rows removed from initial: {initial_count - final_count}")
    
    return df

def main():
    """
    Main entry point for the filtering module.
    Generates synthetic data, ingests it, and applies filtering.
    """
    logger.info("=" * 50)
    logger.info("Starting filtering pipeline")
    logger.info("=" * 50)
    
    try:
        # Import here to avoid circular dependencies
        from code.src.data.ingestion import ingest_synthetic_cohort
        from code.src.utils.config import DATA_DIR
        
        # Ensure data directories exist
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        (DATA_DIR / "processed").mkdir(parents=True, exist_ok=True)
        
        # Ingest synthetic cohort
        logger.info("Ingesting synthetic cohort...")
        merged_df = ingest_synthetic_cohort()
        logger.info(f"Ingested {len(merged_df)} participants")
        
        # Apply filtering with default parameters
        logger.info("Applying cohort filters...")
        filtered_df = filter_cohort(
            merged_df,
            min_age=65,
            handle_missing="listwise",
            score_columns=["shannon_diversity", "cognitive_score"],
            covariate_columns=["age", "sex", "bmi", "fiber_intake", "antibiotics_use"]
        )
        
        # Save filtered cohort
        output_path = DATA_DIR / "processed" / "filtered_cohort.csv"
        filtered_df.to_csv(output_path, index=False)
        logger.info(f"Saved filtered cohort to {output_path}")
        logger.info(f"Final cohort size: {len(filtered_df)}")
        
        # Check for zero variance in key columns
        logger.info("Checking for zero variance in key columns...")
        has_zero, zero_cols = check_zero_variance(
            filtered_df,
            ["shannon_diversity", "cognitive_score", "age", "bmi"]
        )
        if has_zero:
            logger.warning(f"Zero variance detected in: {zero_cols}")
        else:
            logger.info("No zero variance issues detected")
            
        logger.info("Filtering pipeline completed successfully")
        return filtered_df
        
    except Exception as e:
        logger.error(f"Pipeline failed with error: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    main()