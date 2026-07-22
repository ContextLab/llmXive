import os
import json
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from sklearn.model_selection import train_test_split

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_processed_data(input_path: str) -> pd.DataFrame:
    """
    Load the processed metrics data from the parser output.
    
    Args:
        input_path: Path to the CSV file containing parsed trajectory metrics.
        
    Returns:
        pd.DataFrame: The loaded dataset.
        
    Raises:
        FileNotFoundError: If the input file does not exist.
        ValueError: If the file is empty or missing required columns.
    """
    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    df = pd.read_csv(path)
    
    required_cols = ['trajectory_id', 'turn', 'health', 'threat', 'deck_size', 'entropy']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in {input_path}: {missing_cols}")
        
    if df.empty:
        raise ValueError(f"Input file {input_path} is empty.")
        
    logger.info(f"Loaded {len(df)} rows from {input_path}")
    return df

def stratified_split(
    df: pd.DataFrame,
    train_ratio: float = 0.5,
    ablation_train_ratio: float = 0.2,
    val_ratio: float = 0.15,
    test_ratio: float = 0.15,
    min_val_trajectories: int = 20,
    seed: int = 42
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Perform a stratified split of the data into four sets:
    Train, Ablation-Train, Validation, and Test.
    
    The split is performed at the TRAJECTORY level to prevent data leakage.
    We ensure the Validation set contains at least `min_val_trajectories` unique trajectories.
    
    Args:
        df: The input DataFrame with trajectory data.
        train_ratio: Fraction of data for training.
        ablation_train_ratio: Fraction for ablation training.
        val_ratio: Fraction for validation.
        test_ratio: Fraction for testing.
        min_val_trajectories: Minimum number of unique trajectories required in validation set.
        seed: Random seed for reproducibility.
        
    Returns:
        Tuple of (train_df, ablation_train_df, val_df, test_df).
        
    Raises:
        ValueError: If the dataset is too small to satisfy the validation constraint.
    """
    np.random.seed(seed)
    
    # Group by trajectory_id to get unique trajectories
    unique_trajectories = df['trajectory_id'].unique()
    n_total_trajectories = len(unique_trajectories)
    
    logger.info(f"Total unique trajectories: {n_total_trajectories}")
    
    if n_total_trajectories < (min_val_trajectories + 10):
        raise ValueError(
            f"Dataset too small: {n_total_trajectories} trajectories. "
            f"Need at least {min_val_trajectories} for validation plus others for splits."
        )
    
    # Shuffle trajectories
    shuffled_trajectories = np.random.permutation(unique_trajectories)
    
    # Calculate split indices based on trajectory counts
    n_test = int(n_total_trajectories * test_ratio)
    n_val = int(n_total_trajectories * val_ratio)
    n_ablation = int(n_total_trajectories * ablation_train_ratio)
    n_train = n_total_trajectories - n_test - n_val - n_ablation
    
    # Ensure minimum validation size
    if n_val < min_val_trajectories:
        # Adjust: take exactly min_val_trajectories for validation,
        # and redistribute the rest proportionally or take what's left
        n_val = min_val_trajectories
        # Recalculate remaining
        remaining = n_total_trajectories - n_val - n_test
        # Adjust train/ablation from remaining if necessary, but keep test fixed
        # For simplicity in this implementation, we prioritize the min_val constraint
        # and take the rest as train/ablation as calculated or adjusted
        if n_train + n_ablation > remaining:
            # Scale down train/ablation proportionally
            total_train_ablation = n_train + n_ablation
            n_train = int(remaining * (n_train / total_train_ablation))
            n_ablation = remaining - n_train
    
    # Split trajectory IDs
    test_ids = shuffled_trajectories[:n_test]
    val_ids = shuffled_trajectories[n_test:n_test + n_val]
    ablation_ids = shuffled_trajectories[n_test + n_val:n_test + n_val + n_ablation]
    train_ids = shuffled_trajectories[n_test + n_val + n_ablation:]
    
    logger.info(f"Split sizes -> Train: {len(train_ids)}, Ablation-Train: {len(ablation_ids)}, "
                f"Validation: {len(val_ids)}, Test: {len(test_ids)}")
    
    # Verify validation constraint
    if len(val_ids) < min_val_trajectories:
        raise ValueError(
            f"Validation set has {len(val_ids)} trajectories, "
            f"which is less than the required minimum of {min_val_trajectories}. "
            "Cannot proceed with split."
        )
    
    # Filter DataFrame
    train_df = df[df['trajectory_id'].isin(train_ids)].copy()
    ablation_train_df = df[df['trajectory_id'].isin(ablation_ids)].copy()
    val_df = df[df['trajectory_id'].isin(val_ids)].copy()
    test_df = df[df['trajectory_id'].isin(test_ids)].copy()
    
    return train_df, ablation_train_df, val_df, test_df

def save_split_data(
    train_df: pd.DataFrame,
    ablation_train_df: pd.DataFrame,
    val_df: pd.DataFrame,
    test_df: pd.DataFrame,
    output_dir: str,
    val_ids: List[str]
) -> None:
    """
    Save the split datasets to CSV files and the validation IDs to JSON.
    
    Args:
        train_df: Training set DataFrame.
        ablation_train_df: Ablation training set DataFrame.
        val_df: Validation set DataFrame.
        test_df: Test set DataFrame.
        output_dir: Directory to save the files.
        val_ids: List of trajectory IDs in the validation set.
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Save CSVs
    train_path = output_path / "train_set.csv"
    ablation_train_path = output_path / "ablation_train_set.csv"
    val_path = output_path / "validation_set.csv"
    test_path = output_path / "test_set.csv"
    
    train_df.to_csv(train_path, index=False)
    ablation_train_df.to_csv(ablation_train_path, index=False)
    val_df.to_csv(val_path, index=False)
    test_df.to_csv(test_path, index=False)
    
    logger.info(f"Saved {len(train_df)} rows to {train_path}")
    logger.info(f"Saved {len(ablation_train_df)} rows to {ablation_train_path}")
    logger.info(f"Saved {len(val_df)} rows to {val_path}")
    logger.info(f"Saved {len(test_df)} rows to {test_path}")
    
    # Save validation IDs
    val_ids_path = output_path / "validation_set_ids.json"
    with open(val_ids_path, 'w') as f:
        json.dump(val_ids, f, indent=2)
    logger.info(f"Saved {len(val_ids)} validation IDs to {val_ids_path}")

def validate_split(
    train_df: pd.DataFrame,
    ablation_train_df: pd.DataFrame,
    val_df: pd.DataFrame,
    test_df: pd.DataFrame,
    min_val_trajectories: int = 20
) -> bool:
    """
    Validate that the splits are disjoint and meet constraints.
    
    Returns:
        True if valid, raises ValueError otherwise.
    """
    # Check disjoint sets
    sets = [
        ("Train", train_df['trajectory_id'].unique()),
        ("Ablation-Train", ablation_train_df['trajectory_id'].unique()),
        ("Validation", val_df['trajectory_id'].unique()),
        ("Test", test_df['trajectory_id'].unique())
    ]
    
    for i in range(len(sets)):
        for j in range(i + 1, len(sets)):
            name1, ids1 = sets[i]
            name2, ids2 = sets[j]
            intersection = set(ids1) & set(ids2)
            if intersection:
                raise ValueError(f"Overlap found between {name1} and {name2}: {len(intersection)} trajectories")
    
    # Check validation size
    if len(val_df['trajectory_id'].unique()) < min_val_trajectories:
        raise ValueError(f"Validation set has {len(val_df['trajectory_id'].unique())} trajectories, "
                         f"less than required {min_val_trajectories}")
                         
    logger.info("Split validation passed.")
    return True

def main():
    """
    Main entry point to run the splitter.
    Expected input: data/processed/metrics_with_moves.csv
    Expected output: data/processed/train_set.csv, ablation_train_set.csv, validation_set.csv, test_set.csv, validation_set_ids.json
    """
    # Configuration
    input_file = "data/processed/metrics_with_moves.csv"
    output_dir = "data/processed"
    min_val_trajectories = 20
    seed = 42
    
    # Ratios (sum should be 1.0)
    train_ratio = 0.50
    ablation_train_ratio = 0.20
    val_ratio = 0.15
    test_ratio = 0.15
    
    logger.info("Starting data split process...")
    
    try:
        # Load data
        df = load_processed_data(input_file)
        
        # Perform split
        train_df, ablation_train_df, val_df, test_df = stratified_split(
            df,
            train_ratio=train_ratio,
            ablation_train_ratio=ablation_train_ratio,
            val_ratio=val_ratio,
            test_ratio=test_ratio,
            min_val_trajectories=min_val_trajectories,
            seed=seed
        )
        
        # Validate
        validate_split(
            train_df, ablation_train_df, val_df, test_df,
            min_val_trajectories=min_val_trajectories
        )
        
        # Save
        val_ids = val_df['trajectory_id'].unique().tolist()
        save_split_data(
            train_df, ablation_train_df, val_df, test_df,
            output_dir, val_ids
        )
        
        logger.info("Split process completed successfully.")
        
    except FileNotFoundError as e:
        logger.error(f"Input file missing: {e}")
        raise
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during split: {e}")
        raise

if __name__ == "__main__":
    main()