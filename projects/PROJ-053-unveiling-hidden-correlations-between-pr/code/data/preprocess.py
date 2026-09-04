import os
import sys
import csv
import json
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Import config utilities
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import (
    get_project_root,
    get_processed_data_dir,
    get_raw_data_dir,
    get_contracts_dir,
    get_random_seed,
    ensure_directories,
    get_logger
)

# Import schema validator
from data.schema_validator import validate_csv_schema, load_schema

# Set random seed for reproducibility
np.random.seed(get_random_seed())

def setup_logger(name: str, log_file: str, level=logging.INFO) -> logging.Logger:
    """
    Set up a logger that writes to both console and file.
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Create file handler
    fh = logging.FileHandler(log_file, mode='w')
    fh.setLevel(level)

    # Create console handler
    ch = logging.StreamHandler()
    ch.setLevel(level)

    # Create formatter
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)

    # Add handlers to the logger
    logger.addHandler(fh)
    logger.addHandler(ch)

    return logger

def load_raw_csv(file_path: str) -> pd.DataFrame:
    """
    Load a CSV file into a pandas DataFrame.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Raw data file not found: {file_path}")
    
    df = pd.read_csv(file_path)
    return df

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
            missing_counts[col] = 0  # Column missing entirely
    return missing_counts

def compute_medians(df: pd.DataFrame, numeric_cols: List[str]) -> Dict[str, float]:
    """
    Compute median values for imputation.
    """
    medians = {}
    for col in numeric_cols:
        if col in df.columns and df[col].dtype in ['float64', 'float32', 'int64', 'int32']:
            medians[col] = float(df[col].median())
    return medians

def impute_missing_values(df: pd.DataFrame, medians: Dict[str, float], logger: logging.Logger) -> Tuple[pd.DataFrame, int]:
    """
    Impute missing values using median.
    Returns the imputed DataFrame and total count of imputed entries.
    """
    total_imputed = 0
    for col, median in medians.items():
        if col in df.columns:
            missing_mask = df[col].isna()
            count = missing_mask.sum()
            if count > 0:
                df.loc[missing_mask, col] = median
                total_imputed += count
                logger.info(f"Imputed {count} missing values in column '{col}' with median {median:.4f}")
    
    if total_imputed > 0:
        logger.info(f"Total imputed values: {total_imputed}")
    else:
        logger.info("No missing values found to impute.")
    
    return df, total_imputed

def filter_derived_columns(df: pd.DataFrame, excluded_cols_path: str, logger: logging.Logger) -> Tuple[pd.DataFrame, List[str]]:
    """
    Filter out derived columns based on excluded_columns.yaml.
    """
    dropped_cols = []
    
    if os.path.exists(excluded_cols_path):
        try:
            with open(excluded_cols_path, 'r') as f:
                import yaml
                data = yaml.safe_load(f)
                excluded = data.get('excluded_columns', [])
                if excluded:
                    for col in excluded:
                        if col in df.columns:
                            df = df.drop(columns=[col])
                            dropped_cols.append(col)
                            logger.warning(f"Dropped derived/excluded column: '{col}'")
        except Exception as e:
            logger.warning(f"Could not load excluded_columns.yaml: {e}")
    else:
        logger.info("No excluded_columns.yaml found; proceeding with all validated columns.")
    
    return df, dropped_cols

def encode_categorical(df: pd.DataFrame, logger: logging.Logger) -> Tuple[pd.DataFrame, List[str]]:
    """
    One-hot encode categorical columns (specifically 'alloy_type').
    """
    encoded_cols = []
    
    if 'alloy_type' in df.columns:
        logger.info("One-hot encoding 'alloy_type' column...")
        # Create binary columns for each unique alloy type
        unique_types = df['alloy_type'].unique()
        for alloy in unique_types:
            new_col_name = f"is_{alloy}"
            df[new_col_name] = (df['alloy_type'] == alloy).astype(int)
            encoded_cols.append(new_col_name)
        
        # Drop original categorical column
        df = df.drop(columns=['alloy_type'])
        logger.info(f"One-hot encoding complete. Created columns: {encoded_cols}")
    else:
        logger.info("No 'alloy_type' column found; skipping one-hot encoding.")
    
    return df, encoded_cols

