"""
Imputation module for handling missing pore_volume values.

Implements imputation of missing features (specifically pore_volume) using
the mean of similar materials clustered by material_type or surface_area bin.
Only features are imputed; targets are never imputed.
"""

import os
import sys
import logging
import json
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import pandas as pd
import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Ensure output directory exists
OUTPUT_DIR = Path("data/validation")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

IMPUTATION_LOG_PATH = OUTPUT_DIR / "imputation_log.json"

def ensure_directories():
    """Ensure all required directories exist."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def impute_pore_volume(df: pd.DataFrame, impute_by: str = 'material_type') -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Impute missing pore_volume values using the mean of similar materials.
    
    Args:
        df: Input DataFrame with potential missing pore_volume values
        impute_by: Clustering strategy - 'material_type' or 'surface_area_bin'
    
    Returns:
        Tuple of (imputed DataFrame, imputation metadata)
    
    Raises:
        ValueError: If impute_by is not a valid option
        RuntimeError: If imputation fails for all groups
    """
    ensure_directories()
    
    if impute_by not in ['material_type', 'surface_area_bin']:
        raise ValueError(f"impute_by must be 'material_type' or 'surface_area_bin', got '{impute_by}'")
    
    if 'pore_volume' not in df.columns:
        logger.warning("Column 'pore_volume' not found in DataFrame. No imputation performed.")
        return df, {
            'imputed': False,
            'reason': 'pore_volume column not found',
            'rows_imputed': 0,
            'strategy': impute_by,
            'group_stats': {}
        }
    
    missing_mask = df['pore_volume'].isna()
    missing_count = missing_mask.sum()
    
    if missing_count == 0:
        logger.info("No missing pore_volume values found. No imputation needed.")
        return df, {
            'imputed': False,
            'reason': 'no missing values',
            'rows_imputed': 0,
            'strategy': impute_by,
            'group_stats': {}
        }
    
    logger.info(f"Found {missing_count} missing pore_volume values. Starting imputation...")
    
    df_imputed = df.copy()
    group_stats = {}
    rows_imputed = 0
    
    if impute_by == 'material_type':
        if 'material_type' not in df.columns:
            logger.warning("Column 'material_type' not found. Falling back to global mean.")
            # Fallback to global mean
            global_mean = df['pore_volume'].mean()
            if pd.isna(global_mean):
                raise RuntimeError("Cannot compute global mean for pore_volume (all values missing).")
            
            df_imputed.loc[missing_mask, 'pore_volume'] = global_mean
            rows_imputed = missing_count
            group_stats['global_mean'] = float(global_mean)
            logger.info(f"Imputed {rows_imputed} rows using global mean: {global_mean:.4f}")
        else:
            # Group by material_type and impute with group mean
            for material_type, group in df.groupby('material_type'):
                group_missing_mask = group['pore_volume'].isna()
                if group_missing_mask.any():
                    group_mean = group.loc[~group_missing_mask, 'pore_volume'].mean()
                    if pd.isna(group_mean):
                        logger.warning(f"No valid pore_volume values for material_type '{material_type}'. Skipping imputation for this group.")
                        continue
                    
                    # Count how many we can impute in this group
                    imputable_count = group_missing_mask.sum()
                    df_imputed.loc[group.index[group_missing_mask], 'pore_volume'] = group_mean
                    rows_imputed += imputable_count
                    
                    group_stats[material_type] = {
                        'mean': float(group_mean),
                        'imputed_count': int(imputable_count)
                    }
    
    elif impute_by == 'surface_area_bin':
        if 'surface_area' not in df.columns:
            logger.warning("Column 'surface_area' not found. Cannot bin by surface_area.")
            # Fallback to global mean
            global_mean = df['pore_volume'].mean()
            if pd.isna(global_mean):
                raise RuntimeError("Cannot compute global mean for pore_volume (all values missing).")
            
            df_imputed.loc[missing_mask, 'pore_volume'] = global_mean
            rows_imputed = missing_count
            group_stats['global_mean'] = float(global_mean)
            logger.info(f"Imputed {rows_imputed} rows using global mean: {global_mean:.4f}")
        else:
            # Create surface area bins (e.g., 10 bins)
            df_temp = df.copy()
            df_temp['surface_area_bin'] = pd.qcut(
                df_temp['surface_area'].dropna(), 
                q=10, 
                duplicates='drop',
                labels=False
            )
            
            # Map bins back to original dataframe
            df_imputed['surface_area_bin'] = df_temp['surface_area_bin']
            
            for bin_id in df_imputed['surface_area_bin'].unique():
                if pd.isna(bin_id):
                    continue
                
                bin_mask = df_imputed['surface_area_bin'] == bin_id
                bin_missing_mask = df_imputed.loc[bin_mask, 'pore_volume'].isna()
                
                if bin_missing_mask.any():
                    bin_mean = df_imputed.loc[bin_mask & ~bin_missing_mask, 'pore_volume'].mean()
                    if pd.isna(bin_mean):
                        logger.warning(f"No valid pore_volume values for surface_area_bin {bin_id}. Skipping.")
                        continue
                    
                    imputable_count = bin_missing_mask.sum()
                    df_imputed.loc[bin_mask & bin_missing_mask, 'pore_volume'] = bin_mean
                    rows_imputed += imputable_count
                    
                    group_stats[f'bin_{bin_id}'] = {
                        'mean': float(bin_mean),
                        'imputed_count': int(imputable_count)
                    }
    
    if rows_imputed == 0 and missing_count > 0:
        raise RuntimeError(f"Failed to impute any of the {missing_count} missing pore_volume values.")
    
    imputation_result = {
        'imputed': True,
        'reason': 'missing values imputed',
        'rows_imputed': int(rows_imputed),
        'total_missing': int(missing_count),
        'strategy': impute_by,
        'group_stats': group_stats,
        'timestamp': pd.Timestamp.now().isoformat()
    }
    
    logger.info(f"Imputation complete: {rows_imputed}/{missing_count} rows imputed using strategy '{impute_by}'")
    
    return df_imputed, imputation_result

