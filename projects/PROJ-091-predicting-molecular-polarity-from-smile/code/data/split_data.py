"""
Data splitting utilities.

Implements T022: Standard random train/test split (no target stratification).
"""
import os
import sys
import logging
import pyarrow.parquet as pq
import numpy as np
from pathlib import Path
import pandas as pd

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from utils.logging_config import get_logger
from utils.config import load_hyperparameters

logger = get_logger(__name__)

def split_data(
    input_path: Path,
    output_dir: Path,
    test_size: float = 0.2,
    random_state: int = 42
):
    """
    Split the processed descriptors into train and test sets.

    Args:
        input_path: Path to the input parquet file (data/processed/descriptors.parquet).
        output_dir: Directory to save split files.
        test_size: Fraction of data to use for testing.
        random_state: Random seed for reproducibility.

    Returns:
        dict: Paths to the generated train/test files.
    """
    logger.info(f"Splitting data from {input_path}...")
    
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    # Load data
    df = pd.read_parquet(input_path)
    
    if 'target' not in df.columns:
        # Try to infer target column if not named 'target'
        # Assuming the last column is target or a specific name
        # For QM9, the target is usually a specific column. 
        # Let's assume 'target' is the column name as per previous tasks.
        raise ValueError("Column 'target' not found in input dataframe.")

    X = df.drop(columns=['target'])
    y = df['target']

    # Random split (no stratification)
    indices = np.arange(len(df))
    np.random.seed(random_state)
    np.random.shuffle(indices)

    split_idx = int(len(indices) * (1 - test_size))
    train_idx = indices[:split_idx]
    test_idx = indices[split_idx:]

    X_train = X.iloc[train_idx]
    y_train = y.iloc[train_idx]
    X_test = X.iloc[test_idx]
    y_test = y.iloc[test_idx]

    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)

    # Save splits
    train_X_path = output_dir / "train_X.parquet"
    train_y_path = output_dir / "train_y.parquet"
    test_X_path = output_dir / "test_X.parquet"
    test_y_path = output_dir / "test_y.parquet"

    X_train.to_parquet(train_X_path)
    y_train.to_parquet(train_y_path)
    X_test.to_parquet(test_X_path)
    y_test.to_parquet(test_y_path)

    logger.info(f"Saved train split: {X_train.shape}")
    logger.info(f"Saved test split: {X_test.shape}")

    return {
        "train_X": str(train_X_path),
        "train_y": str(train_y_path),
        "test_X": str(test_X_path),
        "test_y": str(test_y_path)
    }

def load_splits(splits_dir: Path):
    """
    Load split data paths from the splits directory.
    """
    if not splits_dir.exists():
        raise FileNotFoundError(f"Splits directory not found: {splits_dir}")

    return {
        "train_X": str(splits_dir / "train_X.parquet"),
        "train_y": str(splits_dir / "train_y.parquet"),
        "test_X": str(splits_dir / "test_X.parquet"),
        "test_y": str(splits_dir / "test_y.parquet")
    }

def main():
    """
    Entry point for T022.
    """
    input_file = Path("data/processed/descriptors.parquet")
    output_dir = Path("data/processed/splits")

    if not input_file.exists():
        logger.error(f"Input file {input_file} not found. Run preprocess_2d first.")
        sys.exit(1)

    config_path = Path("code/config.yaml")
    if config_path.exists():
        config = load_hyperparameters(config_path)
        test_size = config.get("test_size", 0.2)
        random_state = config.get("random_state", 42)
    else:
        test_size = 0.2
        random_state = 42

    try:
        splits = split_data(input_file, output_dir, test_size, random_state)
        logger.info(f"Splits saved to {output_dir}")
    except Exception as e:
        logger.error(f"Splitting failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
