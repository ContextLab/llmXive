import os
import sys
import pandas as pd
from typing import List, Dict, Any, Optional
from utils.logging import get_logger
from utils.unit_utils import normalize_to_mpa

logger = get_logger(__name__)

def preprocess_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filters the raw dataset to:
    1. Single-phase alloys (based on phase column or heuristic)
    2. Room temperature measurements (20-25°C)
    3. Removes rows with missing yield strength values.
    
    Args:
        df: Raw DataFrame.
    
    Returns:
        Filtered DataFrame.
    """
    logger.info(f"Starting preprocessing on {len(df)} rows")
    
    # 1. Handle missing yield strength
    # Assume column name is 'yield_strength' or similar. 
    # We'll look for a column that likely contains YS.
    ys_col = None
    possible_ys_cols = ['yield_strength', 'YS', 'yield_strength_mpa', 'yield_strength_mpA']
    for col in possible_ys_cols:
        if col in df.columns:
            ys_col = col
            break
    
    if ys_col is None:
        # Fallback: try to find any column with 'yield' in name
        cols = [c for c in df.columns if 'yield' in c.lower()]
        if cols:
            ys_col = cols[0]
        else:
            raise ValueError("Could not identify yield strength column in dataset.")
    
    # Drop rows where yield strength is missing
    initial_count = len(df)
    df = df.dropna(subset=[ys_col])
    logger.info(f"Dropped {initial_count - len(df)} rows with missing {ys_col}")
    
    # 2. Filter by Temperature (Room Temp: 20-25°C)
    # Look for a temperature column
    temp_col = None
    possible_temp_cols = ['temperature', 'temp', 'test_temp', 'temperature_celsius']
    for col in possible_temp_cols:
        if col in df.columns:
            temp_col = col
            break
    
    if temp_col:
        logger.info(f"Filtering by temperature column: {temp_col} (20-25°C)")
        # Ensure numeric
        df[temp_col] = pd.to_numeric(df[temp_col], errors='coerce')
        # Filter range
        df = df[(df[temp_col] >= 20) & (df[temp_col] <= 25)]
        logger.info(f"Filtered to {len(df)} rows within 20-25°C range")
    else:
        logger.warning("No temperature column found. Skipping temperature filter.")
    
    # 3. Filter Single-Phase
    # Look for a phase column
    phase_col = None
    possible_phase_cols = ['phase', 'phase_type', 'microstructure']
    for col in possible_phase_cols:
        if col in df.columns:
            phase_col = col
            break
    
    if phase_col:
        logger.info(f"Filtering by phase column: {phase_col} (single-phase)")
        # Heuristic: keep rows where phase contains 'FCC', 'BCC', 'HCP' or 'Single'
        # and NOT 'Multi', 'Complex', 'Amorphous'
        single_phase_keywords = ['FCC', 'BCC', 'HCP', 'Single', 'solid solution']
        exclude_keywords = ['Multi', 'Complex', 'Amorphous', 'Glass']
        
        mask = df[phase_col].astype(str).apply(lambda x: any(k in x for k in single_phase_keywords))
        mask &= ~df[phase_col].astype(str).apply(lambda x: any(k in x for k in exclude_keywords))
        
        df = df[mask]
        logger.info(f"Filtered to {len(df)} single-phase rows")
    else:
        logger.warning("No phase column found. Skipping phase filter.")
    
    logger.info(f"Preprocessing complete. Remaining rows: {len(df)}")
    return df

def normalize_units(df: pd.DataFrame) -> pd.DataFrame:
    """
    Converts yield strength to MPa if necessary.
    Assumes the column is named 'yield_strength' after preprocessing.
    
    Args:
        df: Processed DataFrame.
    
    Returns:
        DataFrame with yield strength in MPa.
    """
    # Find the yield strength column (might be named differently)
    ys_col = None
    possible_ys_cols = ['yield_strength', 'YS', 'yield_strength_mpa']
    for col in possible_ys_cols:
        if col in df.columns:
            ys_col = col
            break
    
    if ys_col is None:
        raise ValueError("Yield strength column not found for normalization.")
    
    # Check for a unit column
    unit_col = None
    for col in df.columns:
        if 'unit' in col.lower() or 'mpa' in col.lower() or 'psi' in col.lower():
            unit_col = col
            break
    
    if unit_col:
        logger.info(f"Normalizing units using column: {unit_col}")
        df[ys_col] = df.apply(lambda row: normalize_to_mpa(row[ys_col], row[unit_col]), axis=1)
        # Drop unit column if we processed it
        # df = df.drop(columns=[unit_col]) 
    else:
        logger.info("No unit column found. Assuming data is already in MPa.")
    
    # Ensure the column is named consistently for downstream steps
    if ys_col != 'yield_strength':
        df['yield_strength'] = df[ys_col]
        # Optional: drop old column if desired, but keeping it might be safer
        # df = df.drop(columns=[ys_col])
    
    return df

def main():
    """
    Entry point for testing preprocessing if needed.
    """
    logger.info("Preprocess module loaded. Use via pipeline.")

if __name__ == "__main__":
    main()
