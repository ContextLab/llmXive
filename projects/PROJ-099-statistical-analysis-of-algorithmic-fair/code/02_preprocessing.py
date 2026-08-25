"""
Preprocessing Module for PROJ-099.
Loads raw datasets, binarizes attributes, performs stratified sampling, and logs exclusions.
"""
import os
import sys
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import pandas as pd
import numpy as np

# Add parent to path for imports if running as script
if str(Path(__file__).parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).parent))

from utils.logging_utils import log_exclusion, log_warning, init_exclusion_log
from utils.validators import validate_variable_presence, get_required_columns
from data_model import DatasetCharacteristic

# FR-008 Disclaimer Constant
FR008_DISCLAIMER = "Findings are associational only; no causal claims are made."

def log_header(message: str):
    """
    Logs a formatted header message to stdout and stderr with the FR-008 disclaimer.
    
    Args:
        message: The main message to log.
    """
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    output = f"[{timestamp}] {message}\n{FR008_DISCLAIMER}"
    print(output)
    sys.stderr.write(output + "\n")

def binarize_column(df: pd.DataFrame, column: str, mapping: Dict[Any, int]) -> pd.DataFrame:
    """
    Binarizes a column using a provided mapping.
    
    Args:
        df: Input DataFrame.
        column: Column name to binarize.
        mapping: Dict mapping original values to binary (0/1).
        
    Returns:
        DataFrame with the new binary column.
    """
    new_col_name = f"{column}_binary"
    df[new_col_name] = df[column].map(mapping)
    return df

def map_categorical_to_binary(df: pd.DataFrame, dataset_id: str) -> pd.DataFrame:
    """
    Maps categorical protected attributes and outcomes to binary 0/1.
    Logic depends on dataset_id.
    """
    # Default mappings based on standard dataset definitions
    mappings = {
        'adult': {'gender': {'Male': 1, 'Female': 0}, 'outcome': {'>50K': 1, '<=50K': 0}},
        'compas': {'race': {'White': 1, 'Black': 0}, 'outcome': {'Recid': 1, 'No Recid': 0}},
        'bank': {'age_group': {'young': 0, 'old': 1}, 'outcome': {'yes': 1, 'no': 0}},
        'german': {'sex': {'male': 1, 'female': 0}, 'outcome': {'good': 1, 'bad': 0}},
        'lawschool': {'race': {'White': 1, 'Non-White': 0}, 'outcome': {'pass': 1, 'fail': 0}}
    }
    
    if dataset_id not in mappings:
        log_warning(f"No mapping defined for {dataset_id}, skipping binarization.")
        return df

    dataset_maps = mappings[dataset_id]
    for col, map_dict in dataset_maps.items():
        if col in df.columns:
            df = binarize_column(df, col, map_dict)
        else:
            log_warning(f"Column {col} not found in {dataset_id} for binarization.")
    
    return df

def load_and_validate_dataset(raw_path: Path, dataset_id: str) -> Optional[pd.DataFrame]:
    """
    Loads a CSV and validates required variables.
    Logs exclusion if validation fails.
    """
    log_header(f"Loading dataset: {dataset_id} from {raw_path}")
    try:
        df = pd.read_csv(raw_path)
    except Exception as e:
        log_header(f"ERROR: Failed to load {dataset_id}: {e}")
        log_exclusion(dataset_id, "file_load_error", str(e))
        return None

    required_cols = get_required_columns()
    # Check for generic presence; specific columns depend on dataset
    if not validate_variable_presence(df, required_cols):
        log_header(f"ERROR: {dataset_id} missing required variables.")
        log_exclusion(dataset_id, "missing_variables", f"Required: {required_cols}")
        return None

    log_header(f"Loaded {dataset_id} with {len(df)} rows.")
    return df

