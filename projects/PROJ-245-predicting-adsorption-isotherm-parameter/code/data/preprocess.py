"""
Preprocess the adsorption dataset.

This module implements the data curation pipeline for User Story 1:
- Filter Type I isotherms
- Remove entries with missing targets
- Normalize units (m²/g)
- Handle missing pore volume (imputation or exclusion)
- Calculate descriptor hashes
- Detect outliers
"""

import os
import sys
import logging
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import pandas as pd
import numpy as np

# Import from sibling modules using exact API surface names
from data.descriptors import calculate_descriptors_batch, generate_descriptor_hash
from data.imputation import impute_pore_volume
from data.validate import DatasetSizeError

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
MIN_DATASET_SIZE = 500
PORE_VOLUME_EXCLUSION_THRESHOLD = 0.10  # 10%

class DatasetSizeError(Exception):
    """Raised when the dataset size falls below the minimum threshold."""
    pass

def load_raw_data(data_dir: Path) -> pd.DataFrame:
    """
    Load the raw merged dataset.
    
    Args:
        data_dir: Path to the directory containing the merged dataset.
        
    Returns:
        DataFrame with the raw dataset.
        
    Raises:
        FileNotFoundError: If the merged dataset is not found.
    """
    merged_path = data_dir / "merged_dataset.parquet"
    if not merged_path.exists():
        raise FileNotFoundError(f"Merged dataset not found at {merged_path}")
    
    logger.info(f"Loading raw data from {merged_path}")
    df = pd.read_parquet(merged_path)
    logger.info(f"Loaded {len(df)} rows")
    return df

