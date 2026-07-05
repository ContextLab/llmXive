import os
import sys
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any, Tuple

import pandas as pd
from sklearn.model_selection import train_test_split

# Ensure project root is in path for imports if running as script
_project_root = Path(__file__).resolve().parent.parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from utils.logging_config import get_logger, log_exclusion_reason, log_pipeline_event

logger = get_logger(__name__)

# Constants
DATA_DIR = _project_root / "data"
PROCESSED_DIR = DATA_DIR / "processed"
RAW_FILE = PROCESSED_DIR / "features.csv"
TRAIN_FILE = PROCESSED_DIR / "train_set.csv"
TEST_FILE = PROCESSED_DIR / "test_set.csv"

def load_raw_data(filepath: Optional[Path] = None) -> pd.DataFrame:
    """Load the raw features CSV."""
    path = filepath or RAW_FILE
    if not path.exists():
        raise FileNotFoundError(f"Raw data file not found: {path}")
    logger.info(f"Loading raw data from {path}")
    df = pd.read_csv(path)
    logger.info(f"Loaded {len(df)} rows with columns: {list(df.columns)}")
    return df

def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean data: handle missing values, remove duplicates, ensure types.
    For this specific task, we assume the data is already cleaned by T018/T019
    (zero nulls in target), but we perform a final check and drop rows with
    any NaNs in the feature columns or target.
    """
    logger.info("Cleaning data...")
    initial_count = len(df)
    
    # Drop rows with any NaNs in the target column (decomposition_energy)
    target_col = "decomposition_energy"
    if target_col in df.columns:
        nulls_before = df[target_col].isnull().sum()
        if nulls_before > 0:
            log_exclusion_reason(f"Removing {nulls_before} rows with null target values")
        df = df.dropna(subset=[target_col])
    
    # Drop rows with any NaNs in feature columns
    df = df.dropna()
    
    # Drop duplicates
    df = df.drop_duplicates()
    
    final_count = len(df)
    logger.info(f"Cleaned data: {initial_count} -> {final_count} rows")
    return df

def validate_schema(df: pd.DataFrame) -> bool:
    """
    Validate that the dataframe has the expected columns.
    Expected: formula, space_group, tolerance_factor, octahedral_factor,
              ionic_radius_mismatch, electronegativity_diff, decomposition_energy
    """
    required_cols = [
        "formula", "space_group", "tolerance_factor", "octahedral_factor",
        "ionic_radius_mismatch", "electronegativity_diff", "decomposition_energy"
    ]
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        logger.error(f"Missing required columns: {missing}")
        return False
    return True

def split_data(df: pd.DataFrame, test_size: float = 0.2, random_state: int = 42) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Perform an 80/20 stratified split into train_set and test_set.
    
    Stratification is performed on the target variable (decomposition_energy)
    by binning it to ensure classes exist for stratify=y, as required by the
    nested CV description in the plan.
    
    Args:
        df: Input dataframe with features and target.
        test_size: Proportion of data to include in the test split (default 0.2).
        random_state: Random seed for reproducibility.
        
    Returns:
        Tuple of (train_set, test_set) dataframes.
    """
    logger.info(f"Splitting data into train/test sets (test_size={test_size})")
    
    if "decomposition_energy" not in df.columns:
        raise ValueError("Column 'decomposition_energy' not found for stratification.")
    
    y = df["decomposition_energy"]
    X = df.drop(columns=["decomposition_energy"])
    
    # For stratification on a continuous target, we bin the target values
    # to create discrete classes. Using 5 bins is a common heuristic.
    y_binned = pd.qcut(y, q=5, duplicates="drop")
    
    # Ensure we have at least 2 classes for stratification
    if y_binned.nunique() < 2:
        logger.warning("Not enough unique binned classes for stratification. Falling back to random split.")
        train_set, test_set = train_test_split(
            df, 
            test_size=test_size, 
            random_state=random_state
        )
    else:
        train_set, test_set = train_test_split(
            df, 
            test_size=test_size, 
            random_state=random_state, 
            stratify=y_binned
        )
    
    logger.info(f"Train set size: {len(train_set)}, Test set size: {len(test_set)}")
    logger.info(f"Train set target stats: mean={train_set['decomposition_energy'].mean():.4f}, std={train_set['decomposition_energy'].std():.4f}")
    logger.info(f"Test set target stats: mean={test_set['decomposition_energy'].mean():.4f}, std={test_set['decomposition_energy'].std():.4f}")
    
    return train_set, test_set

def save_processed_data(df: pd.DataFrame, filepath: Path) -> None:
    """Save a dataframe to CSV."""
    filepath.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(filepath, index=False)
    logger.info(f"Saved processed data to {filepath}")

def main():
    """Main entry point for the preprocessing script."""
    logger.info("Starting preprocessing pipeline...")
    
    # 1. Load raw data
    try:
        df = load_raw_data()
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)
    
    # 2. Validate schema
    if not validate_schema(df):
        logger.error("Schema validation failed.")
        sys.exit(1)
    
    # 3. Clean data
    df_clean = clean_data(df)
    
    # 4. Split data (T022 Implementation)
    train_set, test_set = split_data(df_clean)
    
    # 5. Save splits
    save_processed_data(train_set, TRAIN_FILE)
    save_processed_data(test_set, TEST_FILE)
    
    logger.info("Preprocessing pipeline completed successfully.")
    log_pipeline_event("Preprocessing", "Completed", {"train_size": len(train_set), "test_size": len(test_set)})

if __name__ == "__main__":
    main()