def stratified_sample(df: pd.DataFrame, target_col: str, max_rows: int = 100000, random_state: int = 42) -> pd.DataFrame:
    """
    Performs stratified sampling to ensure <= max_rows while preserving distribution.
    Uses random_state=42 as per T015.
    """
    if len(df) <= max_rows:
        return df

    # Ensure target_col exists
    if target_col not in df.columns:
        log_warning(f"Target column {target_col} not found for stratification. Returning full sample.")
        return df.sample(n=max_rows, random_state=random_state)

    # Calculate sample size per group
    group_counts = df[target_col].value_counts()
    sample_sizes = {}
    
    for group, count in group_counts.items():
        proportion = count / len(df)
        n_samples = int(proportion * max_rows)
        # Ensure at least 1 sample if possible, or proportional
        if n_samples == 0 and count > 0:
            n_samples = 1
        sample_sizes[group] = n_samples
    
    # Adjust if sum exceeds max_rows due to rounding
    total_samples = sum(sample_sizes.values())
    if total_samples > max_rows:
        # Reduce largest group
        max_group = max(sample_sizes, key=sample_sizes.get)
        sample_sizes[max_group] -= (total_samples - max_rows)

    try:
        sampled_df = df.groupby(target_col, group_keys=False).apply(
            lambda x: x.sample(n=min(sample_sizes[x[target_col].iloc[0]], len(x)), random_state=random_state)
        )
        return sampled_df
    except Exception as e:
        log_warning(f"Stratified sampling failed: {e}. Falling back to random sample.")
        return df.sample(n=max_rows, random_state=random_state)

def preprocess_dataset(df: pd.DataFrame, dataset_id: str) -> pd.DataFrame:
    """
    Main preprocessing logic: binarize and sample.
    """
    log_header(f"Preprocessing {dataset_id}")
    
    # Binarize
    df = map_categorical_to_binary(df, dataset_id)
    
    # Determine outcome column for stratification (heuristic)
    outcome_col = None
    for col in df.columns:
        if 'binary' in col and 'outcome' in col.lower():
            outcome_col = col
            break
        elif 'outcome' in col.lower():
            outcome_col = col
            break
    
    if not outcome_col:
        # Fallback: find a column with low cardinality that looks like a target
        for col in df.columns:
            if df[col].nunique() == 2:
                outcome_col = col
                break

    if outcome_col:
        log_header(f"Stratifying on {outcome_col}")
        df = stratified_sample(df, outcome_col, max_rows=100000, random_state=42)
    else:
        log_warning("No suitable outcome column found for stratification.")

    log_header(f"Preprocessing complete for {dataset_id}. Rows: {len(df)}")
    return df

def save_processed_dataset(df: pd.DataFrame, dataset_id: str, processed_dir: Path):
    """
    Saves the processed DataFrame to CSV.
    """
    output_path = processed_dir / f"{dataset_id}_processed.csv"
    df.to_csv(output_path, index=False)
    log_header(f"Saved processed dataset to {output_path}")

def main():
    """
    Main entry point for preprocessing.
    """
    log_header("=== Starting Preprocessing Pipeline ===")
    log_header(FR008_DISCLAIMER)
    
    raw_dir = Path("data/raw")
    processed_dir = Path("data/processed")
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    # Initialize exclusion log
    init_exclusion_log("logs/exclusion.log")

    datasets = ['adult', 'compas', 'bank', 'german', 'lawschool']
    
    for ds_id in datasets:
        raw_file = raw_dir / f"{ds_id}.csv"
        if not raw_file.exists():
            log_warning(f"Raw file {raw_file} not found. Skipping {ds_id}.")
            continue

        df = load_and_validate_dataset(raw_file, ds_id)
        if df is None:
            continue

        df = preprocess_dataset(df, ds_id)
        save_processed_dataset(df, ds_id, processed_dir)

    log_header("=== Preprocessing Pipeline Complete ===")
    log_header(FR008_DISCLAIMER)

if __name__ == "__main__":
    import time
    main()