def filter_type_isotherms(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filter to include only Type I isotherms.
    
    Args:
        df: Input DataFrame.
        
    Returns:
        Filtered DataFrame with only Type I isotherms.
    """
    logger.info("Filtering for Type I isotherms")
    
    # Check for different possible column names
    isotherm_type_col = None
    for col in ['isotherm_type', 'IsothermType', 'type', 'Type']:
        if col in df.columns:
            isotherm_type_col = col
            break
    
    if isotherm_type_col is None:
        logger.warning("No isotherm type column found. Assuming all are Type I.")
        return df
    
    # Filter for Type I (value 'I', '1', or 1)
    mask = df[isotherm_type_col].isin(['I', '1', 1])
    filtered_df = df[mask].copy()
    
    logger.info(f"Filtered from {len(df)} to {len(filtered_df)} rows (Type I only)")
    return filtered_df

def remove_missing_targets(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[Dict[str, Any]]]:
    """
    Remove entries where langmuir_capacity or henry_constant is missing.
    
    Args:
        df: Input DataFrame.
        
    Returns:
        Tuple of (filtered DataFrame, list of exclusion records).
    """
    logger.info("Removing entries with missing targets")
    
    exclusion_log = []
    
    # Identify missing targets
    missing_langmuir = df['langmuir_capacity'].isna()
    missing_henry = df['henry_constant'].isna()
    missing_any = missing_langmuir | missing_henry
    
    if missing_any.any():
        for idx in df[missing_any].index:
            row = df.loc[idx]
            exclusion_log.append({
                'material_id': row.get('material_id', idx),
                'reason': 'missing_target',
                'missing_fields': []
            })
            if missing_langmuir.loc[idx]:
                exclusion_log[-1]['missing_fields'].append('langmuir_capacity')
            if missing_henry.loc[idx]:
                exclusion_log[-1]['missing_fields'].append('henry_constant')
        
        df = df[~missing_any].copy()
        logger.info(f"Removed {missing_any.sum()} rows with missing targets")
    else:
        logger.info("No missing targets found")
    
    return df, exclusion_log

def normalize_units(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalize units to m²/g for surface area.
    
    Args:
        df: Input DataFrame.
        
    Returns:
        DataFrame with normalized units.
    """
    logger.info("Normalizing units")
    
    # Check for surface area column
    surface_area_col = None
    for col in ['surface_area', 'SurfaceArea', 'specific_surface_area']:
        if col in df.columns:
            surface_area_col = col
            break
    
    if surface_area_col is None:
        logger.warning("No surface area column found. Skipping normalization.")
        return df
    
    # Check for unit column
    unit_col = None
    for col in ['unit', 'Unit', 'surface_area_unit']:
        if col in df.columns:
            unit_col = col
            break
    
    if unit_col is not None:
        # Convert from m²/kg to m²/g if necessary
        mask = df[unit_col].isin(['m²/kg', 'm2/kg', 'm² kg⁻¹'])
        if mask.any():
            logger.info(f"Converting {mask.sum()} surface area values from m²/kg to m²/g")
            df.loc[mask, surface_area_col] = df.loc[mask, surface_area_col] / 1000.0
            df.loc[mask, unit_col] = 'm²/g'
    else:
        # Assume all values are already in m²/g or need no conversion
        logger.info("No unit column found. Assuming m²/g.")
    
    return df

def handle_missing_pore_volume(
    df: pd.DataFrame,
    exclusion_log: List[Dict[str, Any]]
) -> Tuple[pd.DataFrame, List[Dict[str, Any]], bool]:
    """
    Handle missing pore volume values.
    
    Logic:
    1. If pore_volume is missing, attempt imputation using mean of similar materials.
    2. If imputation fails or is not applicable, exclude the entry.
    3. Log exclusions to exclusion_log.
    4. If exclusion count > 10%, return flag to invoke imputation function.
    
    Args:
        df: Input DataFrame.
        exclusion_log: Existing exclusion log to append to.
        
    Returns:
        Tuple of (processed DataFrame, updated exclusion log, flag for imputation needed).
    """
    logger.info("Handling missing pore volume")
    
    # Check for pore volume column
    pore_volume_col = None
    for col in ['pore_volume', 'PoreVolume', 'pore_vol']:
        if col in df.columns:
            pore_volume_col = col
            break
    
    if pore_volume_col is None:
        logger.warning("No pore volume column found. Skipping handling.")
        return df, exclusion_log, False
    
    missing_mask = df[pore_volume_col].isna()
    total_missing = missing_mask.sum()
    
    if total_missing == 0:
        logger.info("No missing pore volume values found")
        return df, exclusion_log, False
    
    logger.info(f"Found {total_missing} missing pore volume values ({100*total_missing/len(df):.1f}% of data)")
    
    # Check if imputation should be triggered (> 10% missing)
    imputation_needed = (total_missing / len(df)) > PORE_VOLUME_EXCLUSION_THRESHOLD
    
    if imputation_needed:
        logger.info(f"Missing pore volume exceeds {PORE_VOLUME_EXCLUSION_THRESHOLD*100}% threshold. Triggering imputation.")
        # Import imputation function
        from data.imputation import impute_pore_volume as impute_func
        df, imputation_log = impute_func(df)
        
        # Check if imputation succeeded for all missing values
        still_missing = df[pore_volume_col].isna()
        if still_missing.any():
            # Log the ones that couldn't be imputed
            for idx in df[still_missing].index:
                row = df.loc[idx]
                exclusion_log.append({
                    'material_id': row.get('material_id', idx),
                    'reason': 'pore_volume_imputation_failed',
                    'missing_fields': ['pore_volume']
                })
            df = df[~still_missing].copy()
    else:
        # Direct exclusion for missing pore volume
        exclusion_count = 0
        for idx in df[missing_mask].index:
            row = df.loc[idx]
            exclusion_log.append({
                'material_id': row.get('material_id', idx),
                'reason': 'missing_pore_volume',
                'missing_fields': ['pore_volume']
            })
            exclusion_count += 1
        
        df = df[~missing_mask].copy()
        logger.info(f"Excluded {exclusion_count} rows with missing pore volume")
    
    return df, exclusion_log, imputation_needed

def calculate_descriptor_hash(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate descriptor hash for each row.
    
    Args:
        df: Input DataFrame.
        
    Returns:
        DataFrame with descriptor_hash column added.
    """
    logger.info("Calculating descriptor hashes")
    
    # Check if descriptors are already calculated
    descriptor_cols = ['polarizability', 'kinetic_diameter', 'lj_epsilon', 'quadrupole_moment']
    if all(col in df.columns for col in descriptor_cols):
        logger.info("Using existing descriptor values to calculate hash")
        df['descriptor_hash'] = generate_descriptor_hash(df, descriptor_cols)
    else:
        logger.info("Descriptors not found. Calculating descriptors first.")
        # Calculate descriptors
        df = calculate_descriptors_batch(df)
        df['descriptor_hash'] = generate_descriptor_hash(df, descriptor_cols)
    
    return df

def detect_outliers(
    df: pd.DataFrame,
    target_col: str = 'langmuir_capacity'
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Detect outliers based on descriptor hash and target variance.
    
    Logic:
    1. Group by descriptor_hash
    2. Calculate variance of target within each group
    3. Flag entries where |value - mean_group| > 3 * std_group
    
    Args:
        df: Input DataFrame.
        target_col: Target column to check for outliers.
        
    Returns:
        Tuple of (cleaned DataFrame, outliers DataFrame).
    """
    logger.info("Detecting outliers")
    
    if 'descriptor_hash' not in df.columns:
        logger.warning("No descriptor_hash column found. Skipping outlier detection.")
        return df, pd.DataFrame()
    
    if target_col not in df.columns:
        logger.warning(f"Target column '{target_col}' not found. Skipping outlier detection.")
        return df, pd.DataFrame()
    
    # Group by descriptor_hash
    grouped = df.groupby('descriptor_hash')
    
    outlier_records = []
    
    for hash_val, group in grouped:
        if len(group) < 2:
            continue
        
        mean_val = group[target_col].mean()
        std_val = group[target_col].std()
        
        if std_val == 0 or np.isnan(std_val):
            continue
        
        # Check for outliers
        for idx, row in group.iterrows():
            deviation = abs(row[target_col] - mean_val)
            if deviation > 3 * std_val:
                outlier_records.append({
                    'material_id': row.get('material_id', idx),
                    'descriptor_hash': hash_val,
                    'target_variance': std_val,
                    'exclusion_reason': f'3-sigma outlier: deviation={deviation:.4f}, threshold={3*std_val:.4f}'
                })
    
    if outlier_records:
        outlier_df = pd.DataFrame(outlier_records)
        outlier_df.to_csv('data/processed/outliers.csv', index=False)
        logger.info(f"Detected {len(outlier_records)} outliers. Saved to data/processed/outliers.csv")
        
        # Remove outliers from main dataset
        outlier_hashes = set(outlier_df['descriptor_hash'])
        df = df[~df['descriptor_hash'].isin(outlier_hashes)].copy()
    else:
        logger.info("No outliers detected")
        # Create empty outliers file
        pd.DataFrame(columns=['material_id', 'descriptor_hash', 'target_variance', 'exclusion_reason']).to_csv(
            'data/processed/outliers.csv', index=False
        )
    
    return df, pd.DataFrame(outlier_records) if outlier_records else pd.DataFrame()

def save_logs(
    exclusion_log: List[Dict[str, Any]],
    output_dir: Path
) -> None:
    """
    Save exclusion log to JSON file.
    
    Args:
        exclusion_log: List of exclusion records.
        output_dir: Directory to save the log.
    """
    log_path = output_dir / "exclusion_log.json"
    with open(log_path, 'w') as f:
        json.dump(exclusion_log, f, indent=2)
    logger.info(f"Saved exclusion log to {log_path}")

def preprocess_pipeline(data_dir: Path, output_dir: Path) -> pd.DataFrame:
    """
    Run the full preprocessing pipeline.
    
    Args:
        data_dir: Directory containing raw data.
        output_dir: Directory to save processed data.
        
    Returns:
        Processed DataFrame.
    """
    logger.info("Starting preprocessing pipeline")
    
    # Ensure output directory exists
    output_dir.mkdir(parents=True, exist_ok=True)
    validation_dir = output_dir.parent / "validation"
    validation_dir.mkdir(parents=True, exist_ok=True)
    
    # Step 1: Load raw data
    df = load_raw_data(data_dir)
    
    # Step 2: Filter Type I isotherms
    df = filter_type_isotherms(df)
    
    # Step 3: Remove missing targets
    df, exclusion_log = remove_missing_targets(df)
    
    # Step 4: Validate dataset size after target removal
    if len(df) < MIN_DATASET_SIZE:
        raise DatasetSizeError(
            f"Dataset size {len(df)} is below minimum threshold {MIN_DATASET_SIZE} "
            "after removing entries with missing targets."
        )
    
    # Step 5: Normalize units
    df = normalize_units(df)
    
    # Step 6: Handle missing pore volume
    df, exclusion_log, imputation_triggered = handle_missing_pore_volume(df, exclusion_log)
    
    # Step 7: Validate dataset size again
    if len(df) < MIN_DATASET_SIZE:
        raise DatasetSizeError(
            f"Dataset size {len(df)} is below minimum threshold {MIN_DATASET_SIZE} "
            "after handling missing pore volume."
        )
    
    # Step 8: Calculate descriptor hash
    df = calculate_descriptor_hash(df)
    
    # Step 9: Detect outliers
    df, _ = detect_outliers(df)
    
    # Step 10: Save exclusion log
    save_logs(exclusion_log, validation_dir)
    
    # Step 11: Save processed data
    output_path = output_dir / "processed_dataset.csv"
    df.to_csv(output_path, index=False)
    logger.info(f"Saved processed data to {output_path}")
    
    logger.info(f"Preprocessing complete. Final dataset size: {len(df)}")
    return df

def main():
    """Main entry point for preprocessing."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Preprocess adsorption dataset')
    parser.add_argument('--data-dir', type=str, default='data/raw',
                      help='Directory containing raw data')
    parser.add_argument('--output-dir', type=str, default='data/processed',
                      help='Directory to save processed data')
    
    args = parser.parse_args()
    
    data_dir = Path(args.data_dir)
    output_dir = Path(args.output_dir)
    
    try:
        df = preprocess_pipeline(data_dir, output_dir)
        logger.info("Preprocessing completed successfully")
    except DatasetSizeError as e:
        logger.error(str(e))
        sys.exit(1)
    except Exception as e:
        logger.error(f"Preprocessing failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == '__main__':
    main()