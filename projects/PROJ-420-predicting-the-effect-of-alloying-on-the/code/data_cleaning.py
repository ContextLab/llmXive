import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime
import numpy as np
import pandas as pd
from compositional import compositions

from config import get_config
from logging_config import get_logger

# Constants
REQUIRED_COMPOSITION_ELEMENTS = ['Cu', 'Mg', 'Si', 'Zn', 'Mn']
REQUIRED_PROPERTY_FIELDS = ['poissons_ratio', 'youngs_modulus']
MAJOR_ELEMENT_THRESHOLD = 0.95
MIN_VALID_ENTRIES = 50

def load_raw_data(source_paths: Dict[str, str]) -> pd.DataFrame:
    """
    Load raw data from JSON files produced by extraction.
    """
    logger = get_logger(__name__)
    dataframes = []

    for source, path in source_paths.items():
        p = Path(path)
        if not p.exists():
            logger.warning(f"Source file missing: {path}. Skipping {source}.")
            continue

        with open(p, 'r') as f:
            records = json.load(f)

        if not records:
            logger.warning(f"No records found in {path}.")
            continue

        df = pd.DataFrame(records)
        df['source'] = source
        dataframes.append(df)
        logger.info(f"Loaded {len(df)} records from {source}.")

    if not dataframes:
        raise ValueError("No data loaded from any source.")

    combined_df = pd.concat(dataframes, ignore_index=True)
    logger.info(f"Combined dataset size: {len(combined_df)}")
    return combined_df

