import os
import sys
import csv
import json
import logging
import numpy as np
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
from pathlib import Path

# Local imports based on API surface
from config import (
    get_project_root,
    get_raw_data_dir,
    get_processed_data_dir,
    get_logs_dir,
    ensure_directories,
    get_logger,
    get_random_seed
)
from data.schema_validator import validate_csv_schema, load_schema

# Constants
RANDOM_SEED = get_random_seed()
np.random.seed(RANDOM_SEED)

def load_raw_csv(raw_data_path: Optional[str] = None) -> pd.DataFrame:
    """Load the raw CSV file."""
    if raw_data_path is None:
        raw_data_dir = get_raw_data_dir()
        raw_data_path = os.path.join(raw_data_dir, "am_data.csv")
    
    if not os.path.exists(raw_data_path):
        raise FileNotFoundError(f"Raw data file not found at {raw_data_path}")
    
    logging.info(f"Loading raw data from {raw_data_path}")
    return pd.read_csv(raw_data_path)

def detect_missing_values(df: pd.DataFrame) -> Dict[str, int]:
    """Detect and count missing values per column."""
    missing_counts = df.isnull().sum().to_dict()
    return {k: v for k, v in missing_counts.items() if v > 0}

def compute_medians(df: pd.DataFrame, columns: List[str]) -> Dict[str, float]:
    """Compute median values for specified columns."""
    medians = {}
    for col in columns:
        if col in df.columns:
            medians[col] = df[col].median()
    return medians

def impute_missing_values(df: pd.DataFrame, medians: Dict[str, float]) -> Tuple[pd.DataFrame, int]:
    """Impute missing values using median imputation."""
    df_imputed = df.copy()
    total_imputed = 0
    for col, val in medians.items():
        if col in df_imputed.columns:
            missing_mask = df_imputed[col].isnull()
            count = missing_mask.sum()
            if count > 0:
                df_imputed.loc[missing_mask, col] = val
                total_imputed += count
    return df_imputed, total_imputed

def filter_derived_columns(df: pd.DataFrame, excluded_cols: List[str]) -> Tuple[pd.DataFrame, List[str]]:
    """Filter out derived columns based on excluded list."""
    cols_to_drop = [c for c in excluded_cols if c in df.columns]
    if cols_to_drop:
        df_filtered = df.drop(columns=cols_to_drop)
        logging.warning(f"Dropped derived columns: {cols_to_drop}")
    else:
        df_filtered = df
    return df_filtered, cols_to_drop

def encode_categorical(df: pd.DataFrame, column: str = "alloy_type") -> Tuple[pd.DataFrame, List[str]]:
    """One-hot encode the specified categorical column."""
    if column not in df.columns:
        logging.warning(f"Categorical column '{column}' not found in dataframe.")
        return df, []
    
    # Perform one-hot encoding
    df_encoded = pd.get_dummies(df, columns=[column], prefix=column, drop_first=False)
    
    # Identify new columns
    new_cols = [c for c in df_encoded.columns if c.startswith(column)]
    logging.info(f"One-hot encoded '{column}' into {len(new_cols)} columns: {new_cols}")
    return df_encoded, new_cols

def check_sample_count(df: pd.DataFrame, min_count: int = 50) -> None:
    """Check if sample count is sufficient."""
    n = len(df)
    if n < min_count:
        raise ValueError(f"Sample count ({n}) is below minimum required ({min_count}). Pipeline halted.")
    logging.info(f"Sample count check passed: {n} >= {min_count}")

def check_zero_variance(df: pd.DataFrame, log_path: str) -> List[str]:
    """Detect and drop zero-variance columns."""
    zero_var_cols = []
    logger = logging.getLogger()
    
    for col in df.select_dtypes(include=[np.number]).columns:
        if df[col].nunique() <= 1:
            zero_var_cols.append(col)
            logger.warning(f"Column '{col}' has zero variance; dropping to prevent singularity.")
    
    if zero_var_cols:
        df = df.drop(columns=zero_var_cols)
    
    return zero_var_cols

def split_and_scale(df: pd.DataFrame, target_cols: List[str], test_size: float = 0.2) -> Dict[str, Any]:
    """Split data into train/test and apply MinMaxScaler fit only on train."""
    from sklearn.model_selection import train_test_split
    from sklearn.preprocessing import MinMaxScaler

    # Separate features and targets
    # Assuming all numeric columns except targets are features
    feature_cols = [c for c in df.columns if c not in target_cols and df[c].dtype in [np.float64, np.int64]]
    
    if not feature_cols:
        raise ValueError("No feature columns found for scaling.")

    X = df[feature_cols]
    y = df[target_cols]

    # Split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=RANDOM_SEED
    )

    # Scale
    scaler = MinMaxScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    # Create scaled dataframes
    X_train_scaled_df = pd.DataFrame(X_train_scaled, columns=feature_cols, index=X_train.index)
    X_test_scaled_df = pd.DataFrame(X_test_scaled, columns=feature_cols, index=X_test.index)
    y_train_df = y_train.reset_index(drop=True)
    y_test_df = y_test.reset_index(drop=True)

    return {
        "X_train": X_train_scaled_df,
        "X_test": X_test_scaled_df,
        "y_train": y_train_df,
        "y_test": y_test_df,
        "scaler": scaler,
        "feature_cols": feature_cols
    }

