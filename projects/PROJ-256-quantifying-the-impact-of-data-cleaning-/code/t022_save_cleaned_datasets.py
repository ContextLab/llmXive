"""
Task T022: Write cleaned datasets to data/processed/ with strategy-specific naming.

This script iterates through the cleaning strategies defined in the project,
applies them to the available datasets (loaded from data/raw/), and saves
the resulting cleaned DataFrames to data/processed/ with specific naming conventions.

Naming convention: <dataset_name>_<strategy_type>.csv
Examples:
  - har_outlier_removed.csv
  - har_mean_imputed.csv
  - har_median_imputed.csv
  - har_knn_imputed.csv
  - har_categorical_recoded.csv
"""
import os
import sys
import logging
from typing import Dict, List, Any, Optional
import pandas as pd

# Add project root to path for imports if running as script
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from cleaning import (
    apply_iqr_outlier_removal,
    apply_mean_imputation,
    apply_median_imputation,
    apply_knn_imputation,
    apply_categorical_recoding
)
from config import get_config
from utils import setup_logging, pin_random_seed, compute_file_checksum
from models import CleaningStrategyType, CleaningStrategy

# Configure logging
logger = setup_logging("INFO")

def get_cleaning_strategies() -> List[CleaningStrategy]:
    """
    Returns a list of CleaningStrategy objects defining the operations to perform.
    This matches the implementation in T017-T021.
    """
    strategies = [
        CleaningStrategy(
            strategy_type=CleaningStrategyType.OUTLIER_REMOVAL,
            description="IQR outlier removal (k=1.5)",
            func=apply_iqr_outlier_removal,
            kwargs={"k": 1.5},
            output_suffix="_outlier_removed"
        ),
        CleaningStrategy(
            strategy_type=CleaningStrategyType.MEAN_IMPUTATION,
            description="Mean imputation for missing values",
            func=apply_mean_imputation,
            kwargs={},
            output_suffix="_mean_imputed"
        ),
        CleaningStrategy(
            strategy_type=CleaningStrategyType.MEDIAN_IMPUTATION,
            description="Median imputation for missing values",
            func=apply_median_imputation,
            kwargs={},
            output_suffix="_median_imputed"
        ),
        CleaningStrategy(
            strategy_type=CleaningStrategyType.KNN_IMPUTATION,
            description="KNN imputation (k=5)",
            func=apply_knn_imputation,
            kwargs={"k": 5},
            output_suffix="_knn_imputed"
        ),
        CleaningStrategy(
            strategy_type=CleaningStrategyType.CATEGORICAL_RECODING,
            description="Categorical recoding (factor encoding)",
            func=apply_categorical_recoding,
            kwargs={},
            output_suffix="_categorical_recoded"
        )
    ]
    return strategies

def load_datasets_from_raw(raw_dir: str) -> Dict[str, pd.DataFrame]:
    """
    Loads all CSV files from the raw data directory.
    Returns a dictionary mapping dataset name (without extension) to DataFrame.
    """
    datasets = {}
    if not os.path.exists(raw_dir):
        logger.warning(f"Raw data directory not found: {raw_dir}. No datasets to process.")
        return datasets
    
    for filename in os.listdir(raw_dir):
        if filename.endswith(".csv"):
            filepath = os.path.join(raw_dir, filename)
            try:
                df = pd.read_csv(filepath)
                name = os.path.splitext(filename)[0]
                datasets[name] = df
                logger.info(f"Loaded dataset: {name} (rows: {len(df)}, cols: {len(df.columns)})")
            except Exception as e:
                logger.error(f"Failed to load {filepath}: {e}")
    return datasets

def save_cleaned_dataset(
    df: pd.DataFrame, 
    base_name: str, 
    suffix: str, 
    output_dir: str
) -> str:
    """
    Saves the cleaned DataFrame to the processed directory with the correct naming.
    Returns the path to the saved file.
    """
    filename = f"{base_name}{suffix}.csv"
    filepath = os.path.join(output_dir, filename)
    
    # Ensure directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    df.to_csv(filepath, index=False)
    
    checksum = compute_file_checksum(filepath)
    logger.info(f"Saved cleaned dataset: {filename} (checksum: {checksum[:16]}...)")
    return filepath

def main():
    """Main entry point for T022."""
    pin_random_seed(42) # Reproducibility
    
    config = get_config()
    raw_dir = config.get("RAW_DATA_PATH", "data/raw")
    processed_dir = config.get("PROCESSED_DATA_PATH", "data/processed")
    
    logger.info(f"Starting T022: Saving cleaned datasets.")
    logger.info(f"Raw data path: {raw_dir}")
    logger.info(f"Processed data path: {processed_dir}")
    
    # Load datasets
    datasets = load_datasets_from_raw(raw_dir)
    if not datasets:
        logger.warning("No datasets found to process. Skipping T022.")
        return
    
    strategies = get_cleaning_strategies()
    
    saved_files = []
    
    for dataset_name, df in datasets.items():
        logger.info(f"Processing dataset: {dataset_name}")
        original_rows = len(df)
        
        for strategy in strategies:
            try:
                logger.info(f"  Applying strategy: {strategy.strategy_type.value}")
                
                # Deep copy to ensure we don't modify the original for subsequent strategies
                current_df = df.copy()
                
                # Apply the cleaning function
                cleaned_df = strategy.func(current_df, **strategy.kwargs)
                
                # Validate result (basic check)
                if cleaned_df is None:
                    logger.error(f"  Strategy {strategy.strategy_type.value} returned None for {dataset_name}.")
                    continue
                
                if len(cleaned_df) == 0:
                    logger.warning(f"  Strategy {strategy.strategy_type.value} resulted in empty dataset for {dataset_name}. Skipping save.")
                    continue
                
                # Save
                output_path = save_cleaned_dataset(
                    cleaned_df, 
                    dataset_name, 
                    strategy.output_suffix, 
                    processed_dir
                )
                saved_files.append(output_path)
                
                logger.info(f"    Result: {original_rows} -> {len(cleaned_df)} rows")
                
            except Exception as e:
                logger.error(f"  Failed to apply {strategy.strategy_type.value} to {dataset_name}: {e}", exc_info=True)
    
    logger.info(f"T022 Complete. Saved {len(saved_files)} cleaned dataset files.")
    for f in saved_files:
        logger.info(f"  - {f}")

if __name__ == "__main__":
    main()