def validate_schema(df: pd.DataFrame) -> pd.DataFrame:
    """
    Validate that required fields exist and are not null.
    """
    logger = get_logger(__name__)
    required_fields = REQUIRED_PROPERTY_FIELDS + REQUIRED_COMPOSITION_ELEMENTS + ['measurement_method']
    
    missing_cols = [col for col in required_fields if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required schema fields: {missing_cols}")

    # Check for nulls in required fields
    null_counts = df[required_fields].isnull().sum()
    if null_counts.any():
        logger.warning(f"Found null values in required fields:\n{null_counts[null_counts > 0]}")
        # Drop rows with any nulls in required fields
        initial_count = len(df)
        df = df.dropna(subset=required_fields)
        dropped = initial_count - len(df)
        logger.info(f"Dropped {dropped} rows due to missing required fields.")

    return df

def normalize_units(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalize units: Young's modulus to GPa, ensure compositions are fractions.
    """
    logger = get_logger(__name__)
    df = df.copy()

    # Assume Young's modulus is in GPa if > 100, otherwise convert from MPa
    # Heuristic: Al alloys are ~70 GPa. If value < 10, assume MPa and convert.
    if 'youngs_modulus' in df.columns:
        mask_mp = df['youngs_modulus'] < 10
        if mask_mp.any():
            logger.info(f"Converting {mask_mp.sum()} Young's modulus values from MPa to GPa.")
            df.loc[mask_mp, 'youngs_modulus'] = df.loc[mask_mp, 'youngs_modulus'] / 1000.0

    # Ensure composition columns are numeric and sum to ~1
    for col in REQUIRED_COMPOSITION_ELEMENTS:
        df[col] = pd.to_numeric(df[col], errors='coerce')

    # Calculate sum of specified elements
    df['composition_sum'] = df[REQUIRED_COMPOSITION_ELEMENTS].sum(axis=1)
    
    # If sum is very small (< 0.1), assume values are in percent and convert to fraction
    mask_percent = df['composition_sum'] < 0.1
    if mask_percent.any():
        logger.info(f"Converting {mask_percent.sum()} composition rows from percent to fraction.")
        df.loc[mask_percent, REQUIRED_COMPOSITION_ELEMENTS] /= 100.0
        df.loc[mask_percent, 'composition_sum'] /= 100.0

    return df

def verify_measurement_independence(df: pd.DataFrame) -> pd.DataFrame:
    """
    Verify measurement method for independence (FR-009).
    Exclude derived or non-experimental methods.
    """
    logger = get_logger(__name__)
    log_path = Path(get_config().data_dir) / 'logs' / 'independence_check.log'
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    valid_methods = ['ultrasonic', 'experimental', 'resonant', 'static']
    exclude_methods = ['Derived', 'calculated_from_Youngs_modulus', 'DFT', 'missing', 'null', '']

    initial_count = len(df)
    valid_rows = []
    
    for idx, row in df.iterrows():
        method = str(row.get('measurement_method', '')).strip().lower()
        
        # If field is missing or empty
        if not method or method == 'nan':
            logger.info(f"Excluded: Missing independence verification field (measurement_method). Row {idx}")
            continue
        
        # Check against exclude list
        if method in [m.lower() for m in exclude_methods]:
            logger.info(f"Excluded: Method '{row['measurement_method']}' is not independent. Row {idx}")
            continue
        
        # Check against valid list (case insensitive)
        if method in [m.lower() for m in valid_methods]:
            row['measurement_source'] = 'experimental'
            valid_rows.append(row)
        else:
            # If it's not in exclude but not explicitly valid, log and exclude to be safe
            logger.info(f"Excluded: Method '{row['measurement_method']}' not recognized as independent. Row {idx}")
            continue

    df_filtered = pd.DataFrame(valid_rows)
    dropped = initial_count - len(df_filtered)
    logger.info(f"Measurement independence check: Dropped {dropped} rows. Remaining: {len(df_filtered)}")
    
    return df_filtered

def filter_monolithic_alloys(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filter for monolithic alloys: non-missing Poisson's ratio, Young's modulus, and compositions.
    """
    logger = get_logger(__name__)
    
    # Ensure all required fields are present and non-null
    required = ['poissons_ratio', 'youngs_modulus'] + REQUIRED_COMPOSITION_ELEMENTS
    df = df.dropna(subset=required)
    
    # Filter for positive Poisson's ratio (physical constraint)
    df = df[df['poissons_ratio'] > 0]
    
    return df

def check_major_element_sum(df: pd.DataFrame) -> pd.DataFrame:
    """
    Exclude entries where major element sum < 0.95.
    """
    logger = get_logger(__name__)
    
    # Calculate sum of all specified elements
    if 'composition_sum' not in df.columns:
        df['composition_sum'] = df[REQUIRED_COMPOSITION_ELEMENTS].sum(axis=1)
    
    mask = df['composition_sum'] >= MAJOR_ELEMENT_THRESHOLD
    dropped_count = (~mask).sum()
    
    if dropped_count > 0:
        logger.warning(f"Dropped {dropped_count} rows: major element sum < {MAJOR_ELEMENT_THRESHOLD}")
    
    return df[mask]

def apply_ilr_transformation(df: pd.DataFrame) -> pd.DataFrame:
    """
    Apply ILR transformation to compositional data (Cu, Mg, Si, Zn, Mn).
    Uses the `compositional` package.
    """
    logger = get_logger(__name__)
    
    if len(df) == 0:
        logger.warning("Empty dataframe passed to ILR transformation.")
        return df

    # Prepare composition columns
    comp_cols = REQUIRED_COMPOSITION_ELEMENTS
    if not all(col in df.columns for col in comp_cols):
        raise ValueError(f"Missing composition columns for ILR: {comp_cols}")
    
    # Extract composition data
    comp_data = df[comp_cols].values
    
    # Ensure no zeros or negatives (ILR requires strictly positive)
    # Add a small epsilon if necessary
    epsilon = 1e-10
    comp_data = np.where(comp_data <= 0, epsilon, comp_data)
    
    # Normalize to ensure sum is 1 (robustness)
    comp_data = comp_data / comp_data.sum(axis=1, keepdims=True)
    
    # Use the compositional package for ILR transformation
    # The compositions class handles the transformation
    try:
        comp_obj = compositions(comp_data, label=comp_cols)
        ilr_data = comp_obj.ilr().data
    except Exception as e:
        logger.error(f"ILR transformation failed: {e}")
        raise

    # Create new column names for ILR features
    # ILR for D parts produces D-1 coordinates
    ilr_cols = [f'ilr_{i}' for i in range(ilr_data.shape[1])]
    
    # Add ILR features to dataframe
    for i, col in enumerate(ilr_cols):
        df[col] = ilr_data[:, i]
    
    logger.info(f"ILR transformation complete. Added {len(ilr_cols)} features.")
    return df

def run_cleaning_pipeline(raw_dir: Optional[str] = None, output_path: Optional[str] = None) -> Path:
    """
    Run the full data cleaning pipeline:
    1. Load raw data
    2. Validate schema
    3. Normalize units
    4. Verify measurement independence
    5. Filter monolithic alloys
    6. Check major element sum
    7. Apply ILR transformation
    8. Save final CSV
    """
    logger = get_logger(__name__)
    config = get_config()
    
    if raw_dir is None:
        raw_dir = str(Path(config.data_dir) / 'raw')
    if output_path is None:
        output_path = str(Path(config.data_dir) / 'processed' / 'filtered_alloys.csv')
    
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Define source paths
    source_paths = {
        'materials_project': str(Path(raw_dir) / 'materials_project_aluminum.json'),
        'nist': str(Path(raw_dir) / 'nist_aluminum.json'),
        'openml': str(Path(raw_dir) / 'openml_aluminum.json')
    }
    
    logger.info("Starting cleaning pipeline...")
    
    # 1. Load
    df = load_raw_data(source_paths)
    
    # 2. Validate
    df = validate_schema(df)
    
    # 3. Normalize
    df = normalize_units(df)
    
    # 4. Verify independence
    df = verify_measurement_independence(df)
    
    # 5. Filter monolithic
    df = filter_monolithic_alloys(df)
    
    # 6. Check major element sum
    df = check_major_element_sum(df)
    
    # 7. Apply ILR transformation
    df = apply_ilr_transformation(df)
    
    # 8. Save
    df.to_csv(output_path, index=False)
    logger.info(f"Pipeline complete. Saved {len(df)} records to {output_path}")
    
    if len(df) == 0:
        raise ValueError("CRITICAL: No valid entries found across all sources. Pipeline halted.")
    
    if len(df) < MIN_VALID_ENTRIES:
        raise ValueError(f"CRITICAL: Insufficient data ({len(df)} entries) for 5-fold cross-validation. Pipeline halted per spec Edge Cases.")
    
    return output_path

def main():
    """CLI entry point for cleaning pipeline."""
    logger = setup_logging()
    try:
        path = run_cleaning_pipeline()
        logger.info(f"Success: {path}")
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        raise

if __name__ == '__main__':
    main()