def save_imputation_log(imputation_result: Dict[str, Any]):
    """Save imputation log to JSON file."""
    ensure_directories()
    
    # Load existing log if it exists
    if IMPUTATION_LOG_PATH.exists():
        try:
            with open(IMPUTATION_LOG_PATH, 'r') as f:
                existing_log = json.load(f)
                if not isinstance(existing_log, list):
                    existing_log = [existing_log]
        except (json.JSONDecodeError, IOError):
            existing_log = []
    else:
        existing_log = []
    
    existing_log.append(imputation_result)
    
    with open(IMPUTATION_LOG_PATH, 'w') as f:
        json.dump(existing_log, f, indent=2, default=str)
    
    logger.info(f"Imputation log saved to {IMPUTATION_LOG_PATH}")

def main():
    """
    Main entry point for imputation script.
    
    Reads the preprocessed dataset, performs imputation on missing pore_volume,
    and saves the updated dataset along with the imputation log.
    
    Expected input: data/processed/preprocessed_data.csv (or similar)
    Output: data/processed/imputed_data.csv and data/validation/imputation_log.json
    """
    # Try to find the input file
    input_candidates = [
        Path("data/processed/preprocessed_data.csv"),
        Path("data/processed/processed_data.csv"),
        Path("data/raw/merged_dataset.parquet"),
        Path("data/raw/merged_dataset.csv")
    ]
    
    input_file = None
    for candidate in input_candidates:
        if candidate.exists():
            input_file = candidate
            break
    
    if input_file is None:
        # Create a minimal test case if no input exists (for development)
        logger.warning("No input data file found. Creating test data for demonstration.")
        test_data = pd.DataFrame({
            'material_id': ['MOF-1', 'MOF-2', 'MOF-3', 'MOF-4', 'MOF-5'],
            'material_type': ['MOF', 'MOF', 'COF', 'MOF', 'COF'],
            'surface_area': [1000.0, 2000.0, 1500.0, np.nan, 1200.0],
            'pore_volume': [0.5, np.nan, 0.8, 0.6, np.nan],
            'langmuir_capacity': [10.0, 15.0, 12.0, 11.0, 13.0],
            'henry_constant': [0.5, 0.6, 0.55, 0.52, 0.58]
        })
        df = test_data
        output_file = Path("data/processed/imputed_data.csv")
        output_file.parent.mkdir(parents=True, exist_ok=True)
    else:
        logger.info(f"Loading data from {input_file}")
        if input_file.suffix == '.parquet':
            df = pd.read_parquet(input_file)
        else:
            df = pd.read_csv(input_file)
        output_file = Path(str(input_file).replace('.csv', '_imputed.csv').replace('.parquet', '_imputed.parquet'))
    
    # Perform imputation
    df_imputed, imputation_result = impute_pore_volume(df, impute_by='material_type')
    
    # Save imputation log
    save_imputation_log(imputation_result)
    
    # Save imputed dataset
    if output_file.suffix == '.parquet':
        df_imputed.to_parquet(output_file, index=False)
    else:
        df_imputed.to_csv(output_file, index=False)
    
    logger.info(f"Imputed dataset saved to {output_file}")
    
    return df_imputed, imputation_result

if __name__ == "__main__":
    main()