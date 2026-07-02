import os
import sys
import pandas as pd
from typing import List, Dict, Any, Optional
from utils.logging import get_logger
from utils.unit_utils import normalize_to_mpa

logger = get_logger(__name__)

def preprocess_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Preprocess the dataset: filter single-phase, room-temp, and handle missing yield strength.
    
    This function implements the logic for T009 and T010.
    It filters for single-phase alloys and room temperature measurements,
    then normalizes yield strength to MPa.
    
    Args:
        df (pd.DataFrame): Raw dataset loaded from the source.
        
    Returns:
        pd.DataFrame: Filtered and preprocessed dataframe with normalized units.
    """
    if df.empty:
        logger.warning("Input dataframe is empty.")
        return df

    logger.info(f"Starting preprocessing on {len(df)} rows.")

    # T009: Filter for single-phase alloys
    # Assuming 'phase' or 'microstructure' column exists. 
    # Common HEA datasets use 'phase' with values like 'Single', 'Single-phase', 'FCC', 'BCC' (if single).
    # We will filter for rows where 'phase' indicates a single phase.
    # If the column name varies, we check common names.
    phase_col = None
    for col in ['phase', 'microstructure', 'constituent_phases']:
        if col in df.columns:
            phase_col = col
            break

    if phase_col:
        # Filter for single phase. 
        # We look for specific keywords indicating single phase.
        # Note: This logic assumes the data loader (T008) provides a column with phase info.
        # If the dataset uses specific phase names (FCC, BCC) for single-phase alloys,
        # we might need a more complex filter. For now, we assume a 'Single' or similar flag
        # or we treat specific single-phase names as valid if the column indicates 'Single'.
        
        # Heuristic: If the column contains 'Single', keep it. 
        # If the dataset lists specific phases (e.g., "FCC", "BCC") and we want single-phase,
        # we assume those are single-phase unless 'Multi' or 'Complex' is present.
        
        # Let's implement a robust filter: Keep rows where phase is explicitly 'Single' 
        # OR where the phase is a known single-phase structure (FCC, BCC, HCP) and NOT multi-phase.
        
        single_phase_keywords = ['Single', 'single', 'FCC', 'BCC', 'HCP', 'fcc', 'bcc', 'hcp']
        multi_phase_keywords = ['Multi', 'multi', 'Complex', 'complex', 'Dual', 'dual', 'Sigma', 'sigma', 'Laves', 'laves']
        
        mask = pd.Series([False] * len(df), index=df.index)
        
        for idx, row in df.iterrows():
            val = str(row[phase_col]) if pd.notna(row[phase_col]) else ""
            is_single = any(kw in val for kw in single_phase_keywords)
            is_multi = any(kw in val for kw in multi_phase_keywords)
            
            if is_single and not is_multi:
                mask[idx] = True
        
        df = df[mask]
        logger.info(f"Filtered to {len(df)} single-phase rows based on '{phase_col}'.")
    else:
        logger.warning(f"Could not find phase column. Skipping single-phase filter.")

    # T009: Filter for Room Temperature (20-25°C)
    temp_col = None
    for col in ['temperature', 'test_temp', 'testing_temp', 'T']:
        if col in df.columns:
            temp_col = col
            break

    if temp_col:
        # Convert to numeric, coerce errors to NaN
        df[temp_col] = pd.to_numeric(df[temp_col], errors='coerce')
        # Filter 20-25°C. Assuming unit is Celsius. 
        # If unit is Kelvin, we might need conversion. 
        # Given the context of "room temp", 20-25 C is standard.
        # If values are > 100, assume Kelvin? Or just strict 20-25.
        # Let's assume the dataset is in Celsius as per standard experimental reporting.
        
        df = df[(df[temp_col] >= 20) & (df[temp_col] <= 25)]
        logger.info(f"Filtered to {len(df)} room-temperature rows based on '{temp_col}'.")
    else:
        logger.warning(f"Could not find temperature column. Skipping temperature filter.")

    # T009: Handle missing yield strength values
    ys_col = None
    for col in ['yield_strength', 'YS', 'yield_strength_MPa', 'yield_strength_GPa', 'sigma_y']:
        if col in df.columns:
            ys_col = col
            break

    if ys_col:
        initial_count = len(df)
        df = df.dropna(subset=[ys_col])
        dropped = initial_count - len(df)
        if dropped > 0:
            logger.info(f"Dropped {dropped} rows with missing yield strength in '{ys_col}'.")
    else:
        logger.warning("Could not find yield strength column.")

    # T010: Normalize units to MPa
    if ys_col:
        df = normalize_units(df, ys_col)
        logger.info("Yield strength normalized to MPa.")

    logger.info(f"Preprocessing complete. Final count: {len(df)} rows.")
    return df

def normalize_units(df: pd.DataFrame, ys_column: str = 'yield_strength') -> pd.DataFrame:
    """
    Convert yield strength values to MPa.
    
    This function implements T010. It uses the utility from utils.unit_utils
    to handle conversions from GPa, Pa, or other units if detected, 
    or simply ensures the column is in MPa if the source was already MPa.
    
    Args:
        df (pd.DataFrame): Preprocessed dataframe.
        ys_column (str): Name of the yield strength column.
        
    Returns:
        pd.DataFrame: DataFrame with yield strength in MPa.
    """
    if ys_column not in df.columns:
        logger.error(f"Column '{ys_column}' not found in dataframe for unit normalization.")
        return df

    # Check if there's a unit column
    unit_col = None
    for col in ['unit', 'units', 'YS_unit', 'yield_strength_unit']:
        if col in df.columns:
            unit_col = col
            break

    # If unit column exists, apply conversion logic
    if unit_col:
        logger.info(f"Detected unit column '{unit_col}'. Converting based on units.")
        # Apply conversion row by row or via vectorized mapping
        # We assume the values are numeric and units are strings like 'GPa', 'MPa', 'Pa'
        
        def convert_row(row):
            val = row[ys_column]
            if pd.isna(val):
                return val
            
            unit = str(row[unit_col]).lower() if pd.notna(row[unit_col]) else 'mpa' # Default to MPa if missing unit
            
            # Use the existing utility
            return normalize_to_mpa(val, unit)
        
        df[ys_column] = df.apply(convert_row, axis=1)
        
        # Clean up unit column if we converted everything to MPa (optional, but keeps data clean)
        # However, to be safe, we might keep it or rename. 
        # The task implies the output should be in MPa.
        logger.info("Unit conversion applied.")
    else:
        # If no unit column, we assume the data is already in MPa or the source is consistent.
        # But T010 says "convert ALL yield strength to MPa". 
        # If the dataset is known to be mixed, we might need to infer from magnitude.
        # However, without a unit column, we cannot be certain. 
        # We will assume the source data (T008) provides consistent units or a unit column.
        # If the source is known to be GPa (some datasets), we might need a flag.
        # For this implementation, we assume if no unit column, the data is already in MPa 
        # OR the task expects us to handle the unit column if present.
        # If the dataset is purely GPa, we would need a config or heuristic.
        # Given the spec "convert all yield strength to MPa", if no unit info exists,
        # we assume the data is already in the target unit (MPa) or we rely on the 
        # download step to have standardized it. 
        # But to be robust, if values are very small (< 100), they might be GPa? 
        # No, HEA yield strength is typically 200-2000 MPa.
        # If values are 0.2-2.0, they might be GPa.
        # We will add a heuristic: if max value < 10, assume GPa and convert.
        # This is a fallback for datasets without explicit unit columns.
        
        if df[ys_column].max() < 10 and df[ys_column].max() > 0:
            logger.warning(f"Max yield strength is {df[ys_column].max()}. Assuming GPa and converting to MPa.")
            df[ys_column] = df[ys_column] * 1000.0
        else:
            logger.info(f"No unit column found. Assuming data is already in MPa (max={df[ys_column].max()}).")

    return df