import os
import sys
import csv
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

import numpy as np
import pandas as pd
from scipy import stats

# Import from project utils
from code.utils.logging_config import setup_pipeline_logger, log_exclusion, log_imputation_rate
from code.utils.statistical_tests import shapiro_test
from code.utils.checkpointing import ensure_checkpoint_dir, save_checkpoint, load_checkpoint, has_checkpoint

# Configure logger
logger = setup_pipeline_logger()

DATA_DIR = Path("data")
PROCESSED_DIR = DATA_DIR / "processed"
RAW_DIR = DATA_DIR / "raw"
CHECKPOINT_DIR = DATA_DIR / "checkpoints"

# Constants
MISSING_THRESHOLD = 0.10  # Exclude if > 10% missing
MIN_SAMPLE_SIZE = 30

def load_dataset_from_file(file_path: str) -> pd.DataFrame:
    """
    Load a dataset from a file (CSV/Excel).
    Raises FileNotFoundError or ValueError if the file is invalid.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Dataset file not found: {file_path}")
    
    if file_path.endswith('.csv'):
        return pd.read_csv(file_path)
    elif file_path.endswith(('.xlsx', '.xls')):
        return pd.read_excel(file_path)
    else:
        raise ValueError(f"Unsupported file format: {file_path}")

def calculate_missing_ratio(df: pd.DataFrame) -> float:
    """Calculate the ratio of missing values in the entire dataframe."""
    if df.empty:
        return 1.0
    return df.isna().sum().sum() / (df.shape[0] * df.shape[1])

def impute_missing_values(df: pd.DataFrame, strategy: str = 'mean') -> Tuple[pd.DataFrame, float]:
    """
    Impute missing values using mean or median strategy.
    Returns the imputed dataframe and the imputation rate.
    """
    if df.empty:
        return df, 0.0

    df_imputed = df.copy()
    numeric_cols = df_imputed.select_dtypes(include=[np.number]).columns

    if len(numeric_cols) == 0:
        return df_imputed, 0.0

    imputation_counts = 0
    total_numeric_cells = df_imputed[numeric_cols].size

    for col in numeric_cols:
        missing_mask = df_imputed[col].isna()
        if missing_mask.any():
            if strategy == 'median':
                fill_value = df_imputed[col].median()
            else:
                fill_value = df_imputed[col].mean()
            
            # Handle case where mean/median is NaN (e.g., all NaN column)
            if pd.isna(fill_value):
                fill_value = 0.0
            
            df_imputed.loc[missing_mask, col] = fill_value
            imputation_counts += missing_mask.sum()

    imputation_rate = imputation_counts / total_numeric_cells if total_numeric_cells > 0 else 0.0
    return df_imputed, imputation_rate

def filter_by_missing_data(df: pd.DataFrame, dataset_id: str) -> Optional[pd.DataFrame]:
    """
    Filter dataset: exclude if missing ratio > threshold.
    Returns None if excluded, otherwise returns the dataframe.
    """
    missing_ratio = calculate_missing_ratio(df)
    
    if missing_ratio > MISSING_THRESHOLD:
        log_exclusion(
            dataset_id=dataset_id,
            reason="high_missing_ratio",
            details=f"Missing ratio {missing_ratio:.4f} exceeds threshold {MISSING_THRESHOLD}"
        )
        logger.warning(f"Dataset {dataset_id} excluded due to high missing data ratio: {missing_ratio:.4f}")
        return None
    
    return df

def process_dataset_for_filtering(dataset_id: str, file_path: str) -> Optional[pd.DataFrame]:
    """
    Main processing pipeline for a single dataset:
    1. Load data
    2. Check missing ratio (exclude if > 10%)
    3. Impute remaining missing values (mean/median)
    4. Return processed dataframe
    """
    logger.info(f"Processing dataset {dataset_id} for filtering...")
    
    try:
        df = load_dataset_from_file(file_path)
    except Exception as e:
        log_exclusion(
            dataset_id=dataset_id,
            reason="load_error",
            details=str(e)
        )
        logger.error(f"Failed to load dataset {dataset_id}: {e}")
        return None

    # Step 1: Check missing data ratio
    filtered_df = filter_by_missing_data(df, dataset_id)
    if filtered_df is None:
        return None

    # Step 2: Impute missing values
    imputed_df, imputation_rate = impute_missing_values(filtered_df, strategy='mean')
    
    if imputation_rate > 0:
        log_imputation_rate(
            dataset_id=dataset_id,
            rate=imputation_rate,
            strategy='mean'
        )
        logger.info(f"Dataset {dataset_id}: Imputation rate = {imputation_rate:.4f}")

    return imputed_df

def run_filter_pipeline():
    """
    Main entry point to process all raw datasets, apply imputation and exclusion logic,
    and save processed datasets.
    """
    logger.info("Starting dataset filtering pipeline (T015)...")
    
    # Ensure output directories exist
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    ensure_checkpoint_dir(CHECKPOINT_DIR)

    # Load list of datasets from metadata
    datasets_csv_path = DATA_DIR / "datasets.csv"
    if not datasets_csv_path.exists():
        logger.error("data/datasets.csv not found. Run download_datasets.py first.")
        return

    datasets = []
    with open(datasets_csv_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            datasets.append(row)

    logger.info(f"Found {len(datasets)} datasets to process.")

    processed_count = 0
    excluded_count = 0

    for ds in datasets:
        dataset_id = ds['dataset_id']
        file_path = ds.get('file_path')
        
        if not file_path or not os.path.exists(file_path):
            log_exclusion(
                dataset_id=dataset_id,
                reason="file_missing",
                details="File path missing or file does not exist"
            )
            excluded_count += 1
            continue

        # Check checkpoint
        checkpoint_path = CHECKPOINT_DIR / f"{dataset_id}_filter.json"
        if has_checkpoint(checkpoint_path):
            logger.info(f"Skipping {dataset_id} (already processed)")
            processed_count += 1
            continue

        # Process
        result_df = process_dataset_for_filtering(dataset_id, file_path)
        
        if result_df is not None:
            # Save processed dataset
            output_path = PROCESSED_DIR / f"{dataset_id}_processed.csv"
            result_df.to_csv(output_path, index=False)
            logger.info(f"Saved processed dataset to {output_path}")
            
            # Save checkpoint
            save_checkpoint(checkpoint_path, {
                'dataset_id': dataset_id,
                'status': 'completed',
                'output_path': str(output_path)
            })
            
            processed_count += 1
        else:
            excluded_count += 1

    logger.info(f"Filtering pipeline complete. Processed: {processed_count}, Excluded: {excluded_count}")

if __name__ == "__main__":
    run_filter_pipeline()