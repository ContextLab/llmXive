"""
Data splitting utilities for molecular permeability datasets.

Implements stratified and random splitting strategies with strict validation
for polymer type stratification as required by FR-003.
Supports fallback to random split when stratification metadata is missing
(common in Proxy Mode datasets), logging the deviation as a staged/feasibility mode.
"""

import logging
import yaml
from typing import List, Tuple, Optional
import pandas as pd
from sklearn.model_selection import train_test_split
from pathlib import Path

logger = logging.getLogger(__name__)

def _load_config() -> dict:
    """Load configuration from config.yaml in the project root."""
    config_path = Path(__file__).resolve().parent.parent.parent / "config.yaml"
    if not config_path.exists():
        logger.warning(f"Config file not found at {config_path}. Using defaults.")
        return {"staged_mode": False, "stratification_diff_threshold": 0.05}
    
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)

def random_split(
    df: pd.DataFrame,
    test_size: float = 0.2,
    random_state: int = 42
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Perform a simple random split of the dataframe.

    Args:
        df: Input dataframe containing molecular data.
        test_size: Proportion of the dataset to include in the test split.
        random_state: Seed for reproducibility.

    Returns:
        Tuple of (train_df, test_df).
    """
    if test_size <= 0 or test_size >= 1:
        raise ValueError("test_size must be between 0 and 1 (exclusive).")
    
    train_df, test_df = train_test_split(
        df, 
        test_size=test_size, 
        random_state=random_state, 
        shuffle=True
    )
    
    logger.info(f"Random split completed: Train={len(train_df)}, Test={len(test_df)}")
    return train_df, test_df


def stratified_split(
    df: pd.DataFrame,
    stratify_col: str,
    test_size: float = 0.2,
    random_state: int = 42,
    max_distribution_diff: Optional[float] = None
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Perform a stratified split ensuring distribution difference < threshold.
    
    This function enforces FR-003 by requiring the stratification column to exist
    and validating that the distribution difference between train and test sets
    does not exceed the specified threshold (default 5%).

    Args:
        df: Input dataframe.
        stratify_col: Column name to stratify by (e.g., 'polymer_type').
        test_size: Proportion of the dataset for the test split.
        random_state: Random seed for reproducibility.
        max_distribution_diff: Maximum allowed absolute percentage point difference
                             in class distribution between train and test sets.
                             If None, loads from config.yaml.

    Returns:
        Tuple of (train_df, test_df).

    Raises:
        SystemExit: If the stratification column is missing or if the distribution
                    difference exceeds the threshold after splitting.
        ValueError: If the stratification column has insufficient unique values.
    """
    config = _load_config()
    if max_distribution_diff is None:
        max_distribution_diff = config.get("stratification_diff_threshold", 0.05)

    if stratify_col not in df.columns:
        logger.error(
            f"Stratification column '{stratify_col}' not found in dataframe. "
            f"Available columns: {list(df.columns)}"
        )
        raise SystemExit(
            f"Stratification by {stratify_col} required by FR-003. "
            f"Dataset lacks this metadata."
        )

    if df[stratify_col].isna().any():
        logger.warning(f"Found NaN values in stratification column '{stratify_col}'. Dropping rows.")
        df = df.dropna(subset=[stratify_col])

    if df[stratify_col].nunique() < 2:
        logger.error(f"Stratification column '{stratify_col}' has fewer than 2 unique classes.")
        raise ValueError(
            f"Cannot stratify by '{stratify_col}': only {df[stratify_col].nunique()} unique class found."
        )

    try:
        train_df, test_df = train_test_split(
            df,
            test_size=test_size,
            random_state=random_state,
            stratify=df[stratify_col],
            shuffle=True
        )
    except ValueError as e:
        # Handle cases where stratification fails due to small class sizes
        logger.error(f"Stratified split failed: {e}")
        raise SystemExit(
            f"Stratified split failed. Ensure each class in '{stratify_col}' has sufficient samples "
            f"to support a {test_size*100:.0f}% test split."
        )

    # Validate distribution difference
    train_dist = train_df[stratify_col].value_counts(normalize=True).sort_index()
    test_dist = test_df[stratify_col].value_counts(normalize=True).sort_index()
    
    # Align indices to handle missing classes in one split (though unlikely with stratify)
    all_classes = train_dist.index.union(test_dist.index)
    train_dist = train_dist.reindex(all_classes, fill_value=0)
    test_dist = test_dist.reindex(all_classes, fill_value=0)

    diff = (train_dist - test_dist).abs()
    max_diff = diff.max()

    logger.info(f"Stratification column: {stratify_col}")
    logger.info(f"Train distribution:\n{train_dist}")
    logger.info(f"Test distribution:\n{test_dist}")
    logger.info(f"Max distribution difference: {max_diff:.4f} (threshold: {max_distribution_diff})")

    if max_diff > max_distribution_diff:
        logger.error(
            f"Stratification failed: Max distribution difference ({max_diff:.4f}) exceeds "
            f"threshold ({max_distribution_diff})."
        )
        raise SystemExit(
            f"Stratification validation failed. Distribution difference ({max_diff:.4f}) "
            f"exceeds allowed threshold ({max_distribution_diff}). "
            f"Consider adjusting test_size or checking dataset balance."
        )

    logger.info(f"Stratified split successful: Train={len(train_df)}, Test={len(test_df)}")
    return train_df, test_df


def execute_split(
    df: pd.DataFrame,
    output_dir: str,
    test_size: float = 0.2,
    random_state: int = 42,
    stratify_column: str = "polymer_type"
) -> Tuple[str, str]:
    """
    Main entry point for splitting data.
    
    Implements the logic for T017:
    1. Check if 'polymer_type' (or configured stratify_column) exists.
    2. If yes, perform stratified split.
    3. If no, perform random split with a warning about Proxy Mode/Feasibility.
    4. Save outputs to data/processed/train.csv and data/processed/test.csv.
    
    Args:
        df: The preprocessed dataframe.
        output_dir: Directory to save the split CSVs.
        test_size: Proportion for test set.
        random_state: Random seed.
        stratify_column: The column to stratify by if available.
        
    Returns:
        Tuple of (path_to_train_csv, path_to_test_csv).
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    train_path = output_path / "train.csv"
    test_path = output_path / "test.csv"
    
    config = _load_config()
    staged_mode = config.get("staged_mode", False)
    
    if stratify_column in df.columns:
        logger.info(f"Found stratification column '{stratify_column}'. Performing stratified split.")
        train_df, test_df = stratified_split(
            df, 
            stratify_col=stratify_column, 
            test_size=test_size, 
            random_state=random_state
        )
        strategy = "stratified"
    else:
        warning_msg = (
            f"Stratification by '{stratify_column}' skipped; fallback to "
            "staged/feasibility mode random split due to missing metadata."
        )
        logger.warning(warning_msg)
        logger.warning("This indicates Proxy Mode or a dataset lacking polymer metadata.")
        
        train_df, test_df = random_split(
            df, 
            test_size=test_size, 
            random_state=random_state
        )
        strategy = "random (fallback)"
    
    # Save to CSV
    train_df.to_csv(train_path, index=False)
    test_df.to_csv(test_path, index=False)
    
    logger.info(f"Split saved to: {train_path} and {test_path}")
    logger.info(f"Strategy used: {strategy}")
    logger.info(f"Train size: {len(train_df)}, Test size: {len(test_df)}")
    
    return str(train_path), str(test_path)

def main():
    """
    CLI entry point for T017.
    Expects a preprocessed CSV file path as argument.
    """
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="Split molecular data for training/testing.")
    parser.add_argument("--input", type=str, required=True, help="Path to preprocessed CSV (e.g., data/interim/preprocessed.csv)")
    parser.add_argument("--output", type=str, default="data/processed", help="Output directory for train/test splits")
    parser.add_argument("--test-size", type=float, default=0.2, help="Test set ratio")
    parser.add_argument("--stratify-col", type=str, default="polymer_type", help="Column to stratify by")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    
    args = parser.parse_args()
    
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    if not Path(args.input).exists():
        logger.error(f"Input file not found: {args.input}")
        sys.exit(1)
        
    logger.info(f"Loading data from {args.input}...")
    df = pd.read_csv(args.input)
    
    if df.empty:
        logger.error("Input dataframe is empty.")
        sys.exit(1)
        
    logger.info(f"Loaded {len(df)} rows. Columns: {list(df.columns)}")
    
    try:
        train_path, test_path = execute_split(
            df, 
            output_dir=args.output, 
            test_size=args.test_size, 
            random_state=args.seed, 
            stratify_column=args.stratify_col
        )
        logger.info(f"Successfully split data. Train: {train_path}, Test: {test_path}")
    except SystemExit as e:
        logger.error(f"Split process terminated: {e}")
        sys.exit(1)
    except Exception as e:
        logger.exception(f"Unexpected error during split: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
