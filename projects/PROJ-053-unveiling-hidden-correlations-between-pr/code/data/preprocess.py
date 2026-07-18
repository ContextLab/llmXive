import os
import sys
import csv
import json
import logging
import numpy as np
from typing import Dict, Any, Optional, Tuple, List
from pathlib import Path

from config import (
    get_raw_data_dir, get_processed_data_dir, get_project_root,
    get_random_seed, ensure_directories, get_logger
)
from data.schema_validator import load_schema, validate_csv_schema

logger = logging.getLogger(__name__)

def load_raw_csv(csv_path: Optional[str] = None) -> Tuple[List[str], List[Dict[str, Any]]]:
    """Load raw CSV file and return headers and rows."""
    if csv_path is None:
        raw_dir = get_raw_data_dir()
        # Try standard filename
        csv_path = os.path.join(raw_dir, "am_data.csv")
        if not os.path.exists(csv_path):
            # Try any csv in raw dir
            files = [f for f in os.listdir(raw_dir) if f.endswith('.csv')]
            if not files:
                raise FileNotFoundError(f"No CSV file found in {raw_dir}. Please place data there.")
            csv_path = os.path.join(raw_dir, files[0])
    
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Raw data file not found: {csv_path}")
    
    with open(csv_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames
        rows = list(reader)
    
    logger.info(f"Loaded {len(rows)} rows from {csv_path}")
    return headers, rows

def detect_missing_values(rows: List[Dict[str, Any]], required_cols: List[str]) -> Dict[str, int]:
    """Detect missing values in required columns."""
    missing_counts = {col: 0 for col in required_cols}
    for row in rows:
        for col in required_cols:
            val = row.get(col, '')
            if val is None or str(val).strip() == '':
                missing_counts[col] += 1
    return missing_counts

def compute_medians(rows: List[Dict[str, Any]], numeric_cols: List[str]) -> Dict[str, float]:
    """Compute median values for numeric columns."""
    medians = {}
    for col in numeric_cols:
        values = []
        for row in rows:
            val = row.get(col, '')
            if val and str(val).strip() != '':
                try:
                    values.append(float(val))
                except ValueError:
                    pass
        if values:
            medians[col] = float(np.median(values))
        else:
            medians[col] = 0.0
    return medians

def impute_missing_values(rows: List[Dict[str, Any]], medians: Dict[str, float], cols: List[str]) -> List[Dict[str, Any]]:
    """Impute missing values with median."""
    imputed_rows = []
    for row in rows:
        new_row = row.copy()
        for col in cols:
            val = new_row.get(col, '')
            if val is None or str(val).strip() == '':
                new_row[col] = str(medians.get(col, 0.0))
        imputed_rows.append(new_row)
    return imputed_rows

def encode_categorical(rows: List[Dict[str, Any]], col: str) -> Tuple[List[Dict[str, Any]], List[str]]:
    """One-hot encode a categorical column."""
    if col not in rows[0]:
        return rows, []
    
    unique_vals = sorted(list(set(row[col] for row in rows if row.get(col))))
    encoded_rows = []
    
    for row in rows:
        new_row = row.copy()
        val = row.get(col, '')
        for v in unique_vals:
            new_row[f"{col}_{v}"] = 1 if val == v else 0
        encoded_rows.append(new_row)
    
    return encoded_rows, [f"{col}_{v}" for v in unique_vals]

def check_sample_count(rows: List[Dict[str, Any]], min_n: int = 50):
    """Check if sample count is sufficient."""
    n = len(rows)
    if n < min_n:
        raise ValueError(f"Sample count ({n}) is below minimum ({min_n}). Halting execution.")
    logger.info(f"Sample count check passed: {n} >= {min_n}")

def check_zero_variance(rows: List[Dict[str, Any]], cols: List[str]) -> List[str]:
    """Detect and return columns with zero variance."""
    zero_var_cols = []
    for col in cols:
        values = [float(row.get(col, 0)) for row in rows if row.get(col)]
        if len(values) > 0 and len(set(values)) == 1:
            zero_var_cols.append(col)
    return zero_var_cols

def split_and_scale(rows: List[Dict[str, Any]], 
                    target_cols: List[str], 
                    predictor_cols: List[str],
                    train_ratio: float = 0.8) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, Dict[str, Any]]:
    """Split data and scale features (fit on train, transform both)."""
    np.random.seed(get_random_seed())
    
    indices = np.random.permutation(len(rows))
    split_idx = int(len(rows) * train_ratio)
    train_idx = indices[:split_idx]
    test_idx = indices[split_idx:]
    
    train_rows = [rows[i] for i in train_idx]
    test_rows = [rows[i] for i in test_idx]
    
    # Convert to numpy arrays
    X_train = np.array([[float(r[c]) for c in predictor_cols] for r in train_rows])
    y_train = np.array([[float(r[c]) for c in target_cols] for r in train_rows])
    X_test = np.array([[float(r[c]) for c in predictor_cols] for r in test_rows])
    y_test = np.array([[float(r[c]) for c in target_cols] for r in test_rows])
    
    # MinMax Scaling (fit on train)
    X_min = X_train.min(axis=0)
    X_max = X_train.max(axis=0)
    X_range = X_max - X_min
    X_range[X_range == 0] = 1  # Avoid division by zero
    
    X_train_scaled = (X_train - X_min) / X_range
    X_test_scaled = (X_test - X_min) / X_range
    
    bounds = {
        "min": X_min.tolist(),
        "max": X_max.tolist(),
        "range": X_range.tolist()
    }
    
    return X_train_scaled, X_test_scaled, y_train, y_test, bounds

