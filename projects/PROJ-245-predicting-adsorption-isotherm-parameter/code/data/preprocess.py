import os
import sys
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
import numpy as np
import hashlib
import json

# Ensure parent directory is in path for imports if running as script
_root = Path(__file__).resolve().parent.parent
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from data.descriptors import calculate_descriptors_batch
from data.validate_schema import load_schema, validate_dataframe

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_raw_data(input_path: str) -> pd.DataFrame:
    """
    Load raw data from a CSV file.
    """
    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"Raw data file not found: {input_path}")
    
    logger.info(f"Loading raw data from {input_path}")
    df = pd.read_csv(path)
    logger.info(f"Loaded {len(df)} rows")
    return df

def filter_type_isotherms(df: pd.DataFrame, isotherm_type_col: str = 'isotherm_type', valid_types: List[str] = ['Type I', 'Type I(a)', 'Type I(b)']) -> pd.DataFrame:
    """
    Filter the dataframe to keep only Type I isotherms.
    """
    logger.info(f"Filtering for isotherm types: {valid_types}")
    mask = df[isotherm_type_col].isin(valid_types)
    filtered_df = df[mask].copy()
    dropped = len(df) - len(filtered_df)
    if dropped > 0:
        logger.warning(f"Dropped {dropped} rows due to non-Type I isotherms")
    return filtered_df

def remove_missing_targets(df: pd.DataFrame, target_cols: List[str] = None) -> pd.DataFrame:
    """
    Remove rows where target variables are missing.
    """
    if target_cols is None:
        # Common targets based on schema
        target_cols = ['langmuir_capacity', 'henry_constant']
    
    logger.info(f"Removing rows with missing targets: {target_cols}")
    initial_len = len(df)
    # Drop rows where ANY of the target columns are NaN
    cleaned_df = df.dropna(subset=target_cols)
    removed = initial_len - len(cleaned_df)
    if removed > 0:
        logger.warning(f"Removed {removed} rows with missing target values")
    return cleaned_df

def normalize_units(df: pd.DataFrame, surface_area_col: str = 'surface_area') -> pd.DataFrame:
    """
    Normalize units, specifically ensuring surface area is in m²/g.
    Assuming input is already in correct units or needs simple scaling if specified.
    For this task, we ensure the column exists and is numeric.
    """
    logger.info("Normalizing units")
    if surface_area_col in df.columns:
        df[surface_area_col] = pd.to_numeric(df[surface_area_col], errors='coerce')
        # If a unit conversion factor was needed, it would go here
    return df

def handle_missing_pore_volume(df: pd.DataFrame, pore_volume_col: str = 'pore_volume', strategy: str = 'exclude') -> pd.DataFrame:
    """
    Handle missing pore volume.
    Strategy: 'exclude' (drop rows) or 'impute' (mean/median).
    Logging is required per task description.
    """
    if pore_volume_col not in df.columns:
        logger.warning(f"Column {pore_volume_col} not found, skipping missing value handling")
        return df

    initial_len = len(df)
    missing_count = df[pore_volume_col].isna().sum()
    
    if missing_count == 0:
        logger.info("No missing pore volume values found.")
        return df

    logger.info(f"Found {missing_count} missing pore volume values. Strategy: {strategy}")

    if strategy == 'exclude':
        cleaned_df = df.dropna(subset=[pore_volume_col])
        removed = initial_len - len(cleaned_df)
        logger.warning(f"Excluded {removed} rows due to missing pore volume.")
        return cleaned_df
    
    elif strategy == 'impute':
        # Impute with median to be robust against outliers
        median_val = df[pore_volume_col].median()
        df[pore_volume_col] = df[pore_volume_col].fillna(median_val)
        logger.info(f"Imputed {missing_count} missing pore volume values with median: {median_val}")
        return df
    
    else:
        raise ValueError(f"Unknown strategy '{strategy}' for missing pore volume")

def _compute_descriptor_hash(row: pd.Series, descriptor_cols: List[str]) -> str:
    """
    Compute a deterministic hash for the descriptor values of a row.
    """
    # Extract values, handle NaN by replacing with a specific placeholder string
    values = [str(v) if pd.notna(v) else "NaN" for v in row[descriptor_cols]]
    # Create a unique string representation
    content = "|".join(values)
    return hashlib.sha256(content.encode('utf-8')).hexdigest()[:16]

