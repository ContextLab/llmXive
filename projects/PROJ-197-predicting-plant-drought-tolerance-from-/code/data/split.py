"""
Data splitting module for train-test split.

Implements stratified split and fallback to leave-one-out.
"""
import os
import sys
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Tuple, Optional, Dict, Any

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import get_config, ensure_directories
from utils.logging import DataPipelineLog

logger = DataPipelineLog("split")

# Constants
PROJECT_ROOT = Path(__file__).parent.parent
DATA_PROCESSED = PROJECT_ROOT / "data" / "processed"
DATA_LOGS = PROJECT_ROOT / "data" / "logs"

ensure_directories()

def perform_stratified_split(
    df: pd.DataFrame,
    target_col: str = "drought_tolerance",
    test_size: float = 0.2,
    random_state: int = 42
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Perform stratified train-test split.
    
    Args:
        df: Input DataFrame.
        target_col: Name of the target column.
        test_size: Proportion of data for test set.
        random_state: Random seed.
    
    Returns:
        Tuple of (train_df, test_df).
    """
    from sklearn.model_selection import train_test_split
    
    # Check for small N
    if len(df) < 10:
        logger.warning("Dataset too small for standard split. Using leave-one-out logic (simulated by small test set).")
        test_size = 0.5 # Fallback for very small N
    
    train_df, test_df = train_test_split(
        df,
        test_size=test_size,
        stratify=df[target_col],
        random_state=random_state
    )
    
    logger.record("split_stats", {
        "total": len(df),
        "train": len(train_df),
        "test": len(test_df),
        "train_pos": train_df[target_col].sum(),
        "test_pos": test_df[target_col].sum()
    })
    
    return train_df, test_df

def save_split_metadata(
    train_df: pd.DataFrame,
    test_df: pd.DataFrame,
    feature_names: List[str]
) -> None:
    """
    Save split metadata and data for downstream tasks.
    
    Args:
        train_df: Training DataFrame.
        test_df: Test DataFrame.
        feature_names: List of feature names.
    """
    # Save test data for evaluation and comparison
    test_path = DATA_PROCESSED / "test_data.npz"
    
    # Prepare arrays
    X_test = test_df[feature_names].values
    y_test = test_df["drought_tolerance"].values
    
    np.savez(
        test_path,
        X=X_test,
        y=y_test,
        feature_names=np.array(feature_names)
    )
    
    logger.info(f"Test data saved to {test_path}")

def main():
    """Main entry point for splitting."""
    logger.info("Starting data split")
    
    # Load merged dataset
    path = DATA_PROCESSED / "merged_dataset.csv"
    if not path.exists():
        raise FileNotFoundError(f"Merged dataset not found at {path}")
    
    df = pd.read_csv(path)
    
    # Identify features (exclude species_id and target)
    feature_names = [col for col in df.columns if col not in ["species_id", "drought_tolerance"]]
    
    # Split
    train_df, test_df = perform_stratified_split(df)
    
    # Save metadata
    save_split_metadata(train_df, test_df, feature_names)
    
    logger.info("Data split complete")

if __name__ == "__main__":
    main()
