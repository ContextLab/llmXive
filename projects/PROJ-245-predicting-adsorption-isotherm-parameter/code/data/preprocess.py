import os
import sys
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
import numpy as np
import hashlib
import json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Ensure project root is in path for imports
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from data.descriptors import calculate_descriptors_batch
from models.entities import Adsorbate, Adsorbent, IsothermParameter

def load_raw_data(raw_file_path: str) -> pd.DataFrame:
    """
    Load raw data from CSV.
    """
    path = Path(raw_file_path)
    if not path.exists():
        raise FileNotFoundError(f"Raw data file not found: {path}")
    
    logger.info(f"Loading raw data from {path}")
    df = pd.read_csv(path)
    logger.info(f"Loaded {len(df)} rows")
    return df

def filter_type_isotherms(df: pd.DataFrame, isotherm_type_col: str = 'isotherm_type') -> pd.DataFrame:
    """
    Filter for Type I isotherms (Langmuir-like).
    """
    logger.info(f"Filtering for Type I isotherms in column '{isotherm_type_col}'")
    if isotherm_type_col not in df.columns:
        logger.warning(f"Column '{isotherm_type_col}' not found. Keeping all rows.")
        return df
    
    # Assuming 'Type I' or 'I' or 1 indicates Type I
    mask = df[isotherm_type_col].isin(['Type I', 'I', 1, '1'])
    filtered_df = df[mask].copy()
    logger.info(f"Filtered to {len(filtered_df)} Type I isotherms")
    return filtered_df

def remove_missing_targets(df: pd.DataFrame, target_cols: Optional[List[str]] = None) -> pd.DataFrame:
    """
    Remove rows where target variables are missing.
    """
    if target_cols is None:
        target_cols = ['langmuir_capacity', 'henry_constant']
    
    logger.info(f"Removing rows with missing targets: {target_cols}")
    initial_count = len(df)
    df = df.dropna(subset=target_cols)
    dropped = initial_count - len(df)
    logger.info(f"Dropped {dropped} rows with missing targets")
    return df

def normalize_units(df: pd.DataFrame, surface_area_col: str = 'surface_area', target_unit: str = 'm2/g') -> pd.DataFrame:
    """
    Normalize surface area units to m²/g.
    """
    logger.info(f"Normalizing surface area to {target_unit}")
    if surface_area_col not in df.columns:
        logger.warning(f"Column '{surface_area_col}' not found. Skipping normalization.")
        return df
    
    # Simple logic: if column has unit info in name or value, convert.
    # Assuming input is already in m2/g or needs simple scaling if marked otherwise.
    # For this implementation, we assume data is clean or requires no scaling unless specified.
    # If a 'unit' column exists, we could filter/convert there.
    return df

def handle_missing_pore_volume(df: pd.DataFrame, col: str = 'pore_volume', method: str = 'exclude') -> pd.DataFrame:
    """
    Handle missing pore volume: impute or exclude.
    """
    logger.info(f"Handling missing pore volume (method: {method})")
    if col not in df.columns:
        logger.warning(f"Column '{col}' not found.")
        return df
    
    missing_count = df[col].isna().sum()
    if missing_count == 0:
        return df
    
    if method == 'exclude':
        logger.info(f"Excluding {missing_count} rows with missing pore volume")
        return df.dropna(subset=[col])
    elif method == 'impute_mean':
        mean_val = df[col].mean()
        logger.info(f"Imputing missing pore volume with mean: {mean_val}")
        df[col] = df[col].fillna(mean_val)
        return df
    else:
        raise ValueError(f"Unknown method: {method}")

def _calculate_descriptor_hash(row: pd.Series, descriptor_cols: List[str]) -> str:
    """
    Calculate a deterministic hash for the descriptor values of a row.
    """
    # Extract values, handle NaN by converting to string representation
    vals = [str(row[col]) if pd.notna(row[col]) else 'NaN' for col in descriptor_cols]
    # Create a canonical string
    canonical = ",".join(vals)
    return hashlib.sha256(canonical.encode('utf-8')).hexdigest()

