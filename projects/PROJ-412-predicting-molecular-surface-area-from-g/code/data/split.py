import os
import sys
import csv
import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import numpy as np
import pandas as pd
from scipy import stats

# Import project utilities
from utils.config import get_project_root, get_data_dir
from utils.logging import get_logger
from utils.seed import set_seed

# Ensure path to utils is available if running as script
project_root = get_project_root()
if str(project_root / "code") not in sys.path:
    sys.path.insert(0, str(project_root / "code"))

logger = get_logger(__name__)

class SplitResult:
    def __init__(self, train_indices: List[int], test_indices: List[int], p_value: float, success: bool):
        self.train_indices = train_indices
        self.test_indices = test_indices
        self.p_value = p_value
        self.success = success

def load_processed_data(data_dir: Path) -> pd.DataFrame:
    """
    Loads the processed dataset containing SMILES, molecular_weight, and surface_area.
    Expects 'data/processed/graphs_with_features.parquet' as created by T014c.
    """
    input_path = data_dir / "processed" / "graphs_with_features.parquet"
    if not input_path.exists():
        raise FileNotFoundError(f"Required input file not found: {input_path}. "
                                "Ensure T014c has been executed successfully.")
    
    df = pd.read_parquet(input_path)
    required_cols = ['molecular_weight', 'surface_area']
    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Input dataset missing required columns: {missing_cols}")
    
    return df

def calculate_mw_stats(df: pd.DataFrame) -> Dict[str, Any]:
    """Calculates basic statistics for Molecular Weight."""
    mw = df['molecular_weight']
    return {
        'mean': float(mw.mean()),
        'std': float(mw.std()),
        'min': float(mw.min()),
        'max': float(mw.max()),
        'count': int(len(mw))
    }

def stratified_split_by_mw(df: pd.DataFrame, test_ratio: float = 0.2, seed: int = 42) -> Tuple[List[int], List[int]]:
    """
    Performs a stratified split based on Molecular Weight bins to ensure
    similar distributions in train and test sets.
    """
    set_seed(seed)
    n = len(df)
    n_test = int(n * test_ratio)
    
    # Create bins for stratification (e.g., 10 bins)
    # Using quantile-based binning ensures roughly equal sized bins
    try:
        bins = pd.qcut(df['molecular_weight'], q=10, duplicates='drop')
    except ValueError:
        # Fallback to uniform bins if unique values are too few
        logger.warning("Quantile binning failed, using uniform bins.")
        bins = pd.cut(df['molecular_weight'], bins=10)
    
    df['stratification_bin'] = bins
    
    # Stratified split using sklearn
    try:
        from sklearn.model_selection import train_test_split
        indices = df.index.tolist()
        train_idx, test_idx = train_test_split(
            indices, 
            test_size=test_ratio, 
            stratify=df['stratification_bin'], 
            random_state=seed
        )
    except ImportError:
        logger.warning("sklearn not found, falling back to manual stratified split.")
        # Manual implementation
        train_idx = []
        test_idx = []
        unique_bins = df['stratification_bin'].unique()
        for b in unique_bins:
            bin_indices = df[df['stratification_bin'] == b].index.tolist()
            np.random.shuffle(bin_indices)
            n_bin_test = int(len(bin_indices) * test_ratio)
            test_idx.extend(bin_indices[:n_bin_test])
            train_idx.extend(bin_indices[n_bin_test:])
    
    return train_idx, test_idx

def validate_split_distribution(df: pd.DataFrame, train_indices: List[int], test_indices: List[int]) -> Tuple[float, bool]:
    """
    Validates the split by performing a Kolmogorov-Smirnov (KS) test
    on the Molecular Weight distributions of the train and test sets.
    Returns (p_value, is_valid) where is_valid is True if p > 0.05.
    """
    train_mw = df.loc[train_indices, 'molecular_weight'].values
    test_mw = df.loc[test_indices, 'molecular_weight'].values
    
    # KS Test
    statistic, p_value = stats.ks_2samp(train_mw, test_mw)
    
    is_valid = p_value > 0.05
    
    logger.info(f"KS Test Statistic: {statistic:.6f}")
    logger.info(f"KS Test P-value: {p_value:.6f}")
    if is_valid:
        logger.info("Split validation PASSED: Distributions are statistically similar (p > 0.05).")
    else:
        logger.error("Split validation FAILED: Distributions differ significantly (p <= 0.05).")
    
    return p_value, is_valid

def save_indices_to_csv(indices: List[int], filepath: Path):
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
    Main entry point for T015: Data Splitting.
    1. Loads processed data.
    2. Splits data stratified by Molecular Weight.
    3. Validates split using KS test.
    4. Saves indices and report.
    """
    project_root = get_project_root()
    data_dir = get_data_dir()
    splits_dir = data_dir / "splits"
    
    logger.info("Starting Data Splitting (T015)...")
    
    # 1. Load Data
    try:
        df = load_processed_data(data_dir)
        logger.info(f"Loaded {len(df)} molecules from processed data.")
    except Exception as e:
        logger.critical(f"Failed to load processed data: {e}")
        sys.exit(1)
    
    # 2. Stratified Split
    train_indices, test_indices = stratified_split_by_mw(df, test_ratio=0.2, seed=42)
    logger.info(f"Split completed: Train={len(train_indices)}, Test={len(test_indices)}")
    
    # 3. Validate Distribution (KS Test)
    p_value, is_valid = validate_split_distribution(df, train_indices, test_indices)
    
    if not is_valid:
        raise RuntimeError(
            f"Split validation failed: KS test p-value ({p_value:.6f}) <= 0.05. "
            "The train and test sets have significantly different Molecular Weight distributions."
        )
    
    # 4. Save Outputs
    # Ensure directory exists
    splits_dir.mkdir(parents=True, exist_ok=True)
    
    train_path = splits_dir / "train_indices.csv"
    test_path = splits_dir / "test_indices.csv"
    report_path = splits_dir / "split_report.json"
    
    save_indices_to_csv(train_indices, train_path)
    save_indices_to_csv(test_indices, test_path)
    
    # Create report
    report = {
        "train_size": len(train_indices),
        "test_size": len(test_indices),
        "test_ratio": 0.2,
        "ks_test": {
            "statistic": float(stats.ks_2samp(
                df.loc[train_indices, 'molecular_weight'],
                df.loc[test_indices, 'molecular_weight']
            )[0]),
            "p_value": float(p_value),
            "threshold": 0.05,
            "passed": is_valid
        },
        "molecular_weight_stats": calculate_mw_stats(df),
        "seed": 42
    }
    
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Split report saved to {report_path}")
    logger.info("T015 Data Splitting completed successfully.")
    
    return report

if __name__ == "__main__":
    main()
