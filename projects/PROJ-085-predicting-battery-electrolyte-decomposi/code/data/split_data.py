import os
import sys
import logging
from pathlib import Path
from typing import Tuple, Optional

import pandas as pd
from sklearn.model_selection import train_test_split

# Import project configuration and utilities
from config import get_processed_dir, get_seed, get_project_root
from data.checksum import compute_sha256, save_checksums

# Setup logger
logger = logging.getLogger(__name__)

def load_processed_features(filepath: Optional[str] = None) -> pd.DataFrame:
    """
    Loads the processed feature matrix from the data/processed directory.
    
    Args:
        filepath: Optional explicit path. If None, uses default from config.
        
    Returns:
        pd.DataFrame: The loaded feature matrix.
        
    Raises:
        FileNotFoundError: If the file does not exist.
    """
    if filepath is None:
        processed_dir = get_processed_dir()
        filepath = os.path.join(processed_dir, "electrolyte_features.csv")
    
    path_obj = Path(filepath)
    if not path_obj.exists():
        raise FileNotFoundError(f"Processed features file not found at: {filepath}")
    
    logger.info(f"Loading processed features from {filepath}")
    df = pd.read_csv(filepath)
    
    # Basic validation: ensure it's not empty
    if df.empty:
        raise ValueError(f"Loaded dataframe from {filepath} is empty.")
    
    logger.info(f"Loaded {len(df)} rows with {len(df.columns)} columns.")
    return df

def split_data(
    df: pd.DataFrame,
    target_col: str = "decomp_energy",
    train_ratio: float = 0.7,
    val_ratio: float = 0.15,
    test_ratio: float = 0.15,
    stratify_col: Optional[str] = None,
    random_state: Optional[int] = None
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Splits the dataframe into Train, Validation, and Held-Out (Test) sets.
    
    The split is performed in two stages:
    1. Split Train vs (Val + Test)
    2. Split (Val + Test) into Val and Test
    
    Args:
        df: The input dataframe.
        target_col: The name of the target column to use for stratification if specified.
        train_ratio: Fraction of data for training.
        val_ratio: Fraction of data for validation.
        test_ratio: Fraction of data for held-out testing.
        stratify_col: Column name to stratify on (e.g., 'potential' or a binned target).
        random_state: Random seed for reproducibility.
        
    Returns:
        Tuple of (train_df, val_df, test_df).
    """
    if random_state is None:
        random_state = get_seed()
    
    # Validate ratios sum to 1.0 (with floating point tolerance)
    total_ratio = train_ratio + val_ratio + test_ratio
    if abs(total_ratio - 1.0) > 1e-6:
        raise ValueError(f"Ratios must sum to 1.0. Got {total_ratio}")
    
    # Calculate intermediate ratio for the second split
    # We need val / (val + test)
    remaining_ratio = val_ratio + test_ratio
    if remaining_ratio == 0:
        val_split_ratio = 0.0
    else:
        val_split_ratio = val_ratio / remaining_ratio
    
    # First split: Train vs (Val + Test)
    if stratify_col and stratify_col in df.columns:
        train_df, temp_df = train_test_split(
            df, 
            train_size=train_ratio, 
            random_state=random_state, 
            stratify=df[stratify_col]
        )
    else:
        train_df, temp_df = train_test_split(
            df, 
            train_size=train_ratio, 
            random_state=random_state
        )
    
    # Second split: (Val + Test) -> Val vs Test
    if stratify_col and stratify_col in temp_df.columns:
        # Ensure stratify column exists in temp_df
        val_df, test_df = train_test_split(
            temp_df, 
            train_size=val_split_ratio, 
            random_state=random_state, 
            stratify=temp_df[stratify_col]
        )
    else:
        val_df, test_df = train_test_split(
            temp_df, 
            train_size=val_split_ratio, 
            random_state=random_state
        )
    
    logger.info(f"Split complete: Train={len(train_df)}, Val={len(val_df)}, Test={len(test_df)}")
    return train_df, val_df, test_df

def save_splits(
    train_df: pd.DataFrame,
    val_df: pd.DataFrame,
    test_df: pd.DataFrame,
    output_dir: Optional[str] = None
) -> None:
    """
    Saves the split dataframes to CSV files in the processed directory.
    
    Args:
        train_df: Training dataframe.
        val_df: Validation dataframe.
        test_df: Held-out/Test dataframe.
        output_dir: Optional explicit output directory.
    """
    if output_dir is None:
        output_dir = get_processed_dir()
    
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Define file paths
    train_path = output_path / "electrolyte_train.csv"
    val_path = output_path / "electrolyte_val.csv"
    heldout_path = output_path / "electrolyte_heldout.csv"
    
    # Save files
    logger.info(f"Saving train set to {train_path}")
    train_df.to_csv(train_path, index=False)
    
    logger.info(f"Saving validation set to {val_path}")
    val_df.to_csv(val_path, index=False)
    
    logger.info(f"Saving held-out set to {heldout_path}")
    test_df.to_csv(heldout_path, index=False)
    
    # Generate checksums for reproducibility
    checksums = {
        "train": compute_sha256(str(train_path)),
        "val": compute_sha256(str(val_path)),
        "heldout": compute_sha256(str(heldout_path))
    }
    checksum_file = output_path / "split_checksums.json"
    save_checksums(checksums, str(checksum_file))
    logger.info(f"Saved checksums to {checksum_file}")

def run_split_pipeline(
    input_file: Optional[str] = None,
    output_dir: Optional[str] = None,
    target_col: str = "decomp_energy",
    stratify_col: str = "potential"
) -> None:
    """
    Orchestrates the full splitting pipeline:
    1. Load processed features.
    2. Split into Train, Validation, Held-Out.
    3. Save results to disk.
    
    Args:
        input_file: Path to the input processed features CSV.
        output_dir: Directory to save output files.
        target_col: Target column name.
        stratify_col: Column to stratify on (default: 'potential' to ensure voltage balance).
    """
    logger.info("Starting data split pipeline...")
    
    # Load data
    df = load_processed_features(input_file)
    
    # Perform split
    train_df, val_df, test_df = split_data(
        df,
        target_col=target_col,
        stratify_col=stratify_col,
        random_state=get_seed()
    )
    
    # Save splits
    save_splits(train_df, val_df, test_df, output_dir)
    
    logger.info("Data split pipeline completed successfully.")

if __name__ == "__main__":
    # Configure logging for script execution
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Get paths from config
    processed_dir = get_processed_dir()
    input_file = os.path.join(processed_dir, "electrolyte_features.csv")
    
    if not os.path.exists(input_file):
        logger.error(f"Input file {input_file} does not exist. Please run the ingestion/descriptor pipeline first.")
        sys.exit(1)
    
    run_split_pipeline(input_file=input_file, output_dir=processed_dir)