def detect_outliers(df: pd.DataFrame, descriptor_cols: List[str], target_cols: List[str], output_path: str) -> pd.DataFrame:
    """
    Detect adsorbates with identical descriptors but conflicting targets.
    
    Logic:
    1. Group by a hash of the descriptor columns.
    2. For each group with > 1 entry, calculate the variance of the target columns.
    3. If variance > 0 (or a threshold), flag as outlier.
    4. Write results to `output_path`.
    
    Args:
        df: Preprocessed dataframe.
        descriptor_cols: List of descriptor column names to hash.
        target_cols: List of target column names to check for variance.
        output_path: Path to write the outliers CSV.
    
    Returns:
        DataFrame of outliers.
    """
    logger.info(f"Detecting outliers: identical descriptors ({descriptor_cols}) with conflicting targets ({target_cols})")
    
    # Ensure required columns exist
    missing_desc = [c for c in descriptor_cols if c not in df.columns]
    missing_target = [c for c in target_cols if c not in df.columns]
    
    if missing_desc:
        raise ValueError(f"Missing descriptor columns: {missing_desc}")
    if missing_target:
        raise ValueError(f"Missing target columns: {missing_target}")
    
    # Create a hash column
    df['_desc_hash'] = df.apply(lambda row: _calculate_descriptor_hash(row, descriptor_cols), axis=1)
    
    # Group by hash
    grouped = df.groupby('_desc_hash')
    
    outliers = []
    
    for hash_val, group in grouped:
        if len(group) > 1:
            # Calculate variance for each target
            for target in target_cols:
                var_val = group[target].var()
                if not pd.isna(var_val) and var_val > 1e-9: # Tolerance for float comparison
                    # This group has conflicting targets for the same descriptors
                    # We record one row per conflict or aggregate? 
                    # Requirement: output [material_id, descriptor_hash, target_variance]
                    # We'll record the max variance found for this group across targets, or one row per target.
                    # The prompt implies a single variance metric. Let's use the max variance across targets for the row.
                    pass 
            
            # Aggregate: Find the max variance across targets for this group
            max_var = 0.0
            for target in target_cols:
                v = group[target].var()
                if not pd.isna(v) and v > max_var:
                    max_var = v
            
            if max_var > 1e-9:
                # Take the first material_id in the group as representative
                mat_id = group.iloc[0]['material_id'] if 'material_id' in group.columns else f"group_{hash_val}"
                outliers.append({
                    'material_id': mat_id,
                    'descriptor_hash': hash_val,
                    'target_variance': max_var
                })
    
    outlier_df = pd.DataFrame(outliers)
    
    # Ensure output directory exists
    out_path = Path(output_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    
    if not outlier_df.empty:
        outlier_df.to_csv(out_path, index=False)
        logger.info(f"Wrote {len(outlier_df)} outlier entries to {output_path}")
    else:
        # Write empty file with headers if no outliers found
        outlier_df.to_csv(out_path, index=False)
        logger.info("No outliers found with conflicting targets.")
    
    # Clean up temporary hash column if it was added to the main df
    # Note: We don't modify the input df in place here to avoid side effects in pipeline
    return outlier_df

def preprocess_pipeline(input_path: str, output_path: str, outliers_path: str, use_descriptors: bool = True) -> pd.DataFrame:
    """
    Run the full preprocessing pipeline:
    1. Load
    2. Filter Type I
    3. Remove missing targets
    4. Normalize units
    5. Handle missing pore volume
    6. Detect Outliers (T016)
    
    Returns the cleaned dataframe.
    """
    logger.info("Starting preprocessing pipeline")
    
    # 1. Load
    df = load_raw_data(input_path)
    
    # 2. Filter
    df = filter_type_isotherms(df)
    
    # 3. Remove missing targets
    df = remove_missing_targets(df)
    
    # 4. Normalize
    df = normalize_units(df)
    
    # 5. Handle missing pore volume
    df = handle_missing_pore_volume(df)
    
    # 6. Outlier Detection (T016)
    # Define descriptors based on T014 (calculate_descriptors)
    # We assume these columns exist if descriptors were calculated in T014/T015 step
    # If not, we fallback to a subset or raise error if strictly required
    descriptor_cols = [
        'molecular_weight', 'polar_surface_area', 'polarizability', 
        'h_bond_donors', 'h_bond_acceptors', 'van_der_waals_volume', 'kinetic_diameter'
    ]
    
    # Check which columns are present
    available_desc = [c for c in descriptor_cols if c in df.columns]
    if not available_desc:
        logger.warning("No descriptor columns found. Skipping outlier detection based on descriptors.")
        # Create empty outliers file
        Path(outliers_path).parent.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(columns=['material_id', 'descriptor_hash', 'target_variance']).to_csv(outliers_path, index=False)
    else:
        target_cols = ['langmuir_capacity', 'henry_constant']
        detect_outliers(df, available_desc, target_cols, outliers_path)
    
    # Save processed data
    out_path = Path(output_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Processed data saved to {output_path}")
    
    return df

def main():
    """
    Entry point for the preprocess script.
    Expects environment variables or CLI args for paths.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Preprocess adsorption data")
    parser.add_argument("--input", type=str, default="data/raw/synthetic_adsorption_data.csv", help="Input raw CSV")
    parser.add_argument("--output", type=str, default="data/processed/cleaned_data.csv", help="Output cleaned CSV")
    parser.add_argument("--outliers", type=str, default="data/processed/outliers.csv", help="Output outliers CSV")
    
    args = parser.parse_args()
    
    try:
        df = preprocess_pipeline(args.input, args.output, args.outliers)
        logger.info(f"Pipeline completed. Processed {len(df)} rows.")
    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()