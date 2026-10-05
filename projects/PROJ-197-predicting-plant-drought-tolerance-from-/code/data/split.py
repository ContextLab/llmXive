"""
Data splitting module for train-test split.

Implements stratified split and fallback to leave-one-out.
"""
import os
import sys
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Tuple, Optional, Dict, Any, List

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
    
    # Check for small N (Fallback to LOO logic if N is very small)
    # FR-003: Fallback to leave-one-out if N is small
    if len(df) < 10:
        logger.warning(f"Dataset too small ({len(df)} samples) for standard stratified split. Using leave-one-out logic (simulated by small test set).")
        # For very small N, we simulate LOO by setting test_size to 1/N
        # but sklearn's stratify requires at least 2 samples per class.
        # If we have < 2 classes or < 2 samples total, we just split 50/50 without stratify.
        if len(df[target_col].unique()) < 2 or len(df) < 2:
            logger.warning("Cannot stratify: insufficient classes or samples. Dropping stratification.")
            train_df, test_df = train_test_split(
                df,
                test_size=0.5,
                random_state=random_state
            )
        else:
            # Attempt stratified split with minimal test size (1 sample if possible)
            try:
                train_df, test_df = train_test_split(
                    df,
                    test_size=1.0/len(df), # Attempt 1 sample test set
                    stratify=df[target_col],
                    random_state=random_state
                )
            except ValueError:
                # If stratify fails (e.g., class count < 2 in test), fallback to non-stratified
                logger.warning("Stratification failed for small N. Dropping stratification.")
                train_df, test_df = train_test_split(
                    df,
                    test_size=0.5,
                    random_state=random_state
                )
    else:
        # Standard stratified split
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
        "train_pos": int(train_df[target_col].sum()),
        "test_pos": int(test_df[target_col].sum()),
        "train_neg": int(len(train_df) - train_df[target_col].sum()),
        "test_neg": int(len(test_df) - test_df[target_col].sum())
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
    # Ensure output directory exists
    ensure_directories([DATA_PROCESSED])
    
    # Save test data for evaluation and comparison
    test_path = DATA_PROCESSED / "test_data.npz"
    
    # Prepare arrays
    # Ensure feature_names are actually in the dataframe
    available_features = [f for f in feature_names if f in test_df.columns]
    if len(available_features) != len(feature_names):
        missing = set(feature_names) - set(available_features)
        logger.warning(f"Features missing in test data: {missing}. Using available: {available_features}")
    
    X_test = test_df[available_features].values
    y_test = test_df["drought_tolerance"].values
    
    np.savez(
        test_path,
        X=X_test,
        y=y_test,
        feature_names=np.array(available_features)
    )
    
    # Also save train data for training scripts
    train_path = DATA_PROCESSED / "train_data.npz"
    X_train = train_df[available_features].values
    y_train = train_df["drought_tolerance"].values
    np.savez(
        train_path,
        X=X_train,
        y=y_train,
        feature_names=np.array(available_features)
    )
    
    logger.info(f"Test data saved to {test_path}")
    logger.info(f"Train data saved to {train_path}")

def main():
    """Main entry point for splitting."""
    logger.info("Starting data split")
    
    # Load merged dataset
    path = DATA_PROCESSED / "merged_dataset.csv"
    if not path.exists():
        raise FileNotFoundError(f"Merged dataset not found at {path}. Please run ingest.py first.")
    
    df = pd.read_csv(path)
    
    if df.empty:
        raise ValueError("Merged dataset is empty.")
    
    # Identify features (exclude species_id and target)
    target_col = "drought_tolerance"
    if target_col not in df.columns:
        raise ValueError(f"Target column '{target_col}' not found in dataset. Available columns: {list(df.columns)}")
        
    feature_names = [col for col in df.columns if col not in ["species_id", target_col]]
    
    if not feature_names:
        raise ValueError("No features found to split on.")
    
    # Split
    train_df, test_df = perform_stratified_split(df, target_col=target_col)
    
    # Save metadata and data files
    save_split_metadata(train_df, test_df, feature_names)
    
    logger.info("Data split complete")
    return train_df, test_df

if __name__ == "__main__":
    main()