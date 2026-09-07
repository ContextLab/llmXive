import logging
import sys
from pathlib import Path
from typing import Tuple, Optional, List
import pandas as pd
import numpy as np

from code.src.utils.config import get_processed_data_dir, get_logs_dir, ensure_directories

# Configure logging
LOGS_DIR = get_logs_dir()
ensure_directories()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOGS_DIR / 'filtering.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

REQUIRED_COVARIATES = ['age', 'sex', 'bmi', 'fiber', 'antibiotics']
REQUIRED_SCORES = ['shannon_diversity', 'cognitive_score']
MIN_AGE = 65

def check_zero_variance(df: pd.DataFrame, column: str) -> bool:
    """
    Check if a specific column has zero variance (constant value).
    
    Args:
        df: DataFrame to check
        column: Name of the column to check
        
    Returns:
        True if the column has zero variance, False otherwise
    """
    if column not in df.columns:
        logger.warning(f"Column '{column}' not found in DataFrame")
        return False
    
    non_null_vals = df[column].dropna()
    if len(non_null_vals) == 0:
        logger.warning(f"Column '{column}' is entirely null")
        return True
    
    if non_null_vals.nunique() == 1:
        logger.warning(f"Column '{column}' has zero variance (constant value: {non_null_vals.iloc[0]})")
        return True
    
    return False

def filter_cohort(
    df: pd.DataFrame,
    impute_missing_covariates: bool = False
) -> Tuple[pd.DataFrame, dict]:
    """
    Filter the cohort based on:
    1. Age >= 65
    2. Non-null Shannon Diversity and Cognitive Score
    3. Non-null required covariates (age, sex, BMI, fiber, antibiotics)
    4. Zero-variance check (flagged, but not automatically dropped unless specified)
    
    Args:
        df: Merged cohort DataFrame
        impute_missing_covariates: If True, mean-impute missing covariates. 
                                   If False, use listwise deletion (default).
                                   
    Returns:
        Tuple of (filtered DataFrame, stats dictionary)
    """
    logger.info(f"Starting cohort filtering on {len(df)} rows")
    initial_count = len(df)
    stats = {
        'initial_count': initial_count,
        'age_filtered': 0,
        'null_scores_filtered': 0,
        'null_covariates_filtered': 0,
        'final_count': 0,
        'zero_variance_columns': []
    }

    # 1. Age Filter
    if 'age' not in df.columns:
        raise ValueError("Required column 'age' not found in dataset")
    
    df = df[df['age'] >= MIN_AGE].copy()
    stats['age_filtered'] = initial_count - len(df)
    logger.info(f"Filtered by age >= {MIN_AGE}: {stats['age_filtered']} rows removed. Remaining: {len(df)}")

    # 2. Null Score Filter
    for score_col in REQUIRED_SCORES:
        if score_col not in df.columns:
            raise ValueError(f"Required score column '{score_col}' not found in dataset")
        before = len(df)
        df = df[df[score_col].notna()]
        removed = before - len(df)
        if removed > 0:
            logger.info(f"Filtered by non-null '{score_col}': {removed} rows removed.")
            stats['null_scores_filtered'] += removed

    # 3. Covariate Check & Filter/Impute
    missing_covariates = [col for col in REQUIRED_COVARIATES if col not in df.columns]
    if missing_covariates:
        raise ValueError(f"Missing required covariates: {missing_covariates}")

    # Check for zero variance in covariates
    for col in REQUIRED_COVARIATES:
        if check_zero_variance(df, col):
            stats['zero_variance_columns'].append(col)
            logger.warning(f"Zero variance detected in covariate '{col}'. "
                           f"This may invalidate correlation analysis.")

    if impute_missing_covariates:
        logger.info("Imputing missing covariates with mean values...")
        for col in REQUIRED_COVARIATES:
            if df[col].isna().any():
                mean_val = df[col].mean()
                df[col] = df[col].fillna(mean_val)
                logger.info(f"Imputed {df[col].isna().sum() - 0} missing values in '{col}' with mean {mean_val:.2f}")
        # Note: After imputation, we don't need to filter for nulls in covariates
    else:
        logger.info("Using listwise deletion for missing covariates...")
        for col in REQUIRED_COVARIATES:
            before = len(df)
            df = df[df[col].notna()]
            removed = before - len(df)
            if removed > 0:
                logger.info(f"Filtered by non-null '{col}': {removed} rows removed.")
                stats['null_covariates_filtered'] += removed

    stats['final_count'] = len(df)
    logger.info(f"Filtering complete. Final count: {stats['final_count']} (from {initial_count})")
    
    return df, stats

def main():
    """
    Main entry point for the filtering script.
    Loads the merged cohort from data/processed/merged_cohort.csv,
    applies filters, and saves to data/processed/filtered_cohort.csv.
    """
    from code.src.data.ingestion import save_merged_cohort # Just to ensure path consistency, though we load directly
    from code.src.utils.config import get_raw_data_dir, get_processed_data_dir
    
    # Determine paths
    processed_dir = get_processed_data_dir()
    input_path = processed_dir / 'merged_cohort.csv'
    output_path = processed_dir / 'filtered_cohort.csv'
    
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        logger.error("Please run T012 (ingestion) first to generate merged_cohort.csv")
        sys.exit(1)

    logger.info(f"Loading data from {input_path}")
    df = pd.read_csv(input_path)
    
    # Apply filtering
    # Default: listwise deletion for missing covariates
    filtered_df, stats = filter_cohort(df, impute_missing_covariates=False)
    
    # Save results
    ensure_directories()
    filtered_df.to_csv(output_path, index=False)
    logger.info(f"Filtered cohort saved to {output_path}")
    
    # Log stats summary
    logger.info(f"Filtering Stats: {stats}")

if __name__ == '__main__':
    main()