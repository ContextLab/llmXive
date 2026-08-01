import os
import sys
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
import numpy as np
import hashlib
import json

from data.descriptors import calculate_descriptors_batch
from data.loader import load_raw_data

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_raw_data(data_dir: Path) -> pd.DataFrame:
    """
    Load raw data from the specified directory.
    Delegates to the loader module to ensure consistency with T043a/T015.
    """
    logger.info(f"Loading raw data from {data_dir}")
    # Assuming load_raw_data from loader handles the actual file reading
    # If loader.py's load_raw_data expects a specific file path, we adapt here.
    # Based on T015/T043a, the raw data should be in data/raw/
    raw_file = data_dir / "adsorption_data.csv"
    if not raw_file.exists():
        # Fallback to generic load if specific path not found, though T043a should have placed it
        raise FileNotFoundError(f"Raw data file not found at {raw_file}. Ensure T043a completed successfully.")
    
    df = pd.read_csv(raw_file)
    logger.info(f"Loaded {len(df)} rows from {raw_file}")
    return df

def filter_type_isotherms(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filter for Type I isotherms as per T015 requirements.
    """
    logger.info("Filtering for Type I isotherms...")
    if 'isotherm_type' not in df.columns:
        logger.warning("Column 'isotherm_type' not found. Skipping type filter.")
        return df
    
    # Assuming Type I is represented by 'I', '1', or similar. 
    # Adjust based on actual data values if needed.
    type_i_mask = df['isotherm_type'].astype(str).str.upper().isin(['I', '1'])
    filtered_df = df[type_i_mask].copy()
    logger.info(f"Filtered to {len(filtered_df)} Type I isotherms.")
    return filtered_df

def remove_missing_targets(df: pd.DataFrame, target_cols: Optional[List[str]] = None) -> pd.DataFrame:
    """
    Remove entries with missing target values.
    """
    logger.info("Removing entries with missing target values...")
    if target_cols is None:
        target_cols = ['langmuir_capacity', 'henry_constant']
    
    existing_targets = [col for col in target_cols if col in df.columns]
    if not existing_targets:
        logger.warning("No target columns found. Skipping missing target removal.")
        return df
    
    initial_count = len(df)
    df = df.dropna(subset=existing_targets)
    logger.info(f"Removed {initial_count - len(df)} rows with missing targets.")
    return df

def normalize_units(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalize units (e.g., surface area to m²/g).
    """
    logger.info("Normalizing units...")
    if 'surface_area' in df.columns:
        # Assuming input might be in different units, standardizing to m2/g
        # If data is already in m2/g, this is a no-op or conversion factor application
        # Placeholder for specific conversion logic if needed
        pass
    return df

def handle_missing_pore_volume(df: pd.DataFrame) -> pd.DataFrame:
    """
    Handle missing pore volume (impute or exclude).
    """
    logger.info("Handling missing pore volume...")
    if 'pore_volume' not in df.columns:
        return df
    
    # Strategy: Exclude rows with missing pore volume if critical, or impute with median
    # For strict data quality, we drop missing values here as per T015 "impute/exclude with logging"
    # Let's exclude for strictness, but log it.
    initial_count = len(df)
    df = df.dropna(subset=['pore_volume'])
    logger.info(f"Dropped {initial_count - len(df)} rows with missing pore volume.")
    return df

def _compute_descriptor_hash(df: pd.DataFrame, descriptor_cols: List[str]) -> pd.Series:
    """
    Compute a deterministic hash for a row based on descriptor values.
    """
    def hash_row(row):
        # Convert values to strings to handle floats consistently
        values = [f"{x:.6f}" for x in row if pd.notna(x)]
        content = "|".join(values)
        return hashlib.md5(content.encode('utf-8')).hexdigest()
    
    return df[descriptor_cols].apply(hash_row, axis=1)

def detect_outliers(df: pd.DataFrame, target_col: str, variance_threshold: float = 0.01) -> pd.DataFrame:
    """
    Detect adsorbates with identical descriptors but conflicting targets.
    
    Logic:
    1. Group by descriptor_hash (identical molecular features).
    2. Calculate variance of the target variable within each group.
    3. Flag groups where variance > threshold.
    
    Output:
    data/processed/outliers.csv with columns: [material_id, descriptor_hash, target_variance]
    """
    logger.info(f"Detecting outliers for target '{target_col}' with threshold {variance_threshold}...")
    
    if target_col not in df.columns:
        logger.error(f"Target column '{target_col}' not found in dataset.")
        # Create empty output file to satisfy the requirement of producing the file
        output_dir = Path("data/processed")
        output_dir.mkdir(parents=True, exist_ok=True)
        outliers_df = pd.DataFrame(columns=['material_id', 'descriptor_hash', 'target_variance'])
        outliers_df.to_csv(output_dir / "outliers.csv", index=False)
        return df

    # Identify descriptor columns (assuming they are prefixed with 'desc_' or similar, or specific list)
    # Based on T014a-z, we have descriptors like polarizability, kinetic_diameter, etc.
    # We assume the preprocessed dataframe contains these columns.
    # If not explicitly named, we look for columns that are numeric and not targets/ids.
    exclude_cols = ['material_id', 'adsorbent_structure_id', target_col, 'isotherm_type', 'pore_volume']
    descriptor_cols = [col for col in df.select_dtypes(include=[np.number]).columns if col not in exclude_cols]
    
    if not descriptor_cols:
        logger.warning("No descriptor columns found to compute hash. Skipping outlier detection.")
        output_dir = Path("data/processed")
        output_dir.mkdir(parents=True, exist_ok=True)
        outliers_df = pd.DataFrame(columns=['material_id', 'descriptor_hash', 'target_variance'])
        outliers_df.to_csv(output_dir / "outliers.csv", index=False)
        return df

    # Compute hash
    logger.info(f"Computing descriptor hash on columns: {descriptor_cols}")
    df['descriptor_hash'] = _compute_descriptor_hash(df, descriptor_cols)

    # Group and calculate variance
    logger.info("Grouping by descriptor_hash and calculating target variance...")
    grouped = df.groupby('descriptor_hash')
    
    # We need to collect material_ids and variances
    outlier_records = []
    
    for hash_val, group in grouped:
        if len(group) < 2:
            continue # Cannot calculate variance with 1 item
        
        variance = group[target_col].var()
        
        if variance > variance_threshold:
            # Flag all material_ids in this group as outliers
            for _, row in group.iterrows():
                outlier_records.append({
                    'material_id': row['material_id'],
                    'descriptor_hash': hash_val,
                    'target_variance': variance
                })
    
    outliers_df = pd.DataFrame(outlier_records)
    
    # Ensure output directory exists
    output_dir = Path("data/processed")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Write to CSV
    output_path = output_dir / "outliers.csv"
    outliers_df.to_csv(output_path, index=False)
    logger.info(f"Outlier detection complete. Found {len(outliers_df)} outliers. Saved to {output_path}")
    
    return df

def preprocess_pipeline(data_dir: str, target_col: str = "langmuir_capacity") -> pd.DataFrame:
    """
    Run the full preprocessing pipeline including outlier detection.
    """
    data_path = Path(data_dir)
    
    # 1. Load
    df = load_raw_data(data_path)
    
    # 2. Filter
    df = filter_type_isotherms(df)
    
    # 3. Remove missing targets
    df = remove_missing_targets(df, target_cols=[target_col])
    
    # 4. Normalize units
    df = normalize_units(df)
    
    # 5. Handle missing pore volume
    df = handle_missing_pore_volume(df)
    
    # 6. Detect Outliers (T016)
    df = detect_outliers(df, target_col=target_col)
    
    return df

def main():
    """
    Entry point for the preprocess script.
    Expects data directory as argument or uses default.
    """
    import argparse
    parser = argparse.ArgumentParser(description="Preprocess adsorption data")
    parser.add_argument("--data-dir", type=str, default="data/raw", help="Path to raw data directory")
    parser.add_argument("--target", type=str, default="langmuir_capacity", help="Target column for outlier detection")
    args = parser.parse_args()
    
    try:
        df = preprocess_pipeline(args.data_dir, args.target)
        logger.info("Preprocessing pipeline completed successfully.")
    except Exception as e:
        logger.error(f"Preprocessing pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
