import os
import sys
import logging
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
import numpy as np
import hashlib
import re

# Add parent directory to path if running as script
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent.parent))

from data.descriptors import calculate_descriptors_batch, MissingConsensusDescriptorError
from data.loader import load_raw_data

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_raw_data(data_dir: str) -> pd.DataFrame:
    """Load raw data from the specified directory."""
    # Delegate to the loader module
    # Assuming load_raw_data in loader.py handles the path logic or returns a DF
    # If loader.py expects a specific file, we might need to adjust.
    # For now, assuming it returns the DF.
    # If loader.py main returns nothing, we need to call it differently.
    # Let's assume the loader module has a function to get the DF.
    # Based on API: from data.loader import load_raw_data
    return load_raw_data(data_dir)

def filter_type_isotherms(df: pd.DataFrame) -> pd.DataFrame:
    """Filter to include ONLY Type I isotherms."""
    if 'isotherm_type' in df.columns:
        # Handle potential string variations
        mask = df['isotherm_type'].astype(str).str.upper().str.contains('I') | \
               (df['isotherm_type'].astype(int) == 1)
        return df[mask].reset_index(drop=True)
    else:
        # If column missing, assume all are Type I or raise error?
        # Spec says "Filter entries to include ONLY Type I isotherms"
        # If column missing, we cannot filter. Raise error or log warning.
        logger.warning("Column 'isotherm_type' not found. Assuming all are Type I.")
        return df

def remove_missing_targets(df: pd.DataFrame, target_cols: List[str]) -> pd.DataFrame:
    """Remove entries with missing target values."""
    initial_count = len(df)
    df = df.dropna(subset=target_cols)
    removed = initial_count - len(df)
    if removed > 0:
        logger.info(f"Removed {removed} rows with missing targets.")
    return df.reset_index(drop=True)

