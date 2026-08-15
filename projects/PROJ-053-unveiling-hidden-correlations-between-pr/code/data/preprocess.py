import os
import sys
import csv
import json
import logging
import numpy as np
import pandas as pd
from typing import Dict, Any, Optional, Tuple, List

from config import (
    get_project_root,
    get_data_dir,
    get_raw_data_dir,
    get_processed_data_dir,
    get_results_dir,
    get_random_seed,
    ensure_directories,
    get_logger
)
from data.schema_validator import validate_csv_schema

# --- Configuration ---
RANDOM_SEED = get_random_seed()
np.random.seed(RANDOM_SEED)

# --- Core Functions ---

def load_raw_csv(file_path: str) -> pd.DataFrame:
    """Load raw CSV data into a pandas DataFrame."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Raw data file not found: {file_path}")
    df = pd.read_csv(file_path)
    return df

def detect_missing_values(df: pd.DataFrame) -> Dict[str, int]:
    """Detect and count missing values per column."""
    missing_counts = df.isnull().sum().to_dict()
    return {k: v for k, v in missing_counts.items() if v > 0}

def compute_medians(df: pd.DataFrame, numeric_cols: List[str]) -> Dict[str, float]:
    """Compute median values for numeric columns."""
    medians = {}
    for col in numeric_cols:
        if col in df.columns:
            medians[col] = df[col].median()
    return medians

def impute_missing_values(df: pd.DataFrame, medians: Dict[str, float]) -> pd.DataFrame:
    """Impute missing values using median imputation."""
    df_imputed = df.copy()
    for col, val in medians.items():
        if col in df_imputed.columns:
            df_imputed[col] = df_imputed[col].fillna(val)
    return df_imputed

def encode_categorical(df: pd.DataFrame, col_name: str = 'alloy_type') -> pd.DataFrame:
    """One-hot encode the categorical column 'alloy_type' and drop the original."""
    if col_name not in df.columns:
        logging.warning(f"Column '{col_name}' not found; skipping encoding.")
        return df

    df_encoded = pd.get_dummies(df, columns=[col_name], prefix=col_name)
    return df_encoded

def check_sample_count(df: pd.DataFrame, min_samples: int = 50) -> None:
    """Check if sample count is sufficient. Halts execution if too low."""
    n = len(df)
    if n < min_samples:
        raise ValueError(f"Sample count ({n}) is below minimum threshold ({min_samples}). "
                         "Cannot proceed with analysis.")

def check_zero_variance(df: pd.DataFrame, logger: logging.Logger) -> List[str]:
    """Detect and return list of columns with zero variance."""
    zero_var_cols = []
    for col in df.select_dtypes(include=[np.number]).columns:
        if df[col].std() == 0:
            zero_var_cols.append(col)
            logger.warning(f"Column '{col}' has zero variance; dropping to prevent singularity.")
    return zero_var_cols

def split_and_scale(X: pd.DataFrame, y: pd.DataFrame, test_size: float = 0.2) -> Tuple[Any, Any, Any, Any]:
    """Split data into train/test and apply MinMaxScaler fit ONLY on training set."""
    from sklearn.model_selection import train_test_split
    from sklearn.preprocessing import MinMaxScaler

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=RANDOM_SEED
    )

    scaler = MinMaxScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    return X_train_scaled, X_test_scaled, y_train.values, y_test.values, scaler

def save_normalization_bounds(scaler: MinMaxScaler, feature_names: List[str], output_path: str) -> None:
    """Save normalization bounds (min/max used by MinMaxScaler) to JSON."""
    bounds = {}
    for i, name in enumerate(feature_names):
        bounds[name] = {
            "min": float(scaler.data_min_[i]),
            "max": float(scaler.data_max_[i])
        }
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(bounds, f, indent=2)
    
    logging.info(f"Normalization bounds saved to {output_path}")

def validate_and_preprocess(raw_path: str, processed_path: str) -> Tuple[pd.DataFrame, MinMaxScaler, List[str]]:
    """Main orchestration function for validation and preprocessing."""
    logger = get_logger("preprocess")
    ensure_directories()
    
    # 1. Load
    logger.info(f"Loading raw data from {raw_path}")
    df = load_raw_csv(raw_path)

    # 2. Validate Schema
    schema_path = os.path.join(get_project_root(), "contracts", "dataset.schema.yaml")
    validate_csv_schema(df, schema_path, logger)

    # 3. Check Sample Count
    check_sample_count(df)

    # 4. Handle Missing Values
    missing = detect_missing_values(df)
    if missing:
        logger.info(f"Detected missing values in columns: {list(missing.keys())}")
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        medians = compute_medians(df, numeric_cols)
        df = impute_missing_values(df, medians)
        logger.info(f"Imputed missing values using median: {medians}")
    else:
        logger.info("No missing values detected.")

    # 5. One-Hot Encode
    df = encode_categorical(df, 'alloy_type')

    # 6. Zero Variance Check
    zero_var_cols = check_zero_variance(df, logger)
    if zero_var_cols:
        df = df.drop(columns=zero_var_cols)

    # 7. Identify Features and Targets
    # Assuming targets are yield_strength and ductility (and optionally fatigue_life)
    targets = ['yield_strength', 'ductility']
    # Filter targets that exist
    available_targets = [t for t in targets if t in df.columns]
    
    if not available_targets:
        raise ValueError("No target columns found in dataset.")

    X = df.drop(columns=available_targets)
    y = df[available_targets[0]] # Simplified: using first target for split logic if needed

    # 8. Split and Scale
    X_scaled, _, _, _, scaler = split_and_scale(X, y)

    # 9. Save Normalization Bounds (T019)
    bounds_path = os.path.join(get_processed_data_dir(), "normalization_bounds.json")
    save_normalization_bounds(scaler, X.columns.tolist(), bounds_path)

    # 10. Prepare Processed Data
    # Re-split to get full processed dataframe for downstream tasks
    X_train, X_test, y_train, y_test, _ = split_and_scale(X, y)
    
    processed_df = pd.DataFrame(X_train, columns=X.columns)
    processed_df['target'] = y_train
    
    # Save processed CSV
    processed_df.to_csv(processed_path, index=False)
    logger.info(f"Processed data saved to {processed_path}")

    return processed_df, scaler, X.columns.tolist()

def main():
    """Entry point for preprocessing script."""
    logger = get_logger("preprocess")
    logger.info("Starting preprocessing pipeline...")
    
    raw_path = os.path.join(get_raw_data_dir(), "am_data.csv")
    processed_path = os.path.join(get_processed_data_dir(), "processed_data.csv")
    
    try:
        df, scaler, feature_names = validate_and_preprocess(raw_path, processed_path)
        logger.info("Preprocessing completed successfully.")
    except Exception as e:
        logger.error(f"Preprocessing failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