def check_zero_variance(df: pd.DataFrame, logger: logging.Logger) -> List[str]:
    """
    Detect and drop columns with zero variance.
    """
    zero_var_cols = []
    for col in df.select_dtypes(include=[np.number]).columns:
        if df[col].nunique() <= 1:
            zero_var_cols.append(col)
            logger.warning(f"Zero variance detected in column '{col}'. Dropping.")
    
    if zero_var_cols:
        df = df.drop(columns=zero_var_cols)
        logger.info(f"Dropped {len(zero_var_cols)} zero-variance columns.")
    
    return zero_var_cols

def check_sample_count(df: pd.DataFrame, min_samples: int = 50, logger: logging.Logger = None) -> None:
    """
    Verify sample count meets minimum requirement.
    """
    n = len(df)
    if logger:
        logger.info(f"Dataset contains {n} samples.")
    
    if n < min_samples:
        error_msg = f"Insufficient data for GPR training; minimum {min_samples} samples required. Found {n}."
        if logger:
            logger.error(error_msg)
        raise ValueError(error_msg)

def split_and_scale(df: pd.DataFrame, logger: logging.Logger) -> Tuple[pd.DataFrame, pd.DataFrame, Dict[str, Dict[str, float]]]:
    """
    Split data into train/test sets and normalize.
    Returns train_df, test_df, and normalization_bounds.
    """
    from sklearn.model_selection import train_test_split
    from sklearn.preprocessing import MinMaxScaler

    # Identify numeric columns
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    target_cols = ['yield_strength', 'ductility']
    
    # Filter to only include columns that exist
    available_targets = [c for c in target_cols if c in numeric_cols]
    feature_cols = [c for c in numeric_cols if c not in target_cols]

    if not feature_cols:
        logger.error("No feature columns found for scaling.")
        raise ValueError("No feature columns found.")

    # Stratified split if alloy_type was present (but it's already encoded/removed)
    # We'll do a simple random split with fixed seed
    X = df[feature_cols]
    y = df[available_targets] if available_targets else pd.DataFrame()

    # Split
    if len(y) > 0:
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=get_random_seed(), shuffle=True
        )
        train_df = pd.concat([X_train, y_train], axis=1)
        test_df = pd.concat([X_test, y_test], axis=1)
    else:
        X_train, X_test = train_test_split(
            X, test_size=0.2, random_state=get_random_seed(), shuffle=True
        )
        train_df = X_train
        test_df = X_test

    # Normalize
    scaler = MinMaxScaler()
    scaler.fit(X_train)
    
    # Transform
    train_df[feature_cols] = scaler.transform(X_train)
    test_df[feature_cols] = scaler.transform(X_test)

    # Save normalization bounds
    normalization_bounds = {}
    for i, col in enumerate(feature_cols):
        normalization_bounds[col] = {
            "min": float(scaler.data_min_[i]),
            "max": float(scaler.data_max_[i])
        }

    logger.info(f"Data split: Train={len(train_df)}, Test={len(test_df)}")
    logger.info("Normalization bounds saved.")

    return train_df, test_df, normalization_bounds

def save_normalization_bounds(bounds: Dict[str, Dict[str, float]], output_path: str, logger: logging.Logger) -> None:
    """
    Save normalization bounds to JSON file.
    """
    with open(output_path, 'w') as f:
        json.dump(bounds, f, indent=2)
    logger.info(f"Normalization bounds saved to {output_path}")

