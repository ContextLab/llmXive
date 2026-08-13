import os
import sys
import csv
import json
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

from config import get_processed_data_dir, get_raw_data_dir, get_logs_dir, get_random_seed, ensure_directories, get_logger
from data.schema_validator import validate_csv_schema
from utils.logger import setup_logging

logger = logging.getLogger(__name__)

def load_raw_csv(filepath: Optional[str] = None) -> pd.DataFrame:
    """Load raw CSV file."""
    if filepath is None:
        raw_dir = get_raw_data_dir()
        # Default filename from tasks.md
        filepath = str(raw_dir / "am_data.csv")
    
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Raw data file not found at {filepath}. Please ensure data is placed manually or download script ran.")
    
    logger.info(f"Loading raw data from {filepath}")
    return pd.read_csv(filepath)

def detect_missing_values(df: pd.DataFrame) -> Dict[str, int]:
    """Detect missing values in the dataframe."""
    return df.isnull().sum().to_dict()

def compute_medians(df: pd.DataFrame, columns: List[str]) -> Dict[str, float]:
    """Compute median for specified columns."""
    return {col: df[col].median() for col in columns if col in df.columns}

def impute_missing_values(df: pd.DataFrame, medians: Dict[str, float]) -> Tuple[pd.DataFrame, int]:
    """Impute missing values using median."""
    count = 0
    df_imputed = df.copy()
    for col, median in medians.items():
        if col in df_imputed.columns:
            missing_count = df_imputed[col].isnull().sum()
            if missing_count > 0:
                df_imputed[col] = df_imputed[col].fillna(median)
                count += missing_count
                logger.info(f"Imputed {missing_count} missing values in column '{col}' with median {median:.2f}")
    return df_imputed, count

def encode_categorical(df: pd.DataFrame, column: str) -> Tuple[pd.DataFrame, List[str]]:
    """One-hot encode a categorical column and drop the original."""
    if column not in df.columns:
        logger.warning(f"Categorical column '{column}' not found. Skipping encoding.")
        return df, []
    
    logger.info(f"One-hot encoding column: {column}")
    df_encoded = pd.get_dummies(df, columns=[column], prefix=column)
    new_cols = [col for col in df_encoded.columns if col.startswith(column)]
    return df_encoded, new_cols

def check_sample_count(df: pd.DataFrame, min_count: int = 50) -> None:
    """Check if sample count is sufficient."""
    n = len(df)
    if n < min_count:
        error_msg = f"Sample count ({n}) is below minimum threshold ({min_count}). Halting execution."
        logger.error(error_msg)
        raise ValueError(error_msg)
    logger.info(f"Sample count check passed: {n} samples.")

def check_zero_variance(df: pd.DataFrame) -> List[str]:
    """Detect and return columns with zero variance."""
    zero_var_cols = []
    for col in df.select_dtypes(include=[np.number]).columns:
        if df[col].var() == 0:
            zero_var_cols.append(col)
            logger.warning(f"Column '{col}' has zero variance; dropping to prevent singularity.")
    return zero_var_cols

def split_and_scale(X: np.ndarray, y: np.ndarray, test_size: float = 0.2) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, Any]:
    """Split data and apply MinMaxScaler fit on train only."""
    from sklearn.model_selection import train_test_split
    from sklearn.preprocessing import MinMaxScaler
    
    seed = get_random_seed()
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=test_size, random_state=seed)
    
    scaler = MinMaxScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    logger.info(f"Train set size: {X_train.shape[0]}, Test set size: {X_test.shape[0]}")
    return X_train_scaled, X_test_scaled, y_train, y_test, scaler

def save_normalization_bounds(scaler: Any, filepath: Optional[str] = None) -> str:
    """Save normalization bounds (min/max) to JSON."""
    if filepath is None:
        filepath = str(get_processed_data_dir() / "normalization_bounds.json")
    
    bounds = {
        "feature_names": scaler.feature_names_in_ if hasattr(scaler, 'feature_names_in_') else [],
        "min": scaler.data_min_.tolist(),
        "max": scaler.data_max_.tolist()
    }
    
    with open(filepath, 'w') as f:
        json.dump(bounds, f, indent=2)
    logger.info(f"Normalization bounds saved to {filepath}")
    return filepath