def save_normalization_bounds(bounds: Dict[str, Any], output_path: str):
    """Save normalization bounds to JSON."""
    ensure_directories([os.path.dirname(output_path)])
    with open(output_path, 'w') as f:
        json.dump(bounds, f, indent=2)
    logger.info(f"Normalization bounds saved to {output_path}")

def validate_and_preprocess() -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray, Dict[str, Any]]:
    """
    Full pipeline: Load -> Validate -> Impute -> Encode -> Split -> Scale.
    Returns: X_train, X_test, y_train, y_test, metadata
    """
    logger.info("Starting data validation and preprocessing pipeline.")
    
    # 1. Load
    headers, rows = load_raw_csv()
    
    # 2. Validate Schema
    schema = load_schema()
    required_cols = [c['name'] for c in schema.get('required_columns', [])]
    is_valid, errors = validate_csv_schema(os.path.join(get_raw_data_dir(), "am_data.csv"), schema)
    if not is_valid:
        raise ValueError(f"Schema validation failed: {errors}")
    
    # 3. Check Sample Count
    check_sample_count(rows)
    
    # 4. Detect & Impute Missing Values
    missing_counts = detect_missing_values(rows, required_cols)
    logger.info(f"Missing values detected: {missing_counts}")
    
    numeric_cols = [c['name'] for c in schema.get('required_columns', [])]
    medians = compute_medians(rows, numeric_cols)
    rows = impute_missing_values(rows, medians, numeric_cols)
    logger.info(f"Missing values imputed using median.")
    
    # 5. Encode Categorical
    # Check for alloy_type in optional columns
    optional_cols = [c['name'] for c in schema.get('optional_columns', [])]
    if 'alloy_type' in optional_cols and 'alloy_type' in headers:
        rows, encoded_cols = encode_categorical(rows, 'alloy_type')
        logger.info(f"Encoded categorical column 'alloy_type' into {encoded_cols}")
        # Update predictor list to include encoded cols
        # For now, we assume standard numeric predictors + encoded ones if present
        # We'll dynamically construct predictor list
    else:
        encoded_cols = []
    
    # 6. Define Targets and Predictors
    target_cols = ['yield_strength', 'ductility'] # Based on schema
    # Predictors: laser_power, scan_speed, layer_thickness + encoded cols
    base_predictors = ['laser_power', 'scan_speed', 'layer_thickness']
    predictor_cols = base_predictors + encoded_cols
    
    # 7. Check Zero Variance
    zero_var = check_zero_variance(rows, predictor_cols + target_cols)
    if zero_var:
        logger.warning(f"Dropping zero-variance columns: {zero_var}")
        for col in zero_var:
            if col in predictor_cols:
                predictor_cols.remove(col)
            if col in target_cols:
                target_cols.remove(col)
    
    # 8. Split and Scale
    X_train, X_test, y_train, y_test, bounds = split_and_scale(rows, target_cols, predictor_cols)
    
    # 9. Save Normalization Bounds
    processed_dir = get_processed_data_dir()
    bounds_path = os.path.join(processed_dir, "normalization_bounds.json")
    save_normalization_bounds(bounds, bounds_path)
    
    # 10. Log Stats
    logger.info(f"Preprocessing complete. Train: {X_train.shape}, Test: {X_test.shape}")
    
    metadata = {
        "predictor_cols": predictor_cols,
        "target_cols": target_cols,
        "bounds_path": bounds_path,
        "sample_count": len(rows)
    }
    
    return X_train, X_test, y_train, y_test, metadata

def main():
    """Entry point for preprocessing script."""
    try:
        X_train, X_test, y_train, y_test, metadata = validate_and_preprocess()
        print("Preprocessing completed successfully.")
        print(f"Metadata: {metadata}")
        return 0
    except Exception as e:
        logger.exception(f"Preprocessing failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
