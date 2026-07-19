import os
import sys
import csv
import json
import logging
import numpy as np
from typing import Dict, Any, Optional, Tuple, List
from pathlib import Path

# Import from project config
from config import get_project_root, get_processed_data_dir, ensure_directories, get_logger
from data.schema_validator import validate_csv_schema, load_schema
from utils.logger import setup_logging

# Constants
REQUIRED_COLUMNS = ['laser_power', 'scan_speed', 'layer_thickness', 'yield_strength', 'ductility']
OPTIONAL_COLUMNS = ['fatigue_life', 'alloy_type']
CATEGORICAL_COLUMNS = ['alloy_type']
NUMERIC_COLUMNS = ['laser_power', 'scan_speed', 'layer_thickness', 'yield_strength', 'ductility', 'fatigue_life']

def load_raw_csv(filepath: str) -> List[Dict[str, Any]]:
    """Load raw CSV file into a list of dictionaries."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Raw data file not found: {filepath}")
    
    data = []
    with open(filepath, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append(row)
    return data

def detect_missing_values(data: List[Dict[str, Any]], columns: List[str]) -> Dict[str, int]:
    """Detect missing values in specified columns."""
    missing_counts = {col: 0 for col in columns}
    for row in data:
        for col in columns:
            if row.get(col) is None or row.get(col) == '' or row.get(col) == 'NA':
                missing_counts[col] += 1
    return missing_counts

def compute_medians(data: List[Dict[str, Any]], columns: List[str]) -> Dict[str, float]:
    """Compute median values for numeric columns."""
    medians = {}
    for col in columns:
        values = []
        for row in data:
            val = row.get(col)
            if val is not None and val != '' and val != 'NA':
                try:
                    values.append(float(val))
                except ValueError:
                    pass
        if values:
            medians[col] = float(np.median(values))
        else:
            medians[col] = 0.0
    return medians

def impute_missing_values(data: List[Dict[str, Any]], medians: Dict[str, float], columns: List[str]) -> List[Dict[str, Any]]:
    """Impute missing values using median imputation."""
    imputed_data = []
    for row in data:
        new_row = row.copy()
        for col in columns:
            val = new_row.get(col)
            if val is None or val == '' or val == 'NA':
                new_row[col] = medians.get(col, 0.0)
            else:
                try:
                    new_row[col] = float(val)
                except ValueError:
                    new_row[col] = float(val) if val != 'NA' else medians.get(col, 0.0)
        imputed_data.append(new_row)
    return imputed_data

def encode_categorical(data: List[Dict[str, Any]], column: str) -> Tuple[List[Dict[str, Any]], List[str]]:
    """One-hot encode a categorical column."""
    if not any(column in row for row in data):
        return data, []
    
    unique_values = sorted(set(row.get(column, '') for row in data if row.get(column)))
    encoded_data = []
    
    for row in data:
        new_row = {k: v for k, v in row.items() if k != column}
        for val in unique_values:
            new_row[f"{column}_{val}"] = 1.0 if row.get(column) == val else 0.0
        encoded_data.append(new_row)
    
    return encoded_data, [f"{column}_{val}" for val in unique_values]

def check_sample_count(data: List[Dict[str, Any]], min_samples: int = 50) -> None:
    """Check if sample count meets minimum requirement."""
    if len(data) < min_samples:
        raise ValueError(f"Sample count ({len(data)}) is below minimum required ({min_samples})")

def check_zero_variance(data: List[Dict[str, Any]], columns: List[str], logger: logging.Logger) -> List[str]:
    """Detect and drop zero-variance columns."""
    dropped_columns = []
    for col in columns:
        values = [row.get(col) for row in data if col in row]
        if not values:
            continue
        
        try:
            numeric_values = [float(v) for v in values if v is not None and v != '']
            if len(set(numeric_values)) <= 1:
                logger.warning(f"Column '{col}' has zero variance; dropping to prevent singularity")
                dropped_columns.append(col)
        except ValueError:
            continue
    
    return dropped_columns

def split_and_scale(data: List[Dict[str, Any]], train_ratio: float = 0.8, random_seed: int = 42) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Dict[str, float]]]:
    """Split data into train/test sets and apply MinMax scaling."""
    np.random.seed(random_seed)
    indices = np.random.permutation(len(data))
    split_idx = int(len(data) * train_ratio)
    
    train_indices = indices[:split_idx]
    test_indices = indices[split_idx:]
    
    train_data = [data[i] for i in train_indices]
    test_data = [data[i] for i in test_indices]
    
    # Compute min/max for normalization bounds
    numeric_cols = [k for k in data[0].keys() if isinstance(data[0][k], (int, float))]
    normalization_bounds = {}
    
    for col in numeric_cols:
        train_values = [row.get(col, 0) for row in train_data]
        min_val = min(train_values)
        max_val = max(train_values)
        normalization_bounds[col] = {'min': float(min_val), 'max': float(max_val)}
        
        # Apply MinMax scaling to train and test
        for row in train_data:
            if max_val > min_val:
                row[col] = (row.get(col, 0) - min_val) / (max_val - min_val)
            else:
                row[col] = 0.0
        
        for row in test_data:
            if max_val > min_val:
                row[col] = (row.get(col, 0) - min_val) / (max_val - min_val)
            else:
                row[col] = 0.0
    
    return train_data, test_data, normalization_bounds

def save_normalization_bounds(bounds: Dict[str, Dict[str, float]], output_path: str) -> None:
    """Save normalization bounds to JSON file."""
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(bounds, f, indent=2)

def validate_and_preprocess(raw_csv_path: str, schema_path: str, processed_dir: str, logger: logging.Logger) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Main preprocessing pipeline."""
    # Validate schema
    validate_csv_schema(raw_csv_path, schema_path, logger)
    
    # Load raw data
    data = load_raw_csv(raw_csv_path)
    
    # Check sample count
    check_sample_count(data)
    
    # Detect missing values
    missing_counts = detect_missing_values(data, REQUIRED_COLUMNS)
    total_missing = sum(missing_counts.values())
    logger.info(f"Detected {total_missing} missing values in required columns")
    
    # Compute medians
    medians = compute_medians(data, REQUIRED_COLUMNS)
    
    # Impute missing values
    data = impute_missing_values(data, medians, REQUIRED_COLUMNS)
    
    # Encode categorical variables
    encoded_data, encoded_cols = encode_categorical(data, 'alloy_type')
    if encoded_cols:
        logger.info(f"One-hot encoded 'alloy_type' into {len(encoded_cols)} columns")
    
    # Check zero variance
    all_cols = list(encoded_data[0].keys())
    dropped_cols = check_zero_variance(encoded_data, all_cols, logger)
    if dropped_cols:
        logger.warning(f"Dropped {len(dropped_cols)} zero-variance columns: {dropped_cols}")
    
    # Split and scale
    train_data, test_data, normalization_bounds = split_and_scale(encoded_data)
    
    # Save normalization bounds
    bounds_path = os.path.join(processed_dir, 'normalization_bounds.json')
    save_normalization_bounds(normalization_bounds, bounds_path)
    logger.info(f"Saved normalization bounds to {bounds_path}")
    
    return train_data, test_data

def main():
    """Entry point for preprocessing script."""
    logger = setup_logging()
    logger.info("Starting preprocessing pipeline")
    
    project_root = get_project_root()
    raw_data_path = os.path.join(project_root, 'data', 'raw', 'am_data.csv')
    schema_path = os.path.join(project_root, 'contracts', 'dataset.schema.yaml')
    processed_dir = get_processed_data_dir()
    ensure_directories()
    
    try:
        train_data, test_data = validate_and_preprocess(raw_data_path, schema_path, processed_dir, logger)
        logger.info(f"Preprocessing complete. Train size: {len(train_data)}, Test size: {len(test_data)}")
    except Exception as e:
        logger.error(f"Preprocessing failed: {str(e)}")
        sys.exit(1)

if __name__ == '__main__':
    main()