def save_normalization_bounds(scaler: MinMaxScaler, feature_cols: List[str], output_path: str) -> None:
    """Save normalization bounds (train set min/max) to JSON."""
    bounds = {
        "feature_columns": feature_cols,
        "min_values": scaler.data_min_.tolist(),
        "max_values": scaler.data_max_.tolist(),
        "data_range_min": scaler.data_range_.tolist()
    }
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(bounds, f, indent=2)
    
    logging.info(f"Normalization bounds saved to {output_path}")

def validate_and_preprocess() -> Dict[str, Any]:
    """Main orchestration function for validation and preprocessing."""
    ensure_directories()
    
    # Setup logging
    log_file = os.path.join(get_logs_dir(), "preprocessing.log")
    logger = get_logger("preprocess", log_file)
    
    # 1. Load Raw Data
    try:
        df = load_raw_csv()
    except FileNotFoundError as e:
        logger.critical(str(e))
        raise

    # 2. Schema Validation
    schema_path = os.path.join(get_project_root(), "contracts", "dataset.schema.yaml")
    if not validate_csv_schema(df, schema_path):
        logger.error("Schema validation failed.")
        sys.exit(1)

    # 3. Scope Reduction Check (fatigue_life)
    if "fatigue_life" not in df.columns:
        logger.warning("[SCOPE] Reduced scope: fatigue_life missing; analysis restricted to yield_strength and ductility.")
    
    # 4. Load Excluded Columns (T015B)
    excluded_path = os.path.join(get_processed_data_dir(), "excluded_columns.yaml")
    excluded_cols = []
    if os.path.exists(excluded_path):
        import yaml
        with open(excluded_path, 'r') as f:
            data = yaml.safe_load(f)
            excluded_cols = data.get("excluded_columns", [])
        logger.info(f"Loaded excluded columns from {excluded_path}: {excluded_cols}")
    else:
        logger.warning(f"Excluded columns file not found at {excluded_path}; proceeding without filtering derived columns.")

    # 5. Filter Derived Columns
    df, dropped_derived = filter_derived_columns(df, excluded_cols)

    # 6. Detect Missing Values & Impute
    missing = detect_missing_values(df)
    if missing:
        logger.info(f"Detected missing values in columns: {missing}")
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        medians = compute_medians(df, numeric_cols)
        df, total_imputed = impute_missing_values(df, medians)
        logger.info(f"Imputed {total_imputed} missing values using column medians.")
    else:
        logger.info("No missing values detected.")

    # 7. Check Sample Count
    check_sample_count(df)

    # 8. One-Hot Encoding
    df, encoded_cols = encode_categorical(df, "alloy_type")

    # 9. Zero-Variance Check
    zero_var = check_zero_variance(df, log_file)

    # 10. Define Targets
    target_cols = []
    if "yield_strength" in df.columns:
        target_cols.append("yield_strength")
    if "ductility" in df.columns:
        target_cols.append("ductility")
    
    if not target_cols:
        raise ValueError("No valid target columns (yield_strength, ductility) found.")

    # 11. Split and Scale
    split_data = split_and_scale(df, target_cols)
    
    # 12. Save Normalization Bounds (T019)
    bounds_path = os.path.join(get_processed_data_dir(), "normalization_bounds.json")
    save_normalization_bounds(split_data["scaler"], split_data["feature_cols"], bounds_path)

    # 13. Save Processed Data
    processed_path = os.path.join(get_processed_data_dir(), "am_data_processed.csv")
    # Combine train/test for storage or just train? Usually train for model fitting.
    # For this pipeline, we save the full processed dataset split info might be in metadata.
    # Let's save the full processed df (with NaNs handled, encoded) before split for reference, 
    # but the split_data contains the scaled versions.
    # Standard practice: Save the processed raw-ish version, and scaled versions in memory or separate files.
    # Let's save the scaled train/test to CSVs for downstream tasks.
    
    # Save train
    train_df = pd.concat([split_data["X_train"], split_data["y_train"]], axis=1)
    train_df.to_csv(os.path.join(get_processed_data_dir(), "am_data_train.csv"), index=False)
    
    # Save test
    test_df = pd.concat([split_data["X_test"], split_data["y_test"]], axis=1)
    test_df.to_csv(os.path.join(get_processed_data_dir(), "am_data_test.csv"), index=False)

    logger.info("Preprocessing complete. Artifacts saved.")
    return split_data

def main():
    """Entry point for preprocessing script."""
    try:
        result = validate_and_preprocess()
        logging.info("Preprocessing pipeline executed successfully.")
    except Exception as e:
        logging.critical(f"Preprocessing pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