def detect_outliers(df: pd.DataFrame, descriptor_cols: List[str] = None, target_cols: List[str] = None) -> pd.DataFrame:
    """
    Detect outliers by identifying adsorbates with identical descriptors but conflicting targets.
    
    Logic:
    1. Group by descriptor values (hashed for efficiency).
    2. Within each group, check variance in target variables.
    3. If variance > 0 (or > threshold), flag as outlier.
    
    Output: DataFrame with columns [material_id, descriptor_hash, target_variance]
    """
    if descriptor_cols is None:
        # Default to common descriptors calculated in T014
        descriptor_cols = ['molecular_weight', 'polar_surface_area', 'polarizability', 
                         'h_bond_donors', 'h_bond_acceptors', 'vdw_volume', 'kinetic_diameter']
    
    if target_cols is None:
        target_cols = ['langmuir_capacity', 'henry_constant']

    # Ensure descriptor columns exist
    missing_desc = [c for c in descriptor_cols if c not in df.columns]
    if missing_desc:
        logger.warning(f"Missing descriptor columns: {missing_desc}. Attempting to calculate or skipping.")
        # If they are missing, we cannot group by them. 
        # In a real pipeline, T014 ensures these exist. 
        # If running standalone, we might need to calculate them or return empty.
        # For this task, we assume T014 has populated them.
        return pd.DataFrame(columns=['material_id', 'descriptor_hash', 'target_variance'])

    logger.info(f"Detecting outliers based on descriptors: {descriptor_cols}")
    
    # Add a temporary hash column
    df_temp = df.copy()
    df_temp['descriptor_hash'] = df_temp.apply(
        lambda row: _compute_descriptor_hash(row, descriptor_cols), axis=1
    )
    
    # Group by hash
    grouped = df_temp.groupby('descriptor_hash')
    
    outlier_records = []
    
    for hash_val, group in grouped:
        # We are looking for groups with MORE than 1 row (identical descriptors)
        # where targets differ.
        if len(group) > 1:
            # Calculate variance for each target column
            for target in target_cols:
                if target in group.columns:
                    variance = group[target].var()
                    # If variance is non-zero (or above a tiny epsilon), it's a conflict
                    if variance > 1e-9:
                        # Pick the first material_id in the group for reporting
                        material_id = group.iloc[0]['material_id']
                        outlier_records.append({
                            'material_id': material_id,
                            'descriptor_hash': hash_val,
                            'target_variance': variance
                        })
                        # Log the first occurrence
                        logger.warning(
                            f"Conflict detected for hash {hash_val}: "
                            f"Variance in {target} = {variance:.4f} across {len(group)} rows."
                        )
                        # Break to avoid duplicate reporting for the same hash if multiple targets vary
                        break
    
    if outlier_records:
        outliers_df = pd.DataFrame(outlier_records)
        logger.info(f"Found {len(outliers_df)} potential outliers with conflicting targets.")
    else:
        outliers_df = pd.DataFrame(columns=['material_id', 'descriptor_hash', 'target_variance'])
        logger.info("No outliers with conflicting targets found.")
        
    return outliers_df

def preprocess_pipeline(
    input_path: str, 
    output_path: str, 
    outliers_output_path: Optional[str] = None,
    isotherm_type_col: str = 'isotherm_type',
    target_cols: List[str] = None
) -> pd.DataFrame:
    """
    Run the full preprocessing pipeline:
    1. Load raw data
    2. Filter Type I isotherms
    3. Remove missing targets
    4. Normalize units
    5. Handle missing pore volume
    6. Detect outliers (identical descriptors, conflicting targets)
    
    Returns the cleaned dataframe and optionally saves the outliers.
    """
    logger.info("Starting preprocessing pipeline")
    
    # 1. Load
    df = load_raw_data(input_path)
    
    # 2. Filter
    df = filter_type_isotherms(df, isotherm_type_col=isotherm_type_col)
    
    # 3. Remove missing targets
    df = remove_missing_targets(df, target_cols=target_cols)
    
    # 4. Normalize
    df = normalize_units(df)
    
    # 5. Handle missing pore volume
    df = handle_missing_pore_volume(df)
    
    # 6. Detect Outliers
    # We need to identify columns that are descriptors. 
    # We assume the caller has ensured T014 has run, so these columns exist.
    # If not, we try to detect them or use a default list.
    descriptor_cols = [
        'molecular_weight', 'polar_surface_area', 'polarizability', 
        'h_bond_donors', 'h_bond_acceptors', 'vdw_volume', 'kinetic_diameter'
    ]
    
    # Filter to only existing descriptor columns in the dataframe
    existing_desc_cols = [c for c in descriptor_cols if c in df.columns]
    
    if len(existing_desc_cols) != len(descriptor_cols):
        logger.warning(f"Not all expected descriptor columns found. Found: {existing_desc_cols}")
    
    outliers_df = detect_outliers(df, descriptor_cols=existing_desc_cols, target_cols=target_cols)
    
    # Save outliers if path provided
    if outliers_output_path:
        out_path = Path(outliers_output_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        outliers_df.to_csv(out_path, index=False)
        logger.info(f"Outliers saved to {outliers_output_path}")
    
    # Save processed data
    out_path = Path(output_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    logger.info(f"Processed data saved to {output_path}")
    
    return df

def main():
    """
    Entry point for the preprocessing script.
    Expects input and output paths via environment variables or defaults.
    """
    # Default paths relative to project root
    project_root = Path(__file__).resolve().parent.parent
    input_path = os.environ.get('RAW_DATA_PATH', str(project_root / 'data' / 'raw' / 'synthetic_adsorption.csv'))
    output_path = os.environ.get('PROCESSED_DATA_PATH', str(project_root / 'data' / 'processed' / 'cleaned_adsorption.csv'))
    outliers_path = os.environ.get('OUTLIERS_PATH', str(project_root / 'data' / 'processed' / 'outliers.csv'))
    
    # Check if input exists
    if not Path(input_path).exists():
        logger.error(f"Input file not found: {input_path}")
        # If synthetic data hasn't been generated yet, we can't proceed
        # In a real pipeline, T005 would have run first.
        # We raise an error to fail loudly as per constraints.
        raise FileNotFoundError(f"Cannot run pipeline. Input file missing: {input_path}")

    try:
        preprocess_pipeline(
            input_path=input_path,
            output_path=output_path,
            outliers_output_path=outliers_path,
            target_cols=['langmuir_capacity', 'henry_constant']
        )
        logger.info("Preprocessing pipeline completed successfully.")
    except Exception as e:
        logger.error(f"Pipeline failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == '__main__':
    main()