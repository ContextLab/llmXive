import os
import sys
import json
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Config utilities
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import (
    get_raw_data_dir,
    get_processed_data_dir,
    get_random_seed,
    ensure_directories,
    get_logger,
)

# sklearn utilities
from sklearn.model_selection import StratifiedShuffleSplit
from sklearn.preprocessing import MinMaxScaler

# Set random seed for reproducibility
np.random.seed(get_random_seed())

def setup_logger(name: str, log_file: str, level=logging.INFO) -> logging.Logger:
    """
    Set up a logger that writes to both console and a file.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # File handler
    fh = logging.FileHandler(log_file, mode='w')
    fh.setLevel(level)

    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(level)

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)

    # Avoid duplicate handlers if called multiple times
    if not any(isinstance(h, logging.FileHandler) for h in logger.handlers):
        logger.addHandler(fh)
    if not any(isinstance(h, logging.StreamHandler) for h in logger.handlers):
        logger.addHandler(ch)

    return logger

def load_raw_csv(file_path: str) -> pd.DataFrame:
    """
    Load a CSV file into a pandas DataFrame.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Raw data file not found: {file_path}")
    return pd.read_csv(file_path)

def detect_missing_values(df: pd.DataFrame, required_cols: List[str]) -> Dict[str, int]:
    """
    Detect missing values in required columns.
    Returns a dictionary of column names to missing value counts.
    """
    missing_counts = {}
    for col in required_cols:
        if col in df.columns:
            missing_counts[col] = int(df[col].isna().sum())
        else:
            missing_counts[col] = 0
    return missing_counts

def compute_medians(df: pd.DataFrame, numeric_cols: List[str]) -> Dict[str, float]:
    """
    Compute median values for imputation.
    """
    medians = {}
    for col in numeric_cols:
        if col in df.columns:
            medians[col] = float(df[col].median())
    return medians

def impute_missing_values(
    df: pd.DataFrame, medians: Dict[str, float], logger: logging.Logger
) -> Tuple[pd.DataFrame, int]:
    """
    Impute missing numeric values using median.
    Returns the imputed DataFrame and total count of imputed entries.
    """
    total_imputed = 0
    for col, median in medians.items():
        if col in df.columns:
            mask = df[col].isna()
            count = mask.sum()
            if count > 0:
                df.loc[mask, col] = median
                total_imputed += int(count)
                logger.info(f"Imputed {count} missing values in column '{col}' with median {median:.4f}")
    if total_imputed == 0:
        logger.info("No missing values were imputed.")
    else:
        logger.info(f"Total imputed values: {total_imputed}")
    return df, total_imputed

def drop_zero_variance(df: pd.DataFrame, logger: logging.Logger) -> List[str]:
    """
    Drop columns (numeric or categorical) that have zero variance.
    Returns list of dropped column names.
    """
    zero_var_cols = [col for col in df.columns if df[col].nunique() <= 1]
    if zero_var_cols:
        logger.warning(f"Zero variance detected in columns {zero_var_cols}. Dropping them.")
        df.drop(columns=zero_var_cols, inplace=True)
    else:
        logger.info("No zero-variance columns found.")
    return zero_var_cols

def encode_alloy_type(df: pd.DataFrame, logger: logging.Logger) -> Tuple[pd.DataFrame, List[str]]:
    """
    One‑hot encode the 'alloy_type' column if present.
    Returns the transformed DataFrame and list of new column names.
    """
    if 'alloy_type' not in df.columns:
        logger.info("Column 'alloy_type' not found; skipping one‑hot encoding.")
        return df, []
    logger.info("One‑hot encoding 'alloy_type'...")
    dummies = pd.get_dummies(df['alloy_type'], prefix='alloy')
    df = pd.concat([df.drop(columns=['alloy_type']), dummies], axis=1)
    logger.info(f"Created one‑hot columns: {list(dummies.columns)}")
    return df, list(dummies.columns)

def check_sample_count(df: pd.DataFrame, min_samples: int = 50, logger: Optional[logging.Logger] = None) -> None:
    """
    Ensure the dataset contains at least `min_samples` rows.
    """
    n = len(df)
    if logger:
        logger.info(f"Dataset contains {n} samples.")
    if n < min_samples:
        raise ValueError(
            f"Insufficient data for GPR training; minimum {min_samples} samples required. Found {n}."
        )