def validate_and_preprocess(raw_file_path: str, log_file_path: str) -> None:
    """
    Main preprocessing pipeline:
    1. Load raw CSV
    2. Validate schema
    3. Check for excluded columns
    4. Impute missing values
    5. Encode categoricals
    6. Check zero variance
    7. Split and scale
    8. Save outputs and logs
    """
    # Setup logger
    logger = setup_logger("preprocess", log_file_path)
    logger.info("Starting preprocessing pipeline...")

    # Define paths
    processed_dir = get_processed_data_dir()
    contracts_dir = get_contracts_dir()
    schema_path = os.path.join(contracts_dir, "dataset.schema.yaml")
    excluded_cols_path = os.path.join(processed_dir, "excluded_columns.yaml")
    bounds_path = os.path.join(processed_dir, "normalization_bounds.json")
    train_path = os.path.join(processed_dir, "train.csv")
    test_path = os.path.join(processed_dir, "test.csv")

    ensure_directories()

    # 1. Load raw data
    logger.info(f"Loading raw data from {raw_file_path}")
    df = load_raw_csv(raw_file_path)
    logger.info(f"Loaded {len(df)} rows, {len(df.columns)} columns")

    # 2. Validate schema
    logger.info("Validating schema...")
    required_cols = ['laser_power', 'scan_speed', 'layer_thickness', 'yield_strength', 'ductility']
    try:
        validate_csv_schema(df, schema_path, required_cols)
        logger.info("Schema validation passed.")
    except ValueError as e:
        logger.error(f"Schema validation failed: {e}")
        raise

    # 3. Check scope (fatigue_life)
    if 'fatigue_life' not in df.columns:
        logger.warning("[SCOPE] Reduced scope: fatigue_life missing; analysis restricted to yield_strength and ductility.")
        # Write target config
        target_config_path = os.path.join(processed_dir, "target_config.json")
        with open(target_config_path, 'w') as f:
            json.dump({"active_targets": ["yield_strength", "ductility"]}, f)
        logger.info(f"Target config written to {target_config_path}")
    else:
        logger.info("fatigue_life column present; full scope analysis.")

    # 4. Filter derived/excluded columns
    df, dropped_cols = filter_derived_columns(df, excluded_cols_path, logger)

    # 5. Check zero variance
    zero_var_cols = check_zero_variance(df, logger)

    # 6. Detect missing values in required columns
    missing_counts = detect_missing_values(df, required_cols)
    total_missing = sum(missing_counts.values())
    if total_missing > 0:
        logger.warning(f"Missing values detected in required columns: {missing_counts}")
    else:
        logger.info("No missing values in required columns.")

    # 7. Impute missing values
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    medians = compute_medians(df, numeric_cols)
    df, imputed_count = impute_missing_values(df, medians, logger)

    # 8. Encode categoricals
    df, encoded_cols = encode_categorical(df, logger)

    # 9. Check sample count
    check_sample_count(df, min_samples=50, logger=logger)

    # 10. Split and scale
    train_df, test_df, bounds = split_and_scale(df, logger)

    # 11. Save outputs
    train_df.to_csv(train_path, index=False)
    test_df.to_csv(test_path, index=False)
    logger.info(f"Train data saved to {train_path}")
    logger.info(f"Test data saved to {test_path}")

    save_normalization_bounds(bounds, bounds_path, logger)

    # 12. Log final summary
    logger.info("Preprocessing completed successfully.")
    logger.info(f"Total dropped columns (derived): {len(dropped_cols)}")
    logger.info(f"Total dropped columns (zero-variance): {len(zero_var_cols)}")
    logger.info(f"Total imputed values: {imputed_count}")
    logger.info(f"Encoded columns: {encoded_cols}")
    logger.info(f"Normalization bounds saved.")

def main():
    """
    Entry point for preprocessing script.
    """
    raw_data_dir = get_raw_data_dir()
    processed_data_dir = get_processed_data_dir()
    log_dir = os.path.join(processed_data_dir, "..", "logs")
    
    # Ensure directories exist
    ensure_directories()

    # Determine input file
    raw_file = os.path.join(raw_data_dir, "am_data.csv")
    log_file = os.path.join(processed_data_dir, "preprocessing.log")

    if not os.path.exists(raw_file):
        logger = setup_logger("preprocess", log_file)
        logger.error(f"Raw data file not found: {raw_file}")
        logger.error("Please ensure data is downloaded or manually placed at data/raw/am_data.csv")
        sys.exit(1)

    try:
        validate_and_preprocess(raw_file, log_file)
    except Exception as e:
        # Ensure logger is set up to catch the error
        if not os.path.exists(log_file):
            setup_logger("preprocess", log_file)
        logging.getLogger("preprocess").error(f"Preprocessing failed: {e}")
        raise

if __name__ == "__main__":
    main()