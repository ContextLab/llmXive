import os
import json
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Import config for paths if available, otherwise use defaults
try:
    from config import load_config_from_file
    CONFIG = load_config_from_file()
    DATA_PROCESSED_DIR = Path(CONFIG.get('paths', {}).get('processed', 'data/processed'))
except (ImportError, FileNotFoundError, KeyError):
    DATA_PROCESSED_DIR = Path('data/processed')

# Constants for splitting
TRAIN_RATIO = 0.8
HOLDOUT_RATIO = 0.2
RANDOM_STATE = 42  # Fixed seed for reproducibility

def load_processed_data(input_file: Optional[str] = None) -> pd.DataFrame:
    """
    Loads the processed utility labels or trajectory data for splitting.
    Defaults to 'utility_labels.csv' if no specific input is provided,
    as that is the primary labeled dataset available after T008b.
    """
    if input_file is None:
        # Check for the most likely source of labeled data
        candidates = [
            DATA_PROCESSED_DIR / 'utility_labels.csv',
            DATA_PROCESSED_DIR / 'trajectories.csv'
        ]
        for candidate in candidates:
            if candidate.exists():
                input_file = str(candidate)
                break
    
    if input_file is None:
        raise FileNotFoundError(
            "No input data file found. Expected 'data/processed/utility_labels.csv' "
            "or 'data/processed/trajectories.csv'. Ensure T008b and T007 are completed."
        )
    
    path = Path(input_file)
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {path}")
    
    logger.info(f"Loading data from {path}")
    df = pd.read_csv(path)
    
    if df.empty:
        raise ValueError(f"Input file {path} is empty.")
    
    logger.info(f"Loaded {len(df)} rows with columns: {list(df.columns)}")
    return df

def stratified_split(df: pd.DataFrame, train_ratio: float = TRAIN_RATIO, random_state: int = RANDOM_STATE) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Performs a stratified split of the dataframe into training and hold-out sets.
    
    Stratification is performed on the 'utility_score' column if it exists.
    If 'utility_score' is not available, it attempts to stratify on 'layer_id'.
    If neither exists, it falls back to a random split (with a warning).
    
    Args:
        df: The input DataFrame.
        train_ratio: Proportion of data to include in the training set.
        random_state: Seed for reproducibility.
        
    Returns:
        Tuple of (train_df, holdout_df)
    """
    if df.empty:
        raise ValueError("Cannot split an empty DataFrame.")
    
    np.random.seed(random_state)
    
    stratify_col = None
    if 'utility_score' in df.columns:
        stratify_col = 'utility_score'
        logger.info(f"Stratifying by 'utility_score' column.")
    elif 'layer_id' in df.columns:
        stratify_col = 'layer_id'
        logger.info(f"Stratifying by 'layer_id' column.")
    else:
        logger.warning("No suitable column found for stratification ('utility_score' or 'layer_id'). "
                     "Performing a random split. This may lead to distribution shifts.")
        
    if stratify_col:
        # Ensure the column is numeric or categorical for stratification
        # If it's continuous (float), we might need to bin it, but pandas handles float stratification in newer versions.
        # For safety, we let pandas handle it, but if it fails due to too many unique values, we fall back.
        try:
            train_df, holdout_df = train_test_split(
                df, 
                train_size=train_ratio, 
                stratify=df[stratify_col], 
                random_state=random_state
            )
        except Exception as e:
            logger.warning(f"Stratification failed ({e}). Falling back to random split.")
            train_df, holdout_df = train_test_split(
                df, 
                train_size=train_ratio, 
                random_state=random_state
            )
    else:
        train_df, holdout_df = train_test_split(
            df, 
            train_size=train_ratio, 
            random_state=random_state
        )
        
    logger.info(f"Split complete: Train set size = {len(train_df)}, Holdout set size = {len(holdout_df)}")
    return train_df, holdout_df

def train_test_split(df: pd.DataFrame, train_size: float, stratify: Optional[pd.Series] = None, random_state: int = 42) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Wrapper around sklearn's train_test_split or a manual implementation if sklearn is unavailable.
    Given the project constraints, we use a manual numpy-based approach to ensure no extra dependencies.
    """
    try:
        from sklearn.model_selection import train_test_split as sk_split
        return sk_split(df, train_size=train_size, stratify=stratify, random_state=random_state)
    except ImportError:
        logger.warning("sklearn not found. Using manual stratified split implementation.")
        indices = df.index.tolist()
        
        if stratify is not None:
            # Group indices by stratification column values
            stratify_values = stratify.values
            unique_vals = np.unique(stratify_values)
            strata_indices = {val: [] for val in unique_vals}
            
            for idx, val in zip(indices, stratify_values):
                strata_indices[val].append(idx)
            
            train_indices = []
            holdout_indices = []
            
            for val, idxs in strata_indices.items():
                n_total = len(idxs)
                n_train = int(np.ceil(n_total * train_size))
                np.random.shuffle(idxs)
                train_indices.extend(idxs[:n_train])
                holdout_indices.extend(idxs[n_train:])
                
            np.random.shuffle(train_indices)
            np.random.shuffle(holdout_indices)
            
            return df.loc[train_indices].reset_index(drop=True), df.loc[holdout_indices].reset_index(drop=True)
        else:
            # Random split
            np.random.shuffle(indices)
            n_train = int(len(indices) * train_size)
            train_indices = indices[:n_train]
            holdout_indices = indices[n_train:]
            return df.loc[train_indices].reset_index(drop=True), df.loc[holdout_indices].reset_index(drop=True)