def split_and_normalize(
    df: pd.DataFrame,
    logger: logging.Logger,
    test_size: float = 0.30,
    random_state: int = 42,
) -> Tuple[pd.DataFrame, pd.DataFrame, Dict[str, Dict[str, float]]]:
    """
    Perform a stratified split (based on 'alloy_type' if present) into train and test,
    then apply MinMax scaling to numeric feature columns (excluding targets).
    Returns train_df, test_df, and a dict of normalization bounds.
    """
    # Identify target columns (must exist in data)
    target_cols = [c for c in ['yield_strength', 'ductility'] if c in df.columns]
    if not target_cols:
        raise ValueError("No target columns ('yield_strength', 'ductility') found in the dataset.")

    # Determine stratification column
    stratify_col = df['alloy_type'] if 'alloy_type' in df.columns else None

    # Split
    splitter = StratifiedShuffleSplit(
        n_splits=1, test_size=test_size, random_state=random_state
    )
    for train_idx, test_idx in splitter.split(df, stratify_col):
        train_df = df.iloc[train_idx].reset_index(drop=True)
        test_df = df.iloc[test_idx].reset_index(drop=True)

    # Separate features and targets
    feature_cols = [c for c in train_df.columns if c not in target_cols]

    # Fit scaler on training features
    scaler = MinMaxScaler()
    scaler.fit(train_df[feature_cols])

    # Transform both splits
    train_df[feature_cols] = scaler.transform(train_df[feature_cols])
    test_df[feature_cols] = scaler.transform(test_df[feature_cols])

    # Record bounds (original min/max before scaling)
    bounds: Dict[str, Dict[str, float]] = {}
    for i, col in enumerate(feature_cols):
        bounds[col] = {
            "min": float(scaler.data_min_[i]),
            "max": float(scaler.data_max_[i]),
        }

    logger.info(f"Split data: train={len(train_df)} rows, test={len(test_df)} rows.")
    logger.info("Applied MinMax scaling to numeric features.")
    return train_df, test_df, bounds

def save_normalization_bounds(
    bounds: Dict[str, Dict[str, float]], output_path: Path, logger: logging.Logger
) -> None:
    """
    Write the normalization bounds to a JSON file.
    """
    with open(output_path, "w") as f:
        json.dump(bounds, f, indent=2)
    logger.info(f"Normalization bounds saved to {output_path}")

def validate_and_preprocess(
    raw_file_path: Optional[str] = None,
    log_file_path: Optional[str] = None,
) -> None:
    """
    Full preprocessing pipeline:
    1. Load raw CSV
    2. Verify required schema
    3. Drop zero‑variance columns
    4. Median‑impute missing values
    5. One‑hot encode alloy_type
    6. Stratified split (70/30) and MinMax scaling
    7. Save train/test CSVs and normalization bounds
    """
    # Resolve default paths
    raw_dir = get_raw_data_dir()
    processed_dir = get_processed_data_dir()
    if raw_file_path is None:
        # Pick the first CSV in the raw directory
        candidates = list(raw_dir.glob("*.csv"))
        if not candidates:
            raise FileNotFoundError(f"No CSV files found in raw data directory: {raw_dir}")
        raw_file_path = str(candidates[0])
    if log_file_path is None:
        log_file_path = str(processed_dir / "preprocessing.log")

    # Ensure output directories exist
    ensure_directories([processed_dir, Path(log_file_path).parent])

    logger = setup_logger("preprocess", log_file_path)
    logger.info("Starting preprocessing pipeline...")
    logger.info(f"Loading raw data from {raw_file_path}")

    # Load data
    df = load_raw_csv(raw_file_path)
    logger.info(f"Raw data shape: {df.shape}")

    # Verify required columns exist
    required_cols = [
        "laser_power",
        "scan_speed",
        "layer_thickness",
        "yield_strength",
        "ductility",
    ]
    missing_required = [c for c in required_cols if c not in df.columns]
    if missing_required:
        raise ValueError(f"Missing required columns: {missing_required}")

    # Sample count check
    check_sample_count(df, min_samples=50, logger=logger)

    # Drop zero‑variance columns
    zero_var = drop_zero_variance(df, logger)

    # Impute missing numeric values
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    medians = compute_medians(df, numeric_cols)
    df, imputed_total = impute_missing_values(df, medians, logger)

    # One‑hot encode alloy_type
    df, encoded_cols = encode_alloy_type(df, logger)

    # Split and normalize
    train_df, test_df, bounds = split_and_normalize(df, logger)

    # Save outputs
    train_path = processed_dir / "train.csv"
    test_path = processed_dir / "test.csv"
    train_df.to_csv(train_path, index=False)
    test_df.to_csv(test_path, index=False)
    logger.info(f"Saved train CSV to {train_path}")
    logger.info(f"Saved test CSV to {test_path}")

    # Save normalization bounds
    bounds_path = processed_dir / "normalization_bounds.json"
    save_normalization_bounds(bounds, bounds_path, logger)

    logger.info("Preprocessing completed successfully.")
    logger.info(f"Dropped zero‑variance columns: {zero_var}")
    logger.info(f"One‑hot encoded columns: {encoded_cols}")
    logger.info(f"Total imputed values: {imputed_total}")

def main() -> None:
    """
    Entry point for the preprocessing script.
    """
    try:
        validate_and_preprocess()
    except Exception as e:
        # Ensure a logger is available for the error message
        logger = get_logger("preprocess")
        logger.error(f"Preprocessing failed: {e}")
        raise

if __name__ == "__main__":
    main()
