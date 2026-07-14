import os
import sys
import logging
from pathlib import Path
import numpy as np
import pandas as pd
from typing import Tuple, List, Optional
from sklearn.model_selection import train_test_split

# Add project root to path to allow relative imports if run as script
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from ingestion.preprocess import (
    load_raw_for_sensitivity, 
    load_correlation_flags, 
    impute_composition_by_family, 
    impute_grain_size_knn, 
    encode_elemental_fractions
)
# Import config for RANDOM_SEED if available, otherwise define locally
try:
    from config import RANDOM_SEED
except ImportError:
    RANDOM_SEED = 42

logger = logging.getLogger(__name__)

def load_encoded_features() -> pd.DataFrame:
    """
    Loads the dataset after encoding (T016 output).
    Expected path: data/processed/encoded_features.csv
    """
    data_dir = project_root / "data" / "processed"
    file_path = data_dir / "encoded_features.csv"
    
    if not file_path.exists():
        raise FileNotFoundError(
            f"Required input file not found: {file_path}. "
            "Please ensure T016 (encode_elemental_fractions) has completed successfully."
        )
    
    df = pd.read_csv(file_path)
    logger.info(f"Loaded encoded features from {file_path} with shape {df.shape}")
    return df

def stratified_split(
    df: pd.DataFrame, 
    seed: int = RANDOM_SEED, 
    test_size: float = 0.2,
    min_stratum_count: int = 20
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Implements stratified split by Alloy Family.
    
    Logic:
    1. Group by 'alloy_family'.
    2. Filter out any strata with N < min_stratum_count (log a warning).
    3. Perform train_test_split with stratify on 'alloy_family'.
    
    Args:
        df: The input DataFrame (must contain 'alloy_family' column).
        seed: Random seed for reproducibility.
        test_size: Proportion of data for test set.
        min_stratum_count: Minimum records required per family to be included.
        
    Returns:
        Tuple of (train_df, test_df)
    """
    if 'alloy_family' not in df.columns:
        raise ValueError("Input DataFrame must contain 'alloy_family' column for stratification.")

    # Check stratum sizes
    family_counts = df['alloy_family'].value_counts()
    valid_families = family_counts[family_counts >= min_stratum_count].index
    invalid_families = family_counts[family_counts < min_stratum_count].index

    if len(invalid_families) > 0:
        logger.warning(
            f"Skipping {len(invalid_families)} alloy families with < {min_stratum_count} samples: "
            f"{list(invalid_families)}. These will be excluded from the split."
        )
        df_filtered = df[df['alloy_family'].isin(valid_families)]
    else:
        df_filtered = df

    if df_filtered.empty:
        raise ValueError(
            f"No data remaining after filtering for min_stratum_count={min_stratum_count}. "
            "Cannot perform stratified split."
        )

    logger.info(f"Performing stratified split on {len(df_filtered)} records across {len(valid_families)} families.")

    train_df, test_df = train_test_split(
        df_filtered,
        test_size=test_size,
        random_state=seed,
        stratify=df_filtered['alloy_family']
    )

    logger.info(f"Split complete. Train: {len(train_df)}, Test: {len(test_df)}")
    return train_df, test_df

def save_splits(train_df: pd.DataFrame, test_df: pd.DataFrame) -> None:
    """
    Saves the train and test splits to the data/processed directory.
    """
    data_dir = project_root / "data" / "processed"
    data_dir.mkdir(parents=True, exist_ok=True)

    train_path = data_dir / "train.csv"
    test_path = data_dir / "test.csv"

    train_df.to_csv(train_path, index=False)
    test_df.to_csv(test_path, index=False)

    logger.info(f"Saved train set to {train_path}")
    logger.info(f"Saved test set to {test_path}")

def main() -> None:
    """
    Main entry point for T017: Stratified Split.
    Executes the split logic and writes outputs.
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    try:
        # 1. Load the encoded features (output of T016)
        df = load_encoded_features()

        # 2. Perform stratified split
        train_df, test_df = stratified_split(df, seed=RANDOM_SEED, min_stratum_count=20)

        # 3. Save outputs
        save_splits(train_df, test_df)

        logger.info("T017 (Stratified Split) completed successfully.")

    except FileNotFoundError as e:
        logger.error(f"Missing required input data: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Data validation error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during T017 execution: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()