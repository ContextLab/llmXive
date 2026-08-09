import os
import sys
import csv
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

import pandas as pd
import numpy as np
from scipy import stats

# Project root resolution
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
SPLITS_DIR = DATA_DIR / "splits"
PROCESSED_DIR = DATA_DIR / "processed"
LOGS_DIR = PROJECT_ROOT / "logs"

# Ensure directories exist
SPLITS_DIR.mkdir(parents=True, exist_ok=True)
LOGS_DIR.mkdir(parents=True, exist_ok=True)

logger = logging.getLogger(__name__)

@dataclass
class SplitResult:
    train_indices: List[int]
    test_indices: List[int]
    ks_statistic: float
    ks_p_value: float
    train_mw_mean: float
    test_mw_mean: float
    train_mw_std: float
    test_mw_std: float

def load_processed_data() -> pd.DataFrame:
    """
    Loads the processed dataset containing SMILES, molecular_weight, and surface_area.
    Expects: data/processed/paired_dataset.parquet
    """
    input_path = PROCESSED_DIR / "paired_dataset.parquet"
    if not input_path.exists():
        raise FileNotFoundError(
            f"Input file not found: {input_path}. "
            "Ensure T015 has completed successfully."
        )
    
    logger.info(f"Loading processed data from {input_path}")
    df = pd.read_parquet(input_path)
    
    required_cols = ['smiles', 'molecular_weight', 'surface_area']
    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in input data: {missing_cols}")
    
    # Drop rows with any NaN in critical columns to ensure clean split
    df = df.dropna(subset=required_cols)
    
    logger.info(f"Loaded {len(df)} valid molecules for splitting.")
    return df

def calculate_mw_stats(df: pd.DataFrame) -> Dict[str, float]:
    """Calculate basic statistics for Molecular Weight."""
    mw = df['molecular_weight']
    return {
        'mean': float(mw.mean()),
        'std': float(mw.std()),
        'min': float(mw.min()),
        'max': float(mw.max())
    }

def stratified_split_by_mw(
    df: pd.DataFrame, 
    test_ratio: float = 0.2, 
    random_seed: int = 42
) -> Tuple[List[int], List[int]]:
    """
    Performs a stratified split based on Molecular Weight bins.
    
    Strategy:
    1. Bin the molecular_weight column into quantiles (e.g., 10 bins) to ensure
       distribution coverage across the range.
    2. Stratify the split based on these bins.
    3. Return indices corresponding to the original dataframe.
    """
    n = len(df)
    n_test = int(n * test_ratio)
    
    # Create bins based on quantiles to ensure even distribution
    # Using 10 bins is a standard approach for continuous variables
    n_bins = 10
    df_copy = df.copy()
    df_copy['mw_bin'] = pd.qcut(df_copy['molecular_weight'], q=n_bins, duplicates='drop')
    
    # Reset index to keep track of original row positions
    df_copy = df_copy.reset_index(drop=False)
    
    # Perform stratified split
    train_indices = []
    test_indices = []
    
    for _, group in df_copy.groupby('mw_bin'):
        group_indices = group['index'].tolist()
        np.random.seed(random_seed)
        np.random.shuffle(group_indices)
        
        n_group_test = max(1, int(len(group_indices) * test_ratio))
        test_indices.extend(group_indices[:n_group_test])
        train_indices.extend(group_indices[n_group_test:])
    
    return train_indices, test_indices

def validate_split_distribution(
    train_df: pd.DataFrame, 
    test_df: pd.DataFrame
) -> Tuple[float, float]:
    """
    Performs the Kolmogorov-Smirnov test to compare MW distributions.
    Returns (statistic, p_value).
    """
    train_mw = train_df['molecular_weight'].values
    test_mw = test_df['molecular_weight'].values
    
    statistic, p_value = stats.ks_2samp(train_mw, test_mw)
    return statistic, p_value

def save_indices_to_csv(
    indices: List[int], 
    filepath: Path
) -> None:
    """Saves a list of indices to a CSV file."""
    with open(filepath, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['index'])
        for idx in indices:
            writer.writerow([idx])
    logger.info(f"Saved {len(indices)} indices to {filepath}")

def main():
    """
    Main execution function for T016.
    
    1. Loads paired_dataset.parquet.
    2. Stratified split by Molecular Weight.
    3. Performs KS test.
    4. Generates split_report.json and split_error_report.json (if needed).
    5. Saves train/test indices to CSV.
    """
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(LOGS_DIR / "split_execution.log"),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    try:
        # 1. Load Data
        df = load_processed_data()
        
        # 2. Split Data
        logger.info("Performing stratified split by Molecular Weight...")
        train_indices, test_indices = stratified_split_by_mw(df, test_ratio=0.2, random_seed=42)
        
        # Create subsets for analysis
        train_df = df.iloc[train_indices]
        test_df = df.iloc[test_indices]
        
        # 3. Calculate Statistics & KS Test
        logger.info("Calculating distribution statistics and running KS test...")
        train_stats = calculate_mw_stats(train_df)
        test_stats = calculate_mw_stats(test_df)
        
        ks_stat, ks_p = validate_split_distribution(train_df, test_df)
        
        logger.info(f"KS Statistic: {ks_stat:.4f}, KS P-Value: {ks_p:.4f}")
        
        # 4. Generate Reports
        split_report = {
            "ks_statistic": float(ks_stat),
            "ks_p_value": float(ks_p),
            "train_size": len(train_indices),
            "test_size": len(test_indices),
            "train_mw_stats": train_stats,
            "test_mw_stats": test_stats,
            "random_seed": 42,
            "split_ratio": 0.2
        }
        
        split_report_path = SPLITS_DIR / "split_report.json"
        with open(split_report_path, 'w') as f:
            json.dump(split_report, f, indent=2)
        logger.info(f"Saved split report to {split_report_path}")
        
        # 5. Handle Failure Condition (p <= 0.05)
        if ks_p <= 0.05:
            error_report = {
                "status": "failed_distribution_match",
                "message": "The molecular weight distributions of train and test sets are significantly different (p <= 0.05).",
                "ks_statistic": float(ks_stat),
                "ks_p_value": float(ks_p),
                "threshold": 0.05,
                "recommendation": "Consider re-running with a different random seed or adjusting the stratification bins."
            }
            error_report_path = SPLITS_DIR / "split_error_report.json"
            with open(error_report_path, 'w') as f:
                json.dump(error_report, f, indent=2)
            logger.warning(f"Generated error report: {error_report_path}. Split distribution mismatch detected.")
        else:
            logger.info("Split distribution check passed (p > 0.05).")
        
        # 6. Save Indices
        train_csv_path = SPLITS_DIR / "train_indices.csv"
        test_csv_path = SPLITS_DIR / "test_indices.csv"
        
        save_indices_to_csv(train_indices, train_csv_path)
        save_indices_to_csv(test_indices, test_csv_path)
        
        logger.info("T016 completed successfully.")
        
    except FileNotFoundError as e:
        logger.error(f"Critical file missing: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during split: {e}")
        raise

if __name__ == "__main__":
    main()