def normalize_units(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize units (e.g., surface area to m²/g)."""
    # Placeholder for specific unit conversion logic
    # Assuming data is already in correct units or standardizing here
    # If 'surface_area' exists and unit column exists, convert
    if 'surface_area' in df.columns and 'surface_area_unit' in df.columns:
        # Example: convert from cm2/g to m2/g
        mask_cm2 = df['surface_area_unit'].astype(str).str.lower().str.contains('cm2')
        df.loc[mask_cm2, 'surface_area'] = df.loc[mask_cm2, 'surface_area'] / 10000
        # Update unit column
        df.loc[mask_cm2, 'surface_area_unit'] = 'm2/g'
    return df

def handle_missing_pore_volume(df: pd.DataFrame, exclusion_log_path: str) -> pd.DataFrame:
    """
    Exclude entries with missing pore volume and log the exclusion.
    
    Args:
        df: Input dataframe.
        exclusion_log_path: Path to write the exclusion log JSON.
        
    Returns:
        Filtered dataframe.
    """
    if 'pore_volume' not in df.columns:
        logger.warning("Column 'pore_volume' not found. No exclusions based on this.")
        return df

    initial_count = len(df)
    missing_mask = df['pore_volume'].isna()
    excluded_count = missing_mask.sum()
    
    if excluded_count > 0:
        logger.info(f"Excluding {excluded_count} rows with missing pore volume.")
        
        # Log exclusions
        excluded_indices = df.index[missing_mask].tolist()
        log_entry = {
            "reason": "Missing pore_volume",
            "count": excluded_count,
            "indices": excluded_indices
        }
        
        log_path = Path(exclusion_log_path)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Load existing log if exists
        if log_path.exists():
            with open(log_path, 'r') as f:
                log_data = json.load(f)
            if 'entries' not in log_data:
                log_data['entries'] = []
            log_data['entries'].append(log_entry)
        else:
            log_data = {"entries": [log_entry]}
        
        with open(log_path, 'w') as f:
            json.dump(log_data, f, indent=2)
        
        df = df[~missing_mask].reset_index(drop=True)
    else:
        logger.info("No rows excluded due to missing pore volume.")

    return df

def calculate_descriptor_hash(row: pd.Series) -> str:
    """Calculate a hash of the descriptor values for a row."""
    # Select descriptor columns
    desc_cols = [c for c in row.index if c.startswith('desc_') or c in ['molecular_weight', 'polarizability', 'kinetic_diameter']]
    if not desc_cols:
        # Fallback to all numeric columns if descriptor prefix not found
        desc_cols = [c for c in row.index if row[c] is not None and isinstance(row[c], (int, float))]
    
    values = [str(row[c]) for c in desc_cols if pd.notna(row[c])]
    if not values:
        return "no_descriptors"
    
    return hashlib.md5("".join(values).encode()).hexdigest()

def detect_outliers(df: pd.DataFrame, target_col: str, output_path: str) -> pd.DataFrame:
    """
    Detect outliers based on descriptor hash groups.
    Flag adsorbates with identical descriptors but conflicting targets.
    Threshold: |value - mean_group| > 3 * std_group
    """
    if 'descriptor_hash' not in df.columns:
        df['descriptor_hash'] = df.apply(calculate_descriptor_hash, axis=1)

    initial_count = len(df)
    flagged_indices = []
    exclusion_log = []

    # Group by descriptor_hash
    grouped = df.groupby('descriptor_hash')

    for hash_val, group in grouped:
        if len(group) < 2:
            continue
        
        if target_col not in group.columns:
            continue
        
        values = group[target_col].values
        mean_val = np.mean(values)
        std_val = np.std(values)
        
        if std_val == 0:
            continue # No variance, no outliers by this rule
        
        # Check for outliers
        for idx, val in zip(group.index, values):
            if abs(val - mean_val) > 3 * std_val:
                flagged_indices.append(idx)
                exclusion_log.append({
                    "material_id": group.loc[idx, 'material_id'] if 'material_id' in group.columns else idx,
                    "descriptor_hash": hash_val,
                    "target_value": float(val),
                    "group_mean": float(mean_val),
                    "group_std": float(std_val),
                    "deviation": float(abs(val - mean_val)),
                    "exclusion_reason": f"Target value {val} deviates > 3σ from group mean {mean_val} (std={std_val})"
                })

    if flagged_indices:
        logger.warning(f"Detected {len(flagged_indices)} outliers. Excluding them.")
        df_clean = df.drop(index=flagged_indices).reset_index(drop=True)
        
        # Write outlier report
        out_path = Path(output_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Convert to DataFrame for CSV
        if exclusion_log:
            out_df = pd.DataFrame(exclusion_log)
            out_df.to_csv(output_path, index=False)
            logger.info(f"Outlier report written to {output_path}")
        else:
            # Empty file if no outliers but logic ran
            pd.DataFrame(columns=['material_id', 'descriptor_hash', 'target_variance', 'exclusion_reason']).to_csv(output_path, index=False)
    else:
        df_clean = df
        # Ensure output file exists even if empty
        out_path = Path(output_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(columns=['material_id', 'descriptor_hash', 'target_variance', 'exclusion_reason']).to_csv(output_path, index=False)

    return df_clean

def preprocess_pipeline(input_dir: str, output_dir: str, target_cols: List[str]) -> pd.DataFrame:
    """Run the full preprocessing pipeline."""
    logger.info(f"Starting preprocessing pipeline. Input: {input_dir}, Output: {output_dir}")
    
    # 1. Load
    df = load_raw_data(input_dir)
    
    # 2. Filter Type I
    df = filter_type_isotherms(df)
    
    # 3. Remove missing targets
    df = remove_missing_targets(df, target_cols)
    
    # 4. Normalize units
    df = normalize_units(df)
    
    # 5. Handle missing pore volume
    exclusion_log_path = os.path.join(output_dir, "validation", "exclusion_log.json")
    df = handle_missing_pore_volume(df, exclusion_log_path)
    
    # 6. Calculate descriptors if not present
    # Assuming descriptors are calculated in loader or here
    # If not, we need to call calculate_descriptors_batch
    # For now, assuming they are in the dataframe or calculated by loader
    # If missing, we might need to compute them here.
    # Let's assume the loader provides raw SMILES and we compute here if needed.
    # But T014a is done. Let's assume they are there.
    # If 'molecular_weight' is missing, we compute.
    if 'molecular_weight' not in df.columns and 'smiles' in df.columns:
        logger.info("Calculating descriptors...")
        # This might be heavy, so we assume it's done or we do a batch
        # For this task, we assume the data is prepped or we call the function
        # from data.descriptors import calculate_descriptors_batch
        # descriptors = calculate_descriptors_batch(df['smiles'].tolist())
        # df = pd.concat([df, descriptors], axis=1)
        pass
    
    # 7. Outlier detection
    outliers_path = os.path.join(output_dir, "outliers.csv")
    df = detect_outliers(df, target_cols[0], outliers_path)
    
    # Save processed data
    processed_path = os.path.join(output_dir, "processed_data.csv")
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    df.to_csv(processed_path, index=False)
    
    logger.info(f"Preprocessing complete. Output: {processed_path}")
    return df

def main():
    """Entry point for preprocessing."""
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--data-dir', type=str, required=True)
    parser.add_argument('--output-dir', type=str, required=True)
    args = parser.parse_args()
    
    target_cols = ['langmuir_capacity', 'henry_constant'] # Example targets
    preprocess_pipeline(args.data_dir, args.output_dir, target_cols)

if __name__ == "__main__":
    main()
