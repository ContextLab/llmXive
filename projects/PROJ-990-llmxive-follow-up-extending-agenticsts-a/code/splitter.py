import os
import json
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
INPUT_FILE = "data/processed/metrics_with_moves.csv"
OUTPUT_DIR = "data/processed"
TRAIN_FILE = "data/processed/train_set.csv"
ABLATION_TRAIN_FILE = "data/processed/ablation_train_set.csv"
VALIDATION_FILE = "data/processed/validation_set.csv"
TEST_FILE = "data/processed/test_set.csv"
VALIDATION_IDS_FILE = "data/processed/validation_set_ids.json"
MIN_VALIDATION_SIZE = 20

def load_processed_data(input_path: str) -> pd.DataFrame:
    """Load the processed metrics CSV file."""
    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    logger.info(f"Loading data from {input_path}")
    df = pd.read_csv(path)
    
    # Validate required columns
    required_cols = ['trajectory_id', 'win_rate']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in input file: {missing_cols}")
    
    logger.info(f"Loaded {len(df)} rows from {input_path}")
    return df

def stratified_split(
    df: pd.DataFrame, 
    train_ratio: float = 0.6,
    ablation_train_ratio: float = 0.15,
    validation_ratio: float = 0.125,
    test_ratio: float = 0.125,
    seed: int = 42
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Perform a stratified split of the data into Train, Ablation-Train, Validation, and Test sets.
    
    Stratification is performed on 'win_rate'.
    The split ensures that the Validation set has at least MIN_VALIDATION_SIZE trajectories.
    
    Args:
        df: Input DataFrame with 'trajectory_id' and 'win_rate' columns.
        train_ratio: Proportion for training set.
        ablation_train_ratio: Proportion for ablation training set.
        validation_ratio: Proportion for validation set.
        test_ratio: Proportion for test set.
        seed: Random seed for reproducibility.
    
    Returns:
        Tuple of (train_df, ablation_train_df, validation_df, test_df)
    """
    if not np.isclose(train_ratio + ablation_train_ratio + validation_ratio + test_ratio, 1.0):
        raise ValueError("Ratios must sum to 1.0")
    
    # Ensure unique trajectories for stratification
    # If multiple rows per trajectory, we must split by trajectory_id, not by row
    # Group by trajectory_id and take the mean win_rate for stratification
    traj_stats = df.groupby('trajectory_id')['win_rate'].mean().reset_index()
    
    # Stratify based on binned win_rate to handle continuous variable
    # Create bins for stratification
    n_bins = 10
    traj_stats['win_rate_bin'] = pd.qcut(traj_stats['win_rate'], q=n_bins, duplicates='drop')
    
    # Set random seed
    np.random.seed(seed)
    
    # Perform stratified split on trajectory IDs
    # We use a manual approach to ensure exact ratios and minimum validation size
    train_ids = []
    ablation_train_ids = []
    validation_ids = []
    test_ids = []
    
    # Shuffle within each bin
    for _, group in traj_stats.groupby('win_rate_bin'):
        group_ids = group['trajectory_id'].values
        np.random.shuffle(group_ids)
        
        n = len(group_ids)
        n_train = int(n * train_ratio)
        n_ablation = int(n * ablation_train_ratio)
        n_val = int(n * validation_ratio)
        n_test = n - n_train - n_ablation - n_val
        
        # Adjust to ensure at least MIN_VALIDATION_SIZE in validation if possible
        # If the calculated n_val is too small, we might need to borrow from other sets
        # However, we strictly follow the ratios first, then check the constraint
        
        start = 0
        train_ids.extend(group_ids[start:start+n_train])
        start += n_train
        ablation_train_ids.extend(group_ids[start:start+n_ablation])
        start += n_ablation
        validation_ids.extend(group_ids[start:start+n_val])
        start += n_val
        test_ids.extend(group_ids[start:])
    
    # Validate minimum validation size
    if len(validation_ids) < MIN_VALIDATION_SIZE:
        raise ValueError(
            f"Validation set size ({len(validation_ids)}) is less than required minimum ({MIN_VALIDATION_SIZE}). "
            "Consider increasing the dataset size or adjusting split ratios."
        )
    
    logger.info(f"Stratified split completed:")
    logger.info(f"  Train: {len(train_ids)} trajectories")
    logger.info(f"  Ablation-Train: {len(ablation_train_ids)} trajectories")
    logger.info(f"  Validation: {len(validation_ids)} trajectories")
    logger.info(f"  Test: {len(test_ids)} trajectories")
    
    # Filter original DataFrame based on trajectory IDs
    train_df = df[df['trajectory_id'].isin(train_ids)].copy()
    ablation_train_df = df[df['trajectory_id'].isin(ablation_train_ids)].copy()
    validation_df = df[df['trajectory_id'].isin(validation_ids)].copy()
    test_df = df[df['trajectory_id'].isin(test_ids)].copy()
    
    return train_df, ablation_train_df, validation_df, test_df

def save_split_data(
    train_df: pd.DataFrame,
    ablation_train_df: pd.DataFrame,
    validation_df: pd.DataFrame,
    test_df: pd.DataFrame,
    validation_ids: List[str],
    output_dir: str
):
    """Save the split datasets and validation IDs to disk."""
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    
    # Save CSVs
    train_df.to_csv(Path(output_dir) / TRAIN_FILE, index=False)
    ablation_train_df.to_csv(Path(output_dir) / ABLATION_TRAIN_FILE, index=False)
    validation_df.to_csv(Path(output_dir) / VALIDATION_FILE, index=False)
    test_df.to_csv(Path(output_dir) / TEST_FILE, index=False)
    
    # Save validation IDs as JSON
    ids_file = Path(output_dir) / VALIDATION_IDS_FILE
    with open(ids_file, 'w') as f:
        json.dump(validation_ids, f, indent=2)
    
    logger.info(f"Saved split data to {output_dir}")
    logger.info(f"  Train: {TRAIN_FILE}")
    logger.info(f"  Ablation-Train: {ABLATION_TRAIN_FILE}")
    logger.info(f"  Validation: {VALIDATION_FILE}")
    logger.info(f"  Test: {TEST_FILE}")
    logger.info(f"  Validation IDs: {VALIDATION_IDS_FILE}")

def validate_split(
    train_df: pd.DataFrame,
    ablation_train_df: pd.DataFrame,
    validation_df: pd.DataFrame,
    test_df: pd.DataFrame
):
    """Validate that the split is correct and non-overlapping."""
    all_ids = (
        set(train_df['trajectory_id']) |
        set(ablation_train_df['trajectory_id']) |
        set(validation_df['trajectory_id']) |
        set(test_df['trajectory_id'])
    )
    
    # Check for overlaps
    intersections = {
        'Train & Ablation': set(train_df['trajectory_id']) & set(ablation_train_df['trajectory_id']),
        'Train & Validation': set(train_df['trajectory_id']) & set(validation_df['trajectory_id']),
        'Train & Test': set(train_df['trajectory_id']) & set(test_df['trajectory_id']),
        'Ablation & Validation': set(ablation_train_df['trajectory_id']) & set(validation_df['trajectory_id']),
        'Ablation & Test': set(ablation_train_df['trajectory_id']) & set(test_df['trajectory_id']),
        'Validation & Test': set(validation_df['trajectory_id']) & set(test_df['trajectory_id']),
    }
    
    for name, intersection in intersections.items():
        if intersection:
            raise ValueError(f"Overlap detected in {name}: {intersection}")
    
    logger.info("Split validation passed: No overlapping trajectory IDs found.")

def main():
    """Main entry point for the splitter script."""
    try:
        # Load data
        df = load_processed_data(INPUT_FILE)
        
        # Perform stratified split
        train_df, ablation_train_df, validation_df, test_df = stratified_split(df)
        
        # Validate split
        validate_split(train_df, ablation_train_df, validation_df, test_df)
        
        # Get validation IDs for JSON output
        validation_ids = validation_df['trajectory_id'].unique().tolist()
        
        # Save outputs
        save_split_data(
            train_df,
            ablation_train_df,
            validation_df,
            test_df,
            validation_ids,
            OUTPUT_DIR
        )
        
        logger.info("T014a: Split completed successfully.")
        
    except Exception as e:
        logger.error(f"T014a: Split failed with error: {e}")
        raise

if __name__ == "__main__":
    main()