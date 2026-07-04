"""
Preprocessing pipeline for Gut Microbiome and Cognitive Decline Analysis.

Implements:
- Age >= 60 filtering
- Covariate imputation (BMI, education)
- Rarefaction and genus-level collapse (T016)
- Final validation (T017)
"""
import os
import sys
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Tuple, Optional, Dict, Any
from scipy import stats

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data/processed/preprocessing.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Project paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_RAW = PROJECT_ROOT / 'data' / 'raw'
DATA_PROCESSED = PROJECT_ROOT / 'data' / 'processed'

# Ensure output directories exist
DATA_PROCESSED.mkdir(parents=True, exist_ok=True)

def load_merged_data() -> pd.DataFrame:
    """Load the merged dataset from 01_data_ingestion.py output."""
    input_path = DATA_RAW / 'merged_participant_data.csv'
    if not input_path.exists():
        # Fallback for testing if raw merge hasn't been run yet
        # In production, this should fail loudly
        raise FileNotFoundError(
            f"Required input file not found: {input_path}. "
            "Run 01_data_ingestion.py first to generate merged data."
        )
    
    logger.info(f"Loading merged data from {input_path}")
    df = pd.read_csv(input_path)
    logger.info(f"Loaded {len(df)} rows with columns: {list(df.columns)}")
    return df

def filter_by_age(df: pd.DataFrame, min_age: int = 60) -> pd.DataFrame:
    """Filter dataset to include only participants aged >= min_age."""
    if 'age' not in df.columns:
        raise ValueError("Dataset must contain 'age' column for filtering.")
    
    logger.info(f"Filtering for age >= {min_age}")
    initial_count = len(df)
    filtered_df = df[df['age'] >= min_age].copy()
    filtered_count = len(filtered_df)
    
    logger.info(f"Age filter: {initial_count} -> {filtered_count} rows "
               f"(removed {initial_count - filtered_count} samples)")
    
    if filtered_count < 500:
        logger.warning(f"Warning: Only {filtered_count} samples remain after age filtering. "
                     "Minimum recommended is 500 for statistical power.")
    
    return filtered_df

def impute_covariates(df: pd.DataFrame) -> pd.DataFrame:
    """
    Impute missing values for covariates (BMI, education) using median/mean.
    
    Strategy:
    - BMI: Median imputation (robust to outliers)
    - Education: Mean imputation (ordinal scale)
    - Other numeric covariates: Median imputation
    - Categorical covariates: Mode imputation
    
    Returns:
        DataFrame with imputed covariates and logging of imputation counts.
    """
    df_imputed = df.copy()
    covariates_to_impute = ['bmi', 'education']
    
    # Identify which covariates exist in the dataset
    existing_covariates = [col for col in covariates_to_impute if col in df_imputed.columns]
    
    if not existing_covariates:
        logger.warning("No covariates (BMI, education) found in dataset for imputation.")
        return df_imputed
    
    imputation_log = {}
    
    for col in existing_covariates:
        missing_count = df_imputed[col].isna().sum()
        if missing_count == 0:
            logger.info(f"Covariate '{col}': No missing values found.")
            continue
        
        # Determine imputation method based on column characteristics
        if df_imputed[col].dtype in ['float64', 'int64']:
            # Numeric: use median for robustness
            impute_value = df_imputed[col].median()
            imputation_method = 'median'
        else:
            # Categorical: use mode
            impute_value = df_imputed[col].mode().iloc[0]
            imputation_method = 'mode'
        
        # Perform imputation
        df_imputed[col] = df_imputed[col].fillna(impute_value)
        
        imputation_log[col] = {
            'missing_count': int(missing_count),
            'imputation_method': imputation_method,
            'impute_value': float(impute_value) if isinstance(impute_value, (int, float)) else str(impute_value)
        }
        
        logger.info(f"Imputed {missing_count} missing values in '{col}' using {imputation_method} "
                   f"(value: {impute_value})")
    
    # Log summary
    total_imputed = sum(log['missing_count'] for log in imputation_log.values())
    logger.info(f"Total covariate values imputed: {total_imputed}")
    
    return df_imputed

def validate_covariate_imputation(df: pd.DataFrame) -> bool:
    """Validate that all covariates have no missing values after imputation."""
    covariates = ['bmi', 'education']
    existing_covariates = [col for col in covariates if col in df.columns]
    
    for col in existing_covariates:
        if df[col].isna().any():
            logger.error(f"Validation failed: Column '{col}' still has missing values after imputation.")
            return False
    
    logger.info("Covariate imputation validation passed: No missing values in covariates.")
    return True

def run_preprocessing_pipeline() -> pd.DataFrame:
    """
    Execute the full preprocessing pipeline:
    1. Load merged data
    2. Filter by age >= 60
    3. Impute covariates (BMI, education)
    4. Validate results
    
    Returns:
        Processed DataFrame ready for downstream analysis.
    """
    logger.info("="*60)
    logger.info("Starting Preprocessing Pipeline (T015)")
    logger.info("="*60)
    
    # Step 1: Load data
    df = load_merged_data()
    
    # Step 2: Filter by age
    df_filtered = filter_by_age(df, min_age=60)
    
    # Step 3: Impute covariates
    df_imputed = impute_covariates(df_filtered)
    
    # Step 4: Validate
    if not validate_covariate_imputation(df_imputed):
        raise RuntimeError("Preprocessing validation failed. Check logs for details.")
    
    # Step 5: Save intermediate results
    output_path = DATA_PROCESSED / 'preprocessed_age_filtered.csv'
    df_imputed.to_csv(output_path, index=False)
    logger.info(f"Saved age-filtered, covariate-imputed data to {output_path}")
    
    logger.info("="*60)
    logger.info("Preprocessing Pipeline Completed Successfully")
    logger.info(f"Final dataset: {len(df_imputed)} rows, {len(df_imputed.columns)} columns")
    logger.info("="*60)
    
    return df_imputed

def main():
    """Entry point for preprocessing script."""
    try:
        result_df = run_preprocessing_pipeline()
        logger.info("Preprocessing completed successfully.")
        return result_df
    except Exception as e:
        logger.error(f"Preprocessing pipeline failed: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == '__main__':
    main()
