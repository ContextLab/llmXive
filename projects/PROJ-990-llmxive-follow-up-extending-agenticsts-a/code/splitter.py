import os
import json
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

# Configure logging to file and console
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data/processed/splitter.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Constants from config (hardcoded defaults if config not loaded, per T004)
# These match the constants defined in T004
MIN_CONTEXT = 256
K_RANDOM_BASELINE = 2

def load_processed_data(input_path: str) -> pd.DataFrame:
    """
    Load the processed metrics CSV.
    
    Args:
        input_path: Path to data/processed/metrics_with_moves.csv
        
    Returns:
        DataFrame with trajectory metrics.
        
    Raises:
        FileNotFoundError: If input file does not exist.
        ValueError: If input file is empty or has no data rows.
    """
    path = Path(input_path)
    if not path.exists():
        logger.error(f"Input file not found: {input_path}")
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    try:
        df = pd.read_csv(path)
    except Exception as e:
        logger.error(f"Failed to read CSV: {e}")
        raise e
    
    if df.empty:
        logger.error("Input CSV is empty (header only). Cannot split.")
        raise ValueError("Input CSV is empty (header only). Cannot split.")
    
    logger.info(f"Loaded {len(df)} rows from {input_path}")
    return df

def stratified_split(df: pd.DataFrame, test_size: float = 0.2, val_size: float = 0.1, random_state: int = 42) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Split the dataframe into train, validation, and test sets.
    Uses trajectory_id for stratification to ensure unique trajectories per split.
    
    Args:
        df: Input DataFrame.
        test_size: Fraction for test set.
        val_size: Fraction for validation set.
        random_state: Random seed for reproducibility.
        
    Returns:
        Tuple of (train_df, val_df, test_df)
    """
    if 'trajectory_id' not in df.columns:
        # If no trajectory_id, just split rows
        logger.warning("No 'trajectory_id' column found. Performing random row split.")
        train_df, temp_df = train_test_split(df, test_size=test_size+val_size, random_state=random_state)
        val_df, test_df = train_test_split(temp_df, test_size=test_size/(test_size+val_size), random_state=random_state)
    else:
        # Group by trajectory_id to ensure all turns of a trajectory stay together
        trajectory_ids = df['trajectory_id'].unique()
        np.random.seed(random_state)
        np.random.shuffle(trajectory_ids)
        
        n_total = len(trajectory_ids)
        n_test = int(n_total * test_size)
        n_val = int(n_total * val_size)
        
        test_ids = trajectory_ids[:n_test]
        val_ids = trajectory_ids[n_test:n_test+n_val]
        train_ids = trajectory_ids[n_test+n_val:]
        
        test_df = df[df['trajectory_id'].isin(test_ids)]
        val_df = df[df['trajectory_id'].isin(val_ids)]
        train_df = df[df['trajectory_id'].isin(train_ids)]
        
        logger.info(f"Split trajectory_ids: Train={len(train_ids)}, Val={len(val_ids)}, Test={len(test_ids)}")
    
    return train_df, val_df, test_df

def validate_split(train_df: pd.DataFrame, val_df: pd.DataFrame, test_df: pd.DataFrame) -> bool:
    """
    Validate that splits are disjoint and cover the data.
    
    Returns:
        True if valid, False otherwise.
    """
    train_ids = set(train_df['trajectory_id'].unique()) if 'trajectory_id' in train_df.columns else set(train_df.index)
    val_ids = set(val_df['trajectory_id'].unique()) if 'trajectory_id' in val_df.columns else set(val_df.index)
    test_ids = set(test_df['trajectory_id'].unique()) if 'trajectory_id' in test_df.columns else set(test_df.index)
    
    if train_ids & val_ids:
        logger.error("Intersection found between train and validation sets.")
        return False
    if train_ids & test_ids:
        logger.error("Intersection found between train and test sets.")
        return False
    if val_ids & test_ids:
        logger.error("Intersection found between validation and test sets.")
        return False
        
    logger.info("Split validation passed: sets are disjoint.")
    return True

def save_split_data(train_df: pd.DataFrame, val_df: pd.DataFrame, test_df: pd.DataFrame, output_dir: str):
    """
    Save the split dataframes to CSV files.
    
    Args:
        train_df: Training set.
        val_df: Validation set.
        test_df: Test set.
        output_dir: Directory to save files.
    """
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    
    train_df.to_csv(out_path / 'train_set.csv', index=False)
    val_df.to_csv(out_path / 'validation_set.csv', index=False)
    test_df.to_csv(out_path / 'test_set.csv', index=False)
    
    # Create ablation_train_set as a copy of train_set for this phase
    # (Ablation labels are added later in T008, but the file structure is needed now)
    train_df.to_csv(out_path / 'ablation_train_set.csv', index=False)
    
    logger.info(f"Saved split data to {output_dir}")

def log_sample_size_warning(train_size: int, log_path: str):
    """
    Log a warning if the training set size is below the statistical power threshold.
    Also writes a flag to trigger the fixed-k heuristic if needed.
    
    Args:
        train_size: Number of rows in the training set.
        log_path: Path to the edge_case_warnings.log file.
    """
    warnings_path = Path(log_path)
    warnings_path.parent.mkdir(parents=True, exist_ok=True)
    
    if train_size < 300:
        warning_msg = f"Statistical power marginal (n < 300): Training set size is {train_size}."
        logger.warning(warning_msg)
        
        with open(warnings_path, 'a') as f:
            f.write(f"{warning_msg}\n")
        
        # Write fallback flag as per T008d logic
        fallback_path = Path('data/processed/fallback_flag.json')
        fallback_data = {
            "fallback": True,
            "use_heuristic": True,
            "reason": f"Training set size {train_size} < 300",
            "k_value": K_RANDOM_BASELINE
        }
        with open(fallback_path, 'w') as f:
            json.dump(fallback_data, f, indent=2)
        
        logger.info(f"Wrote fallback flag to {fallback_path}")
    else:
        logger.info(f"Training set size {train_size} >= 300. No fallback needed.")

def main():
    """
    Main entry point for the data splitting task T014a.
    """
    input_file = 'data/processed/metrics_with_moves.csv'
    output_dir = 'data/processed'
    warnings_log = 'data/processed/edge_case_warnings.log'
    
    try:
        # Load data
        df = load_processed_data(input_file)
        
        # Split data
        train_df, val_df, test_df = stratified_split(df)
        
        # Validate
        if not validate_split(train_df, val_df, test_df):
            raise ValueError("Split validation failed.")
        
        # Save
        save_split_data(train_df, val_df, test_df, output_dir)
        
        # Check sample size and log warnings
        log_sample_size_warning(len(train_df), warnings_log)
        
        logger.info("Task T014a completed successfully.")
        
    except FileNotFoundError as e:
        logger.error(f"Pipeline blocked: {e}")
        raise e
    except ValueError as e:
        logger.error(f"Data processing error: {e}")
        raise e
    except Exception as e:
        logger.error(f"Unexpected error in splitter: {e}")
        raise e

if __name__ == '__main__':
    main()