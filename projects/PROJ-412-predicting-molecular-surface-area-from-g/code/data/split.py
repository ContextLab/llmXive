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

from utils.logging import get_logger
from utils.seed import set_seed
from utils.config import get_data_dir

logger = get_logger(__name__)

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
    train_size: int
    test_size: int

def load_processed_data() -> pd.DataFrame:
    """
    Loads the processed dataset containing SMILES, molecular_weight, and SASA.
    Expects the file at data/processed/graphs_with_features.parquet.
    """
    data_dir = get_data_dir()
    input_path = data_dir / "processed" / "graphs_with_features.parquet"
    
    if not input_path.exists():
        raise FileNotFoundError(
            f"Required input file not found: {input_path}. "
            "Please run T014 (preprocess) to generate molecular weights "
            "and T015 (conformer generation) to generate SASA before running split."
        )
    
    logger.info(f"Loading processed data from {input_path}")
    df = pd.read_parquet(input_path)
    
    required_cols = ['smiles', 'molecular_weight', 'sasa']
    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Input data missing required columns: {missing_cols}")
    
    # Drop rows with missing MW or SASA
    initial_count = len(df)
    df = df.dropna(subset=required_cols)
    dropped = initial_count - len(df)
    if dropped > 0:
        logger.warning(f"Dropped {dropped} rows due to missing MW or SASA values.")
    
    logger.info(f"Loaded {len(df)} molecules for splitting.")
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
    n_bins: int = 10, 
    random_state: int = 42
) -> SplitResult:
    """
    Performs a stratified split based on Molecular Weight bins.
    Ensures the distribution of MW in train and test sets is similar.
    """
    set_seed(random_state)
    
    logger.info(f"Performing stratified split by Molecular Weight (test_ratio={test_ratio}, bins={n_bins})")
    
    mw = df['molecular_weight'].values
    
    # Create bins based on MW distribution
    # Using quantile-based binning to ensure roughly equal numbers per bin
    # This helps stratification work better on skewed distributions
    try:
        bins = np.percentile(mw, np.linspace(0, 100, n_bins + 1))
        # Ensure unique bins if data is too uniform
        bins = np.unique(bins)
        if len(bins) < 2:
            logger.warning("MW distribution is too uniform for binning. Using uniform split.")
            bins = np.array([mw.min(), mw.max()])
    except Exception as e:
        logger.error(f"Error creating MW bins: {e}")
        raise
    
    # Assign bin labels
    bin_labels = np.digitize(mw, bins[1:-1])
    
    # Stratified split
    train_indices = []
    test_indices = []
    
    # We need to keep track of original indices
    original_indices = df.index.tolist()
    
    for bin_id in range(len(bins) - 1):
        # Get indices for this bin
        bin_mask = bin_labels == bin_id
        bin_indices = [original_indices[i] for i, val in enumerate(bin_mask) if val]
        
        if not bin_indices:
            continue
        
        # Shuffle within bin
        np.random.shuffle(bin_indices)
        
        # Split
        split_point = int(len(bin_indices) * (1 - test_ratio))
        train_indices.extend(bin_indices[:split_point])
        test_indices.extend(bin_indices[split_point:])
    
    # Create DataFrames for KS test
    train_df = df.loc[train_indices]
    test_df = df.loc[test_indices]
    
    # Kolmogorov-Smirnov test
    ks_stat, ks_p = stats.ks_2samp(train_df['molecular_weight'], test_df['molecular_weight'])
    
    logger.info(f"KS Test: Statistic={ks_stat:.4f}, P-value={ks_p:.4f}")
    
    if ks_p <= 0.05:
        error_msg = (
            f"Split failed KS test (p={ks_p:.4f} <= 0.05). "
            "The training and test sets have significantly different MW distributions."
        )
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    stats_result = SplitResult(
        train_indices=train_indices,
        test_indices=test_indices,
        ks_statistic=ks_stat,
        ks_p_value=ks_p,
        train_mw_mean=float(train_df['molecular_weight'].mean()),
        test_mw_mean=float(test_df['molecular_weight'].mean()),
        train_mw_std=float(train_df['molecular_weight'].std()),
        test_mw_std=float(test_df['molecular_weight'].std()),
        train_size=len(train_indices),
        test_size=len(test_indices)
    )
    
    logger.info(f"Split successful. Train: {len(train_indices)}, Test: {len(test_indices)}")
    logger.info(f"Train MW: mean={stats_result.train_mw_mean:.2f}, std={stats_result.train_mw_std:.2f}")
    logger.info(f"Test MW: mean={stats_result.test_mw_mean:.2f}, std={stats_result.test_mw_std:.2f}")
    
    return stats_result

def validate_split_distribution(train_df: pd.DataFrame, test_df: pd.DataFrame) -> bool:
    """
    Additional validation to ensure no data leakage and reasonable distribution overlap.
    """
    # Check for index overlap (should be impossible with our logic, but safety check)
    if set(train_df.index) & set(test_df.index):
        logger.error("Data leakage detected: indices overlap between train and test.")
        return False
    
    return True

def save_indices_to_csv(indices: List[int], filepath: Path) -> None:
    """Saves a list of indices to a CSV file."""
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['index'])
        for idx in indices:
            writer.writerow([idx])
    logger.info(f"Saved indices to {filepath} ({len(indices)} rows)")

def main():
    """
    Main entry point for the data splitting task.
    Generates train_indices.csv, test_indices.csv, and split_report.json.
    """
    logger.info("Starting T016: Data Splitting")
    
    # 1. Load data
    df = load_processed_data()
    
    # 2. Perform stratified split
    try:
        split_result = stratified_split_by_mw(df)
    except ValueError as e:
        logger.critical(str(e))
        sys.exit(1)
    
    # 3. Save indices
    splits_dir = get_data_dir() / "splits"
    splits_dir.mkdir(parents=True, exist_ok=True)
    
    train_path = splits_dir / "train_indices.csv"
    test_path = splits_dir / "test_indices.csv"
    
    save_indices_to_csv(split_result.train_indices, train_path)
    save_indices_to_csv(split_result.test_indices, test_path)
    
    # 4. Generate and save report
    report = {
        "ks_statistic": split_result.ks_statistic,
        "ks_p_value": split_result.ks_p_value,
        "train_size": split_result.train_size,
        "test_size": split_result.test_size,
        "train_mw_stats": {
            "mean": split_result.train_mw_mean,
            "std": split_result.train_mw_std
        },
        "test_mw_stats": {
            "mean": split_result.test_mw_mean,
            "std": split_result.test_mw_std
        },
        "split_ratio": split_result.test_size / (split_result.train_size + split_result.test_size),
        "status": "success"
    }
    
    report_path = splits_dir / "split_report.json"
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Split report saved to {report_path}")
    logger.info("T016 completed successfully.")
    
    return report

if __name__ == "__main__":
    main()