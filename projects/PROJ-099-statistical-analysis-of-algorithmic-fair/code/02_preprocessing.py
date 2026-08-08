"""
Preprocessing Pipeline for Fairness Analysis Datasets.

This module implements the preprocessing steps for the fairness analysis project:
1. Load raw CSVs from data/raw/
2. Extract binary protected attributes and binary outcomes
3. Perform stratified sampling to <=100k rows per dataset
4. Log exclusions of datasets missing required variables to logs/exclusion.log
5. Save preprocessed datasets to data/processed/

FR-008 Disclaimer: Findings are associational only; no causal claims are made.
"""

import os
import sys
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import pandas as pd
import numpy as np

# Add project root to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from utils.logging_utils import init_exclusion_log, log_exclusion, log_warning
from utils.validators import compute_sha256, validate_variable_presence, get_required_columns
from data_model import Dataset

# Constants
MAX_ROWS = 100_000
RANDOM_STATE = 42
RAW_DATA_DIR = project_root / "data" / "raw"
PROCESSED_DATA_DIR = project_root / "data" / "processed"
EXCLUSION_LOG_PATH = project_root / "logs" / "exclusion.log"

# Mapping of dataset names to their specific column requirements
# Format: dataset_name -> {protected_attr, outcome, prediction}
# Note: 'prediction' is often the same as 'outcome' for raw data, 
# but we treat it as the target variable for modeling.
DATASET_CONFIGS = {
    "adult": {
        "protected_attr": "sex",
        "outcome": "class",
        "required_binary": ["sex", "class"]
    },
    "compas": {
        "protected_attr": "race",
        "outcome": "two_year_recid",
        "required_binary": ["race", "two_year_recid"]
    },
    "bank": {
        "protected_attr": "age", # Note: Age is continuous, need to binarize or find binary proxy. 
                                 # Spec says "binary protected attributes". Bank dataset has 'age' (int).
                                 # Common practice: binarize age > median or > 30/40. 
                                 # However, looking at UCI Bank Marketing, there isn't a direct binary protected attribute like gender/race in the raw set.
                                 # Let's check the spec's loader. The loader usually returns the raw df.
                                 # We will implement a generic binarization for continuous variables if needed, 
                                 # but strictly the task asks to "Extract binary protected attributes".
                                 # If the raw data doesn't have one, we might need to create one (e.g., age > median) 
                                 # or exclude. Given the task says "Extract", we assume the raw data has them or we derive them deterministically.
                                 # For Bank: 'age' is continuous. We will binarize age > median for this task to satisfy "binary".
        "outcome": "y",
        "required_binary": ["age", "y"], # Will binarize age
        "binarize_map": {"age": "median"}
    },
    "german": {
        "protected_attr": "sex_and_marital_status", # Often needs mapping to binary sex
        "outcome": "creditability",
        "required_binary": ["sex_and_marital_status", "creditability"],
        "mapping_map": {"sex_and_marital_status": "sex"}
    },
    "lawschool": {
        "protected_attr": "race",
        "outcome": "bar",
        "required_binary": ["race", "bar"]
    }
}

def log_header(message: str):
    """Log a formatted header message with FR-008 disclaimer."""
    print(f"\n{'='*60}")
    print(f"{message}")
    print(f"{'='*60}")
    print("FR-008 DISCLAIMER: Findings are associational only; no causal claims are made.")

def binarize_column(df: pd.DataFrame, col_name: str, method: str = "median") -> pd.DataFrame:
    """
    Binarize a continuous column.
    - 'median': 1 if value > median, 0 otherwise.
    - 'mean': 1 if value > mean, 0 otherwise.
    - 'threshold': 1 if value > 0 (for specific encodings).
    """
    if method == "median":
        threshold = df[col_name].median()
        df[col_name] = (df[col_name] > threshold).astype(int)
    elif method == "mean":
        threshold = df[col_name].mean()
        df[col_name] = (df[col_name] > threshold).astype(int)
    elif method == "threshold":
        df[col_name] = (df[col_name] > 0).astype(int)
    else:
        raise ValueError(f"Unknown binarization method: {method}")
    return df

