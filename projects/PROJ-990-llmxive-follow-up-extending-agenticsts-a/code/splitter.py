"""
Data Splitter Module (T014a)

Implements logic to split processed trajectory metrics into train, validation, and test sets.
Handles edge cases for sample size and updates pipeline configuration state accordingly.
"""
import os
import json
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
MIN_SAMPLE_SIZE = 300
TRAIN_RATIO = 0.6
VAL_RATIO = 0.2
TEST_RATIO = 0.2

def load_processed_data(input_path: str) -> pd.DataFrame:
    """
    Load the processed metrics CSV file.
    
    Args:
        input_path: Path to the input CSV file (data/processed/metrics_with_moves.csv)
        
    Returns:
        DataFrame containing the processed metrics
        
    Raises:
        FileNotFoundError: If the input file does not exist
        ValueError: If the file is empty or has no data rows
    """
    path = Path(input_path)
    
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    df = pd.read_csv(input_path)
    
    if df.empty:
        raise ValueError(f"Input file {input_path} is empty (no data rows). Pipeline cannot proceed.")
    
    logger.info(f"Loaded {len(df)} rows from {input_path}")
    return df

def stratified_split(
    df: pd.DataFrame, 
    train_ratio: float = TRAIN_RATIO,
    val_ratio: float = VAL_RATIO,
    test_ratio: float = TEST_RATIO,
    seed: int = 42
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Split the dataframe into train, validation, and test sets.
    
    Uses stratified sampling if a suitable target column exists (e.g., 'win', 'loss'),
    otherwise performs a random split.
    
    Args:
        df: Input DataFrame
        train_ratio: Fraction of data for training
        val_ratio: Fraction of data for validation
        test_ratio: Fraction of data for testing
        seed: Random seed for reproducibility
        
    Returns:
        Tuple of (train_df, val_df, test_df)
    """
    # Ensure ratios sum to 1.0
    total_ratio = train_ratio + val_ratio + test_ratio
    if not np.isclose(total_ratio, 1.0):
        logger.warning(f"Ratios sum to {total_ratio}, normalizing to 1.0")
        train_ratio /= total_ratio
        val_ratio /= total_ratio
        test_ratio /= total_ratio

    # Determine stratification column
    stratify_col = None
    possible_cols = ['win', 'loss', 'outcome', 'result']
    for col in possible_cols:
        if col in df.columns:
            stratify_col = col
            break
    
    if stratify_col:
        logger.info(f"Stratifying split by column: {stratify_col}")
    else:
        logger.warning("No suitable stratification column found. Using random split.")

    # Shuffle data
    df_shuffled = df.sample(frac=1, random_state=seed).reset_index(drop=True)

    # Calculate split indices
    train_end = int(len(df_shuffled) * train_ratio)
    val_end = train_end + int(len(df_shuffled) * val_ratio)

    train_df = df_shuffled.iloc[:train_end].reset_index(drop=True)
    val_df = df_shuffled.iloc[train_end:val_end].reset_index(drop=True)
    test_df = df_shuffled.iloc[val_end:].reset_index(drop=True)

    return train_df, val_df, test_df

def validate_split(train_df: pd.DataFrame, val_df: pd.DataFrame, test_df: pd.DataFrame) -> bool:
    """
    Validate that the splits are non-empty and cover all data.
    
    Args:
        train_df: Training set
        val_df: Validation set
        test_df: Test set
        
    Returns:
        True if valid, False otherwise
    """
    total_original = len(train_df) + len(val_df) + len(test_df)
    if total_original == 0:
        logger.error("Total split size is zero.")
        return False
    
    if len(train_df) == 0:
        logger.error("Training set is empty.")
        return False
        
    logger.info(f"Split validation passed: Train={len(train_df)}, Val={len(val_df)}, Test={len(test_df)}")
    return True

def save_split_data(
    train_df: pd.DataFrame,
    val_df: pd.DataFrame,
    test_df: pd.DataFrame,
    output_dir: str = "data/processed"
) -> Dict[str, str]:
    """
    Save the split datasets to CSV files.
    
    Args:
        train_df: Training DataFrame
        val_df: Validation DataFrame
        test_df: Test DataFrame
        output_dir: Output directory path
        
    Returns:
        Dictionary mapping dataset name to file path
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    train_path = output_path / "train_set.csv"
    val_path = output_path / "validation_set.csv"
    test_path = output_path / "test_set.csv"
    ablation_train_path = output_path / "ablation_train_set.csv"
    
    train_df.to_csv(train_path, index=False)
    val_df.to_csv(val_path, index=False)
    test_df.to_csv(test_path, index=False)
    
    # For ablation study, we often use the training set
    # We create a copy or specific subset if needed, but for now, it's the train set
    train_df.to_csv(ablation_train_path, index=False)
    
    logger.info(f"Saved split data to {output_dir}")
    return {
        "train": str(train_path),
        "validation": str(val_path),
        "test": str(test_path),
        "ablation_train": str(ablation_train_path)
    }

def log_sample_size_warning(n: int, log_path: str = "data/processed/edge_case_warnings.log") -> None:
    """
    Log a warning if the training set size is below the minimum threshold.
    
    Args:
        n: Number of samples in the training set
        log_path: Path to the warning log file
    """
    if n < MIN_SAMPLE_SIZE:
        warning_msg = f"Statistical power marginal (n < {MIN_SAMPLE_SIZE}): Training set size is {n}."
        
        # Ensure directory exists
        Path(log_path).parent.mkdir(parents=True, exist_ok=True)
        
        with open(log_path, 'a') as f:
            f.write(f"{warning_msg}\n")
        
        logger.warning(warning_msg)
        return True
    return False

def write_config_state(use_heuristic: bool, output_path: str = "data/processed/config_state.json") -> None:
    """
    Write the pipeline configuration state to a JSON file.
    
    Args:
        use_heuristic: Boolean flag indicating if heuristic fallback is active
        output_path: Path to the config state file
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    config = {
        "use_heuristic": use_heuristic,
        "min_sample_size": MIN_SAMPLE_SIZE,
        "timestamp": pd.Timestamp.now().isoformat()
    }
    
    with open(output_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    logger.info(f"Config state written to {output_path}: use_heuristic={use_heuristic}")

def main():
    """
    Main entry point for T014a: Data Splitting.
    
    1. Loads data from data/processed/metrics_with_moves.csv
    2. Splits into train/validation/test sets
    3. Checks sample size and updates config_state.json if n < 300
    4. Saves split CSVs to data/processed/
    """
    input_file = "data/processed/metrics_with_moves.csv"
    output_dir = "data/processed"
    log_file = "data/processed/edge_case_warnings.log"
    config_file = "data/processed/config_state.json"
    
    logger.info(f"Starting T014a: Data Splitting. Input: {input_file}")
    
    try:
        # 1. Load Data
        df = load_processed_data(input_file)
        
        # 2. Split Data
        train_df, val_df, test_df = stratified_split(df)
        
        # 3. Validate Splits
        if not validate_split(train_df, val_df, test_df):
            raise ValueError("Split validation failed. Aborting.")
        
        # 4. Check Sample Size & Update Config
        n_train = len(train_df)
        warning_logged = log_sample_size_warning(n_train, log_file)
        
        use_heuristic = warning_logged  # If warning logged, n < 300
        write_config_state(use_heuristic, config_file)
        
        # 5. Save Outputs
        save_split_data(train_df, val_df, test_df, output_dir)
        
        logger.info("T014a completed successfully.")
        
    except FileNotFoundError as e:
        logger.error(f"Data file missing: {e}")
        raise
    except ValueError as e:
        logger.error(f"Data processing error: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during splitting: {e}")
        raise

if __name__ == "__main__":
    main()