def validate_and_preprocess(raw_filepath: Optional[str] = None) -> pd.DataFrame:
    """Main preprocessing pipeline."""
    # Load
    df = load_raw_csv(raw_filepath)
    
    # Validate Schema
    schema_path = "contracts/dataset.schema.yaml"
    validate_csv_schema(df, schema_path)
    
    # Handle Missing Values
    missing = detect_missing_values(df)
    if any(v > 0 for v in missing.values()):
        logger.info(f"Missing values detected: {missing}")
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        medians = compute_medians(df, numeric_cols)
        df, imputed_count = impute_missing_values(df, medians)
    else:
        logger.info("No missing values detected.")
    
    # Encode Categoricals
    if 'alloy_type' in df.columns:
        df, _ = encode_categorical(df, 'alloy_type')
    
    # Check Sample Count
    check_sample_count(df)
    
    # Check Zero Variance
    zero_var_cols = check_zero_variance(df)
    if zero_var_cols:
        df = df.drop(columns=zero_var_cols)
    
    return df

def main():
    """Entry point for preprocessing."""
    setup_logging()
    
    try:
        df = validate_and_preprocess()
        
        # Identify features and targets for saving processed data
        # Assuming standard columns exist after encoding
        target_cols = [c for c in ['yield_strength', 'ductility', 'fatigue_life'] if c in df.columns]
        if not target_cols:
            raise ValueError("No target columns found.")
        
        feature_cols = [c for c in df.columns if c not in target_cols]
        
        X = df[feature_cols].values
        y = df[target_cols].values
        
        X_train, X_test, y_train, y_test, scaler = split_and_scale(X, y)
        
        # Save processed data (concatenated for convenience, with a split indicator)
        # Or save train/test separately. For simplicity, save the full processed DF with a 'split' column?
        # The task T017 says save normalization_bounds. T016 says split and scale.
        # Let's save the processed dataframe to data/processed/processed_data.csv
        # We need to reconstruct the dataframe with scaled values?
        # Usually, we save the raw processed (encoded/imputed) data and let the model loader handle scaling,
        # OR we save the scaled data.
        # Given T017 saves bounds, we assume the model loader will apply scaling.
        # So we save the df with encoded/imputed but NOT scaled values, and the scaler object?
        # Or we save the scaled data. Let's save the scaled data to processed_data.csv for the model trainer.
        
        # Reconstruct df with scaled values for X part
        # This is tricky because X is numpy array.
        # Let's just save the original processed df and the scaler separately?
        # The task T014 says "handle missing values", T016 "split and scale".
        # Let's save the processed (imputed/encoded) df to processed_data.csv.
        # The model trainer will load this, re-split, and re-scale using the saved scaler logic or re-fit?
        # T016 says "fit only on training set". If we save the full df, the trainer must re-split.
        # So we save the processed df.
        
        processed_dir = get_processed_data_dir()
        processed_path = processed_dir / "processed_data.csv"
        df.to_csv(processed_path, index=False)
        logger.info(f"Processed data saved to {processed_path}")
        
        # Save normalization bounds (T017)
        # We need to fit a scaler on the TRAIN set of the processed data to get bounds.
        # Since we just saved the raw processed df, we must re-load and split here to save bounds?
        # Or we do it in main() before saving.
        
        # Let's re-split here to save bounds correctly
        X_full = df[feature_cols].values
        y_full = df[target_cols].values
        X_tr, X_te, y_tr, y_te, scaler_obj = split_and_scale(X_full, y_full)
        
        save_normalization_bounds(scaler_obj)
        
    except Exception as e:
        logger.error(f"Preprocessing failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