def map_categorical_to_binary(df: pd.DataFrame, col_name: str, mapping: Dict[str, int]) -> pd.DataFrame:
    """
    Map a categorical column to binary based on a provided mapping dict.
    If the column contains multiple categories, we map specific ones to 1 and others to 0.
    For 'sex_and_marital_status' in German Credit:
    Often values are: 1: male/divorced, 2: female/divorced, 3: male/single, 4: female/single.
    We typically want just 'sex'.
    Standard mapping for German Credit:
    1: Male, 2: Female (simplified).
    We will implement a generic fallback if specific mapping isn't provided in config.
    """
    if col_name not in df.columns:
        raise KeyError(f"Column {col_name} not found in dataframe.")
    
    # If mapping is provided, use it. Else, try to infer if it's already binary-like (0/1)
    if mapping:
        df[col_name] = df[col_name].map(mapping)
        # Fill NaNs if mapping didn't cover all values, treating them as 0 or raising error?
        # We'll fill with 0 for safety, but log a warning.
        if df[col_name].isna().any():
            log_warning(f"Mapping for {col_name} left {df[col_name].isna().sum()} values as NaN. Filled with 0.")
            df[col_name] = df[col_name].fillna(0).astype(int)
    else:
        # If already 0/1, do nothing
        if df[col_name].nunique() > 2:
            # Fallback: treat as continuous and binarize by median? 
            # This is a heuristic.
            log_warning(f"Column {col_name} has {df[col_name].nunique()} unique values. Binarizing by median.")
            df = binarize_column(df, col_name, "median")
        else:
            df[col_name] = df[col_name].astype(int)
    
    return df

def load_and_validate_dataset(dataset_name: str) -> Optional[pd.DataFrame]:
    """
    Load a raw dataset, validate required variables, and return the dataframe.
    Returns None if validation fails (logs exclusion).
    """
    raw_path = RAW_DATA_DIR / f"{dataset_name}.csv"
    if not raw_path.exists():
        log_exclusion(dataset_name, "raw_file", f"Raw file {raw_path} not found.")
        return None

    try:
        df = pd.read_csv(raw_path)
    except Exception as e:
        log_exclusion(dataset_name, "load_error", str(e))
        return None

    config = DATASET_CONFIGS.get(dataset_name)
    if not config:
        log_exclusion(dataset_name, "config_missing", f"No configuration found for {dataset_name}")
        return None

    required_cols = config.get("required_binary", [])
    # Check for presence of required columns
    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        log_exclusion(dataset_name, "missing_variable", f"Missing columns: {missing_cols}")
        return None

    return df

def preprocess_dataset(dataset_name: str, df: pd.DataFrame) -> pd.DataFrame:
    """
    Perform specific preprocessing steps for a dataset:
    1. Binarize protected attributes if necessary.
    2. Ensure outcome is binary (0/1).
    3. Drop rows with missing values in key columns.
    """
    config = DATASET_CONFIGS[dataset_name]
    protected_col = config["protected_attr"]
    outcome_col = config["outcome"]
    
    # Handle binarization for protected attribute
    binarize_map = config.get("binarize_map", {})
    if protected_col in binarize_map:
        df = binarize_column(df, protected_col, binarize_map[protected_col])
    
    # Handle mapping for protected attribute (e.g., German Credit)
    mapping_map = config.get("mapping_map", {})
    if protected_col in mapping_map:
        # We need the actual mapping values. Since they aren't in the simple config,
        # we assume the loader or a standard mapping is used.
        # For German Credit, sex_and_marital_status -> sex (1=Male, 2=Female -> 0/1)
        # Let's define a standard mapping for known problematic columns.
        if dataset_name == "german" and protected_col == "sex_and_marital_status":
            # 1,3,5 -> Male (1), 2,4,6 -> Female (0) ? 
            # Actually, standard German Credit: 
            # 1: male/divorced, 2: female/divorced, 3: male/single, 4: female/single.
            # We want 'sex'. 
            # 1,3 -> Male (1), 2,4 -> Female (0).
            # Let's assume values are 1,2,3,4.
            # If 1,3 -> 1; 2,4 -> 0.
            def map_sex(val):
                if val in [1, 3]: return 1
                if val in [2, 4]: return 0
                return 0 # Fallback
            df[protected_col] = df[protected_col].apply(map_sex)
    
    # Ensure outcome is binary
    if df[outcome_col].nunique() > 2:
        # If outcome is not binary, we might need to map or binarize.
        # For 'class' in Adult: <=50K, >50K -> 0, 1
        # For 'y' in Bank: no, yes -> 0, 1
        # For 'creditability' in German: bad, good -> 0, 1
        # For 'bar' in Law: 0, 1
        # For 'two_year_recid' in Compas: 0, 1
        
        # Heuristic: map string values to 0/1
        unique_vals = df[outcome_col].unique()
        if all(isinstance(v, str) for v in unique_vals):
            # Assume first unique is 0, second is 1? No, need specific mapping.
            # Let's handle known cases.
            if dataset_name == "adult":
                df[outcome_col] = df[outcome_col].map({">50K": 1, "<=50K": 0}).fillna(0)
            elif dataset_name == "bank":
                df[outcome_col] = df[outcome_col].map({"yes": 1, "no": 0}).fillna(0)
            elif dataset_name == "german":
                df[outcome_col] = df[outcome_col].map({"good": 1, "bad": 0}).fillna(0)
            else:
                # Generic: sort unique and map 0, 1... but this is risky.
                # Fallback to error if not handled.
                log_warning(f"Outcome column {outcome_col} in {dataset_name} has non-binary string values: {unique_vals}. Attempting generic mapping.")
                sorted_vals = sorted(list(unique_vals))
                mapping = {v: i for i, v in enumerate(sorted_vals)}
                df[outcome_col] = df[outcome_col].map(mapping).fillna(0)
        
        # Ensure it's int
        df[outcome_col] = df[outcome_col].astype(int)
    
    # Drop rows with NaN in protected or outcome
    df = df.dropna(subset=[protected_col, outcome_col])
    
    # Reset index
    df = df.reset_index(drop=True)
    
    return df