def save_split_data(train_df: pd.DataFrame, holdout_df: pd.DataFrame, output_dir: Optional[Path] = None) -> Tuple[Path, Path]:
    """
    Saves the split dataframes to CSV files.
    
    Args:
        train_df: Training set DataFrame.
        holdout_df: Holdout set DataFrame.
        output_dir: Directory to save files. Defaults to DATA_PROCESSED_DIR.
        
    Returns:
        Tuple of (train_path, holdout_path)
    """
    if output_dir is None:
        output_dir = DATA_PROCESSED_DIR
        
    output_dir.mkdir(parents=True, exist_ok=True)
    
    train_path = output_dir / 'train_set.csv'
    holdout_path = output_dir / 'holdout_set.csv'
    
    train_df.to_csv(train_path, index=False)
    holdout_df.to_csv(holdout_path, index=False)
    
    logger.info(f"Saved training set to {train_path} ({len(train_df)} rows)")
    logger.info(f"Saved holdout set to {holdout_path} ({len(holdout_df)} rows)")
    
    return train_path, holdout_path

def validate_split(train_df: pd.DataFrame, holdout_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Validates the split for data leakage and distribution balance.
    
    Returns a report dictionary with validation status and statistics.
    """
    report = {
        "status": "passed",
        "train_size": len(train_df),
        "holdout_size": len(holdout_df),
        "total_size": len(train_df) + len(holdout_df),
        "train_ratio": len(train_df) / (len(train_df) + len(holdout_df)),
        "issues": []
    }
    
    # Check for index overlap (should not happen with reset_index, but good to verify)
    if set(train_df.index) & set(holdout_df.index):
        report["status"] = "failed"
        report["issues"].append("Index overlap detected between train and holdout sets.")
        
    # Check for column consistency
    if set(train_df.columns) != set(holdout_df.columns):
        report["status"] = "failed"
        report["issues"].append("Column mismatch between train and holdout sets.")
        
    # Check for empty sets
    if len(train_df) == 0:
        report["status"] = "failed"
        report["issues"].append("Training set is empty.")
    if len(holdout_df) == 0:
        report["status"] = "failed"
        report["issues"].append("Holdout set is empty.")
        
    # Check distribution of key columns if available
    for col in ['utility_score', 'layer_id']:
        if col in train_df.columns and col in holdout_df.columns:
            # Simple check for presence of unique values
            train_unique = train_df[col].nunique()
            holdout_unique = holdout_df[col].nunique()
            if train_unique == 0 or holdout_unique == 0:
                report["issues"].append(f"Column '{col}' has no unique values in one of the sets.")
                
    return report

def main():
    """
    Main entry point for the splitter task.
    Loads processed data, performs stratified split, and saves the results.
    """
    logger.info("Starting data split process (T014a)...")
    
    try:
        # 1. Load Data
        df = load_processed_data()
        
        # 2. Split Data
        train_df, holdout_df = stratified_split(df)
        
        # 3. Validate Split
        validation_report = validate_split(train_df, holdout_df)
        if validation_report["status"] == "failed":
            logger.error(f"Split validation failed: {validation_report['issues']}")
            raise RuntimeError("Data split validation failed.")
            
        # 4. Save Data
        train_path, holdout_path = save_split_data(train_df, holdout_df)
        
        # 5. Log Summary
        logger.info("Split process completed successfully.")
        logger.info(f"Train set: {train_path} ({len(train_df)} rows)")
        logger.info(f"Holdout set: {holdout_path} ({len(holdout_df)} rows)")
        
        # Save validation report as JSON for audit
        report_path = DATA_PROCESSED_DIR / 'split_validation_report.json'
        with open(report_path, 'w') as f:
            json.dump(validation_report, f, indent=2)
        logger.info(f"Saved validation report to {report_path}")
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        raise
    except ValueError as e:
        logger.error(f"Value error: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during split: {e}")
        raise

if __name__ == "__main__":
    main()
