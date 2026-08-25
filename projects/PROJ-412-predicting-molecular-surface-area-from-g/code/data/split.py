import os
import sys
import csv
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

import numpy as np
import pandas as pd
from scipy import stats

# Import project utilities
from code.utils.logging import get_logger, get_project_root
from code.utils.seed import set_seed
from code.config import RANDOM_SEED

@dataclass
class SplitResult:
    train_indices: List[int]
    test_indices: List[int]
    ks_p_value: float
    used_seed: int

def load_processed_data() -> pd.DataFrame:
    """Load the processed dataset containing SMILES and Molecular Weight."""
    project_root = get_project_root()
    input_path = project_root / "data" / "processed" / "paired_dataset.parquet"
    
    if not input_path.exists():
        raise FileNotFoundError(f"Required input file not found: {input_path}")
    
    logger = get_logger()
    logger.info(f"Loading processed data from {input_path}")
    
    df = pd.read_parquet(input_path)
    
    required_cols = ['smiles', 'molecular_weight']
    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Input dataset missing required columns: {missing_cols}")
    
    # Drop rows with missing MW if any (should not happen after T014/T015c)
    initial_count = len(df)
    df = df.dropna(subset=['molecular_weight'])
    if len(df) < initial_count:
        logger.warning(f"Dropped {initial_count - len(df)} rows with missing molecular_weight")
    
    return df

def calculate_mw_stats(df: pd.DataFrame) -> Dict[str, float]:
    """Calculate basic statistics for molecular weight."""
    mw = df['molecular_weight']
    return {
        'mean': float(mw.mean()),
        'std': float(mw.std()),
        'min': float(mw.min()),
        'max': float(mw.max()),
        'median': float(mw.median())
    }

def stratified_split_by_mw(
    df: pd.DataFrame, 
    test_ratio: float = 0.2, 
    seed: int = 42
) -> Tuple[List[int], List[int]]:
    """
    Perform a stratified split based on Molecular Weight bins.
    This ensures the distribution of MW is similar in train and test sets.
    """
    set_seed(seed)
    logger = get_logger()
    
    n_samples = len(df)
    n_test = int(n_samples * test_ratio)
    n_train = n_samples - n_test
    
    if n_test == 0:
        raise ValueError("Dataset too small for the requested test ratio.")
    
    # Create bins for stratification
    # Use quantiles to ensure balanced distribution across bins
    n_bins = 10
    try:
        bins = np.quantile(df['molecular_weight'].values, np.linspace(0, 1, n_bins + 1))
        # Ensure unique bins if data is constant in some regions
        bins = np.unique(bins)
        if len(bins) < 2:
            # Fallback to uniform bins if quantiles are identical
            bins = np.linspace(df['molecular_weight'].min(), df['molecular_weight'].max(), n_bins + 1)
        
        # Assign bins
        labels = pd.cut(df['molecular_weight'], bins=bins, labels=False, include_lowest=True)
    except Exception as e:
        logger.warning(f"Quantile binning failed ({e}), falling back to uniform binning.")
        # Fallback: uniform bins
        n_bins = 10
        bins = np.linspace(df['molecular_weight'].min(), df['molecular_weight'].max(), n_bins + 1)
        labels = pd.cut(df['molecular_weight'], bins=bins, labels=False, include_lowest=True)

    # Stratified split
    train_indices = []
    test_indices = []
    
    for label in range(len(bins) - 1):
        indices = df[labels == label].index.tolist()
        if not indices:
            continue
        
        # Shuffle indices within the bin
        np.random.shuffle(indices)
        
        # Split
        n_bin_test = max(1, int(len(indices) * test_ratio)) if len(indices) > 1 else 0
        # Ensure we don't take all if we need some for train, unless it's 1 item
        if len(indices) == 1:
            n_bin_test = 0 # Put the single item in train if possible, or handle logic
            # Actually, standard stratified split usually puts the item in train if n=1
            # Let's strictly follow ratio but ensure at least 1 in train if possible
            n_bin_test = 0
        
        test_indices.extend(indices[:n_bin_test])
        train_indices.extend(indices[n_bin_test:])
    
    logger.info(f"Split complete. Train: {len(train_indices)}, Test: {len(test_indices)}")
    return train_indices, test_indices