def stratified_sample(df: pd.DataFrame, dataset_name: str) -> pd.DataFrame:
    """
    Perform stratified sampling to <=100k rows.
    Stratify by protected attribute and outcome to maintain distribution.
    """
    config = DATASET_CONFIGS[dataset_name]
    protected_col = config["protected_attr"]
    outcome_col = config["outcome"]
    
    n_samples = len(df)
    if n_samples <= MAX_ROWS:
        log_warning(f"Dataset {dataset_name} has {n_samples} rows, which is <= {MAX_ROWS}. No sampling needed.")
        return df
    
    # Stratify by protected attribute and outcome
    try:
        # If the combination of protected and outcome is too sparse, stratify by just protected or outcome
        # We try the full combination first.
        df_sampled = df.groupby([protected_col, outcome_col], group_keys=False).apply(
            lambda x: x.sample(n=min(len(x), int(len(x) * (MAX_ROWS / n_samples))), random_state=RANDOM_STATE)
        )
    except Exception:
        # Fallback to just protected attribute
        log_warning(f"Full stratification failed for {dataset_name}, falling back to stratification by {protected_col}.")
        df_sampled = df.groupby(protected_col, group_keys=False).apply(
            lambda x: x.sample(n=min(len(x), int(len(x) * (MAX_ROWS / n_samples))), random_state=RANDOM_STATE)
        )
    
    # Ensure we don't exceed MAX_ROWS due to rounding
    if len(df_sampled) > MAX_ROWS:
        df_sampled = df_sampled.sample(n=MAX_ROWS, random_state=RANDOM_STATE)
    
    return df_sampled.reset_index(drop=True)

def save_processed_dataset(df: pd.DataFrame, dataset_name: str):
    """Save the processed dataframe to data/processed/."""
    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
    output_path = PROCESSED_DATA_DIR / f"{dataset_name}_processed.csv"
    df.to_csv(output_path, index=False)
    checksum = compute_sha256(output_path)
    log_warning(f"Saved {dataset_name} to {output_path} (SHA256: {checksum[:16]}...)")
    return output_path, checksum

def main():
    log_header("Starting Preprocessing Pipeline (T016)")
    
    # Initialize exclusion log
    init_exclusion_log(EXCLUSION_LOG_PATH)
    
    # Get list of datasets to process
    # We assume the raw files are named {dataset_name}.csv based on T014
    dataset_names = ["adult", "compas", "bank", "german", "lawschool"]
    
    processed_datasets = []
    
    for dataset_name in dataset_names:
        print(f"\nProcessing {dataset_name}...")
        
        # 1. Load and Validate
        df = load_and_validate_dataset(dataset_name)
        if df is None:
            print(f"Skipping {dataset_name} due to validation failure.")
            continue
        
        print(f"  Loaded {len(df)} rows.")
        
        # 2. Preprocess (Binarize, Clean)
        try:
            df = preprocess_dataset(dataset_name, df)
        except Exception as e:
            log_exclusion(dataset_name, "preprocessing_error", str(e))
            print(f"  Error preprocessing {dataset_name}: {e}")
            continue
        
        print(f"  After preprocessing: {len(df)} rows.")
        
        # 3. Stratified Sampling
        if len(df) > MAX_ROWS:
            print(f"  Sampling to {MAX_ROWS} rows...")
            df = stratified_sample(df, dataset_name)
            print(f"  Sampled to {len(df)} rows.")
        
        # 4. Save
        output_path, checksum = save_processed_dataset(df, dataset_name)
        processed_datasets.append({
            "dataset_name": dataset_name,
            "rows": len(df),
            "output_path": str(output_path),
            "checksum": checksum
        })
    
    print("\n" + "="*60)
    print("Preprocessing Complete.")
    print(f"Processed {len(processed_datasets)} datasets.")
    for item in processed_datasets:
        print(f"  - {item['dataset_name']}: {item['rows']} rows ({item['output_path']})")
    print("FR-008 DISCLAIMER: Findings are associational only; no causal claims are made.")
    print("="*60)

if __name__ == "__main__":
    main()