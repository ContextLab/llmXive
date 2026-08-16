import os
import sys
import csv
import json
import logging
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional, Tuple

from config import (
    get_project_root,
    get_raw_data_dir,
    get_processed_data_dir,
    get_logs_dir,
    ensure_directories,
    get_random_seed,
    get_logger
)

# Numeric features required for normalization bounds
NUMERIC_FEATURES = ['laser_power', 'scan_speed', 'layer_thickness']

def setup_logger(name: str, log_file: str, level=logging.INFO) -> logging.Logger:
    """Setup a dedicated logger for preprocessing tasks."""
    ensure_directories()
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Avoid duplicate handlers if called multiple times
    if not logger.handlers:
        fh = logging.FileHandler(log_file)
        fh.setLevel(level)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        fh.setFormatter(formatter)
        logger.addHandler(fh)

        ch = logging.StreamHandler()
        ch.setLevel(level)
        ch.setFormatter(formatter)
        logger.addHandler(ch)

    return logger

def load_raw_csv(path: str) -> pd.DataFrame:
    """Load the raw CSV file."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Raw data file not found: {path}")
    return pd.read_csv(path)

def detect_missing_values(df: pd.DataFrame) -> Dict[str, int]:
    """Detect missing values in the DataFrame."""
    return df.isnull().sum().to_dict()

def compute_medians(df: pd.DataFrame) -> Dict[str, float]:
    """Compute median values for numeric columns with missing data."""
    medians = {}
    for col in df.columns:
        if pd.api.types.is_numeric_dtype(df[col]) and df[col].isnull().any():
            medians[col] = df[col].median()
    return medians

def impute_missing_values(df: pd.DataFrame, medians: Dict[str, float]) -> Tuple[pd.DataFrame, int]:
    """Impute missing values using median strategy."""
    df_imputed = df.copy()
    total_imputed = 0
    for col, median in medians.items():
        missing_count = df_imputed[col].isnull().sum()
        if missing_count > 0:
            df_imputed[col].fillna(median, inplace=True)
            total_imputed += missing_count
    return df_imputed, total_imputed

def filter_derived_columns(df: pd.DataFrame, excluded_columns: List[str]) -> Tuple[pd.DataFrame, List[str]]:
    """Filter out derived feature columns based on excluded list."""
    if not excluded_columns:
        return df, []

    cols_to_drop = [col for col in excluded_columns if col in df.columns]
    if cols_to_drop:
        df_filtered = df.drop(columns=cols_to_drop)
        return df_filtered, cols_to_drop
    return df, []

def encode_categorical(df: pd.DataFrame, categorical_col: str = 'alloy_type') -> Tuple[pd.DataFrame, List[str]]:
    """One-hot encode the categorical column."""
    if categorical_col not in df.columns:
        return df, []

    df_encoded = pd.get_dummies(df, columns=[categorical_col], prefix=categorical_col)
    encoded_cols = [col for col in df_encoded.columns if col.startswith(categorical_col)]
    return df_encoded, encoded_cols

def check_sample_count(df: pd.DataFrame, min_count: int = 50) -> None:
    """Check if sample count meets minimum requirement."""
    if len(df) < min_count:
        raise ValueError(f"Sample count ({len(df)}) is below minimum requirement ({min_count}).")

def check_zero_variance(df: pd.DataFrame, logger: logging.Logger) -> List[str]:
    """Detect and drop zero-variance columns."""
    zero_var_cols = []
    for col in df.select_dtypes(include=[np.number]).columns:
        if df[col].std() == 0:
            zero_var_cols.append(col)
            logger.warning(f"Column '{col}' has zero variance; dropping to prevent singularity.")
    
    if zero_var_cols:
        df = df.drop(columns=zero_var_cols)
    
    return zero_var_cols

def split_and_scale(
    df: pd.DataFrame,
    feature_cols: List[str],
    target_cols: List[str],
    random_seed: int,
    logger: logging.Logger
) -> Tuple[pd.DataFrame, pd.DataFrame, Dict[str, Dict[str, float]]]:
    """Split data into train/test and apply MinMaxScaler fit only on train."""
    from sklearn.model_selection import train_test_split
    from sklearn.preprocessing import MinMaxScaler

    # Split
    train_df, test_df = train_test_split(
        df, 
        test_size=0.2, 
        random_state=random_seed,
        shuffle=True
    )

    # Extract features
    X_train = train_df[feature_cols].copy()
    X_test = test_df[feature_cols].copy()

    # Scale
    scaler = MinMaxScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    # Capture bounds from the scaler (min=0, max=1 in scaled space, but we need original bounds)
    # MinMaxScaler stores feature_range and transform logic. We need original min/max for bounds.
    bounds = {}
    for i, col in enumerate(feature_cols):
        bounds[col] = {
            "min": float(X_train.min().iloc[i]),
            "max": float(X_train.max().iloc[i])
        }

    # Reconstruct DataFrames
    train_df_scaled = train_df.copy()
    for i, col in enumerate(feature_cols):
        train_df_scaled[col] = X_train_scaled[:, i]

    test_df_scaled = test_df.copy()
    for i, col in enumerate(feature_cols):
        test_df_scaled[col] = X_test_scaled[:, i]

    logger.info(f"Train/Test split completed. Train size: {len(train_df_scaled)}, Test size: {len(test_df_scaled)}")
    
    return train_df_scaled, test_df_scaled, bounds

def save_normalization_bounds(bounds: Dict[str, Dict[str, float]], output_path: str, logger: logging.Logger) -> None:
    """Save normalization bounds to a JSON file."""
    ensure_directories()
    with open(output_path, 'w') as f:
        json.dump(bounds, f, indent=2)
    logger.info(f"Normalization bounds saved to {output_path}")

def validate_and_preprocess(
    raw_path: str,
    schema_path: str,
    excluded_path: str,
    output_path: str,
    log_path: str
) -> Dict[str, Any]:
    """Main preprocessing pipeline."""
    logger = setup_logger("preprocess", log_path)
    
    # Load Schema
    from data.schema_validator import load_schema, validate_csv_schema
    schema = load_schema(schema_path)
    
    # Load Data
    logger.info(f"Loading raw data from {raw_path}")
    df = load_raw_csv(raw_path)
    
    # Validate Schema
    validate_csv_schema(df, schema, logger)
    
    # Scope Reduction Check (T016 requirement)
    if 'fatigue_life' not in df.columns:
        logger.info("[SCOPE] Reduced scope: fatigue_life missing; analysis restricted to yield_strength and ductility.")
    
    # Load Excluded Columns
    excluded_cols = []
    if os.path.exists(excluded_path):
        import yaml
        with open(excluded_path, 'r') as f:
            data = yaml.safe_load(f)
            excluded_cols = data.get('excluded_columns', [])
    
    # Filter Derived Columns
    df, dropped_derived = filter_derived_columns(df, excluded_cols)
    if dropped_derived:
        logger.warning(f"Dropped derived columns: {dropped_derived}")
    
    # Check Sample Count
    check_sample_count(df)
    
    # Detect & Impute
    missing = detect_missing_values(df)
    if any(v > 0 for v in missing.values()):
        medians = compute_medians(df)
        df, imputed_count = impute_missing_values(df, medians)
        logger.info(f"Imputed {imputed_count} missing values using median strategy.")
    else:
        logger.info("No missing values detected.")
    
    # Check Zero Variance
    zero_var = check_zero_variance(df, logger)
    if zero_var:
        logger.warning(f"Dropped zero-variance columns: {zero_var}")
    
    # Encode Categorical
    df, encoded_cols = encode_categorical(df, 'alloy_type')
    if encoded_cols:
        logger.info(f"One-hot encoded 'alloy_type' into: {encoded_cols}")
    
    # Define Features and Targets
    # Keep numeric features for scaling, drop targets from scaling features
    target_cols = ['yield_strength', 'ductility']
    feature_cols = [col for col in NUMERIC_FEATURES if col in df.columns]
    
    # Ensure targets exist
    for t in target_cols:
        if t not in df.columns:
            raise ValueError(f"Required target column '{t}' not found in dataset.")
    
    # Split and Scale
    train_df, test_df, bounds = split_and_scale(df, feature_cols, target_cols, get_random_seed(), logger)
    
    # Save Normalization Bounds (T019)
    bounds_path = os.path.join(get_processed_data_dir(), 'normalization_bounds.json')
    save_normalization_bounds(bounds, bounds_path, logger)
    
    # Save Processed Data
    train_df.to_csv(output_path, index=False)
    logger.info(f"Processed data saved to {output_path}")
    
    return {
        "bounds_path": bounds_path,
        "output_path": output_path,
        "log_path": log_path
    }

def main():
    """Entry point for preprocessing script."""
    from config import get_raw_data_dir, get_processed_data_dir, get_logs_dir, get_contracts_dir, ensure_directories
    import argparse

    parser = argparse.ArgumentParser(description="Preprocess AM alloy data")
    parser.add_argument("--input", type=str, default=None, help="Path to raw CSV")
    parser.add_argument("--output", type=str, default=None, help="Path to processed CSV")
    args = parser.parse_args()

    ensure_directories()

    raw_path = args.input if args.input else os.path.join(get_raw_data_dir(), 'am_data.csv')
    output_path = args.output if args.output else os.path.join(get_processed_data_dir(), 'processed_data.csv')
    schema_path = os.path.join(get_contracts_dir(), 'dataset.schema.yaml')
    excluded_path = os.path.join(get_processed_data_dir(), 'excluded_columns.yaml')
    log_path = os.path.join(get_processed_data_dir(), 'preprocessing.log')

    try:
        result = validate_and_preprocess(raw_path, schema_path, excluded_path, output_path, log_path)
        print(f"Preprocessing complete. Output: {result['output_path']}, Bounds: {result['bounds_path']}")
    except Exception as e:
        logging.error(f"Preprocessing failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