def validate_split_distribution(
    train_df: pd.DataFrame, 
    test_df: pd.DataFrame
) -> Tuple[float, bool]:
    """
    Perform Kolmogorov-Smirnov test to check if train and test MW distributions are similar.
    Returns (p_value, is_valid) where is_valid is True if p > 0.05.
    """
    train_mw = train_df['molecular_weight'].values
    test_mw = test_df['molecular_weight'].values
    
    statistic, p_value = stats.ks_2samp(train_mw, test_mw)
    is_valid = p_value > 0.05
    
    return float(p_value), is_valid

def save_indices_to_csv(
    indices: List[int], 
    output_path: Path, 
    column_name: str = 'index'
) -> None:
    """Save indices to a CSV file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow([column_name])
        for idx in indices:
            writer.writerow([idx])

def main():
    """
    Main entry point for T016: Data Splitting.
    - Loads paired_dataset.parquet
    - Stratified split by MW
    - KS test
    - Outputs: train_indices.csv, test_indices.csv, split_report.json
    """
    logger = get_logger()
    logger.info("Starting T016: Data Splitting")
    
    project_root = get_project_root()
    output_dir = project_root / "data" / "splits"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Load data
    try:
        df = load_processed_data()
    except Exception as e:
        logger.error(f"Failed to load processed data: {e}")
        sys.exit(1)
    
    logger.info(f"Loaded {len(df)} molecules.")
    
    # Configuration
    test_ratio = 0.2
    current_seed = RANDOM_SEED
    max_retries = 1 # T016 does the split, T016-Gate handles retries logic if needed, 
                    # but T016 must run once. The task says "retry... up to 5 times" in T016-Gate.
                    # T016 just runs the split logic.
    
    # Perform split
    train_indices, test_indices = stratified_split_by_mw(df, test_ratio=test_ratio, seed=current_seed)
    
    # Create DataFrames for validation
    train_df = df.iloc[train_indices]
    test_df = df.iloc[test_indices]
    
    # Validate distribution
    p_value, is_valid = validate_split_distribution(train_df, test_df)
    
    logger.info(f"KS Test p-value: {p_value:.4f} (Valid: {is_valid})")
    
    # Save indices
    train_path = output_dir / "train_indices.csv"
    test_path = output_dir / "test_indices.csv"
    
    save_indices_to_csv(train_indices, train_path)
    save_indices_to_csv(test_indices, test_path)
    
    logger.info(f"Saved train indices to {train_path}")
    logger.info(f"Saved test indices to {test_path}")
    
    # Generate split report
    report = {
        "ks_p_value": p_value,
        "used_seed": current_seed,
        "train_count": len(train_indices),
        "test_count": len(test_indices),
        "total_count": len(df),
        "is_distribution_valid": is_valid
    }
    
    report_path = output_dir / "split_report.json"
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Saved split report to {report_path}")
    
    # If p <= 0.05, generate error report as per task description
    if not is_valid:
        error_report = {
            "ks_p_value": p_value,
            "used_seed": current_seed,
            "message": "KS test p-value <= 0.05. Distributions differ significantly.",
            "train_mean_mw": float(train_df['molecular_weight'].mean()),
            "test_mean_mw": float(test_df['molecular_weight'].mean()),
            "train_std_mw": float(train_df['molecular_weight'].std()),
            "test_std_mw": float(test_df['molecular_weight'].std())
        }
        error_path = output_dir / "split_error_report.json"
        with open(error_path, 'w') as f:
            json.dump(error_report, f, indent=2)
        logger.warning(f"Split distribution invalid. Saved error report to {error_path}")
    
    logger.info("T016 completed.")

if __name__ == "__main__":
    main()