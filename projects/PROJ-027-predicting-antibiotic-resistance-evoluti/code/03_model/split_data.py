"""
Split data into training, validation, and test sets with stratification.

This module implements the initial stratified split required by FR-003.
It loads the mechanism-blind filtered feature matrix, ensures stratification
by resistance phenotype and antibiotic class, and splits the data into
train/val/test sets while maintaining the class distribution.
"""
import os
import sys
import logging
import argparse
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd
from sklearn.model_selection import train_test_split

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from utils.logging import get_logger
from utils.config import load_config, get_random_seed

logger = get_logger(__name__)


def load_filtered_matrix(input_path: Path) -> pd.DataFrame:
    """
    Load the mechanism-blind filtered feature matrix.

    Args:
        input_path: Path to the filtered feature matrix CSV.

    Returns:
        DataFrame with filtered features.
    """
    if not input_path.exists():
        raise FileNotFoundError(f"Filtered matrix not found: {input_path}")

    logger.info(f"Loading filtered matrix from {input_path}")
    df = pd.read_csv(input_path)

    # Validate required columns
    required_cols = ['isolate_id', 'resistance_phenotype', 'antibiotic_class']
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    logger.info(f"Loaded {len(df)} isolates with columns: {list(df.columns)}")
    return df


def validate_stratification(df: pd.DataFrame, target_col: str) -> None:
    """
    Validate that stratification is possible (enough samples per class).

    Args:
        df: DataFrame to validate.
        target_col: Column to stratify by.
    """
    class_counts = df[target_col].value_counts()
    min_count = class_counts.min()

    if min_count < 10:
        logger.warning(f"Stratification may be unreliable: min class count is {min_count}")
    else:
        logger.info(f"Stratification valid: min class count is {min_count}")


def split_data(
    df: pd.DataFrame,
    test_size: float = 0.2,
    val_size: float = 0.1,
    random_state: int = 42
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Split data into train, validation, and test sets with stratification.

    The split is performed in two steps:
    1. Split off test set (test_size)
    2. Split remaining into train and validation (val_size / (1 - test_size))

    Both splits are stratified by resistance_phenotype.

    Args:
        df: Input DataFrame.
        test_size: Fraction of data for test set.
        val_size: Fraction of data for validation set (relative to original).
        random_state: Random seed for reproducibility.

    Returns:
        Tuple of (train_df, val_df, test_df).
    """
    # Validate stratification column
    validate_stratification(df, 'resistance_phenotype')

    # First split: separate test set
    train_val_df, test_df = train_test_split(
        df,
        test_size=test_size,
        stratify=df['resistance_phenotype'],
        random_state=random_state,
        shuffle=True
    )

    # Second split: separate validation from training
    # Adjust val_size to be relative to train_val_df
    adjusted_val_size = val_size / (1 - test_size)
    train_df, val_df = train_test_split(
        train_val_df,
        test_size=adjusted_val_size,
        stratify=train_val_df['resistance_phenotype'],
        random_state=random_state,
        shuffle=True
    )

    logger.info(f"Split completed:")
    logger.info(f"  Train: {len(train_df)} ({len(train_df)/len(df)*100:.1f}%)")
    logger.info(f"  Val:   {len(val_df)} ({len(val_df)/len(df)*100:.1f}%)")
    logger.info(f"  Test:  {len(test_df)} ({len(test_df)/len(df)*100:.1f}%)")

    return train_df, val_df, test_df


def save_splits(
    train_df: pd.DataFrame,
    val_df: pd.DataFrame,
    test_df: pd.DataFrame,
    output_dir: Path,
    antibiotic_class: str
) -> Dict[str, str]:
    """
    Save the split datasets to CSV files.

    Args:
        train_df: Training set DataFrame.
        val_df: Validation set DataFrame.
        test_df: Test set DataFrame.
        output_dir: Directory to save files.
        antibiotic_class: Name of the antibiotic class for filenames.

    Returns:
        Dictionary mapping split names to file paths.
    """
    output_dir.mkdir(parents=True, exist_ok=True)

    file_paths = {}
    for name, df in [('train', train_df), ('val', val_df), ('test', test_df)]:
        filename = f"feature_matrix_{antibiotic_class}_{name}.csv"
        filepath = output_dir / filename
        df.to_csv(filepath, index=False)
        file_paths[name] = str(filepath)
        logger.info(f"Saved {name} set to {filepath} ({len(df)} rows)")

    return file_paths


def save_split_metadata(
    split_paths: Dict[str, str],
    antibiotic_class: str,
    random_state: int,
    output_dir: Path
) -> None:
    """
    Save metadata about the split for reproducibility.

    Args:
        split_paths: Dictionary of split names to file paths.
        antibiotic_class: Name of the antibiotic class.
        random_state: Random seed used.
        output_dir: Directory to save metadata.
    """
    metadata = {
        'antibiotic_class': antibiotic_class,
        'random_state': random_state,
        'split_files': split_paths,
        'row_counts': {
            'train': len(pd.read_csv(split_paths['train'])),
            'val': len(pd.read_csv(split_paths['val'])),
            'test': len(pd.read_csv(split_paths['test']))
        }
    }

    metadata_path = output_dir / f"split_metadata_{antibiotic_class}.json"
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)

    logger.info(f"Saved split metadata to {metadata_path}")


def main():
    """Main entry point for the data splitting script."""
    parser = argparse.ArgumentParser(
        description='Split filtered feature matrix into train/val/test sets.'
    )
    parser.add_argument(
        '--input',
        type=str,
        required=True,
        help='Path to the mechanism-blind filtered feature matrix CSV.'
    )
    parser.add_argument(
        '--output-dir',
        type=str,
        default='data/processed/splits',
        help='Directory to save split datasets.'
    )
    parser.add_argument(
        '--test-size',
        type=float,
        default=0.2,
        help='Fraction of data for test set (default: 0.2).'
    )
    parser.add_argument(
        '--val-size',
        type=float,
        default=0.1,
        help='Fraction of data for validation set (default: 0.1).'
    )
    parser.add_argument(
        '--antibiotic-class',
        type=str,
        required=True,
        help='Name of the antibiotic class for output filenames.'
    )
    parser.add_argument(
        '--config',
        type=str,
        default='config.yaml',
        help='Path to configuration file.'
    )

    args = parser.parse_args()

    # Setup logging
    setup_file_logging('split_data.log')

    # Load configuration for random seed
    try:
        config = load_config(args.config)
        random_state = get_random_seed(config)
    except Exception as e:
        logger.warning(f"Could not load config: {e}, using default seed 42")
        random_state = 42

    logger.info(f"Starting data split for antibiotic class: {args.antibiotic_class}")
    logger.info(f"Random seed: {random_state}")

    # Load filtered matrix
    input_path = Path(args.input)
    df = load_filtered_matrix(input_path)

    # Perform split
    train_df, val_df, test_df = split_data(
        df,
        test_size=args.test_size,
        val_size=args.val_size,
        random_state=random_state
    )

    # Save splits
    output_dir = Path(args.output_dir)
    split_paths = save_splits(train_df, val_df, test_df, output_dir, args.antibiotic_class)
    save_split_metadata(split_paths, args.antibiotic_class, random_state, output_dir)

    logger.info("Data split completed successfully.")
    return 0


if __name__ == '__main__':
    sys.exit(main())
