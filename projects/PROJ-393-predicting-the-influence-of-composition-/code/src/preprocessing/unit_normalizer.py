"""
Unit Normalizer for Heusler Alloy Hysteresis Data.

Standardizes coercivity (Hc) to Oersted (Oe) and saturation magnetization (Ms)
to emu/gram (emu/g) based on project specifications.

Supported conversions:
- Coercivity (Hc): Oe, kOe, A/m
- Saturation Magnetization (Ms): emu/g, A·m²/kg, Am²/kg, Tesla (converted via density if available, else assumes standard units)

Note: This module assumes the input DataFrame contains columns 'coercivity' (or 'Hc')
and 'saturation_magnetization' (or 'Ms') along with their respective unit columns
(e.g., 'coercivity_unit', 'ms_unit'). If unit columns are missing, it assumes
the input is already in the target unit (Oe, emu/g) and logs a warning.
"""

import logging
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Optional, Tuple

# Configure logging for this module
logger = logging.getLogger(__name__)

# Conversion factors to target units (Oe for Hc, emu/g for Ms)
# 1 kOe = 1000 Oe
# 1 A/m = 0.012566370614 Oe (approx 4*pi/1000)
# 1 emu/g = 1 A·m²/kg (SI equivalent for specific magnetic moment)
# Note: Converting Tesla to emu/g requires density. Since density is not always
# available in the raw dataset, we will only convert explicit magnetic field units
# and specific magnetization units. If 'T' is found for Ms without density, we log a warning.

H_TO_OE = {
    'oe': 1.0,
    'oersted': 1.0,
    'ko e': 1000.0,
    'koe': 1000.0,
    'a/m': 0.012566370614359172,  # 4 * pi / 1000
    'a m^-1': 0.012566370614359172,
}

MS_TO_EMU_G = {
    'emu/g': 1.0,
    'emu g-1': 1.0,
    'emu g^-1': 1.0,
    'a m^2/kg': 1.0,
    'a m2/kg': 1.0,
    'am2/kg': 1.0,
    'a m^2 g^-1': 1000.0,  # If unit is A m^2 / g (rare but possible)
    'a m^2/g': 1000.0,
}

# Columns to look for
H_C_COLUMNS = ['coercivity', 'Hc', 'h_c', 'coercive_force']
MS_COLUMNS = ['saturation_magnetization', 'Ms', 'm_s', 'sigma', 'saturation']
H_UNIT_COLUMNS = ['coercivity_unit', 'Hc_unit', 'h_c_unit', 'unit_hc']
MS_UNIT_COLUMNS = ['ms_unit', 'Ms_unit', 'm_s_unit', 'unit_ms', 'sigma_unit']

def normalize_unit(value: float, unit: str, conversion_map: dict, target_name: str) -> float:
    """
    Normalize a single value given its unit to the target unit.

    Args:
        value: Numeric value
        unit: String unit (case-insensitive)
        conversion_map: Dict mapping unit strings to conversion factors
        target_name: Name of target unit for logging

    Returns:
        Normalized value
    """
    if pd.isna(value) or pd.isna(unit):
        return np.nan

    unit_clean = str(unit).strip().lower().replace(' ', '')
    
    if unit_clean in conversion_map:
        return float(value) * conversion_map[unit_clean]
    else:
        # Check for common variations
        # e.g., "kOe" vs "ko e"
        unit_clean = unit_clean.replace('oersted', 'oe')
        if unit_clean in conversion_map:
            return float(value) * conversion_map[unit_clean]
        
        logger.warning(f"Unknown unit '{unit}' for {target_name}. Assuming input is already in target units (Oe/emu/g).")
        return float(value)

def normalize_coercivity(df: pd.DataFrame) -> pd.DataFrame:
    """
    Standardize coercivity column to Oersted (Oe).
    
    Args:
        df: Input DataFrame
        
    Returns:
        DataFrame with 'coercivity_oe' column added
    """
    df = df.copy()
    
    # Identify source columns
    h_col = None
    unit_col = None
    
    for col in H_C_COLUMNS:
        if col in df.columns:
            h_col = col
            break
    
    for col in H_UNIT_COLUMNS:
        if col in df.columns:
            unit_col = col
            break
    
    if h_col is None:
        logger.warning("No coercivity column found. Skipping coercivity normalization.")
        df['coercivity_oe'] = np.nan
        return df

    if unit_col is None:
        logger.warning(f"Unit column for coercivity not found. Assuming all values in '{h_col}' are already in Oe.")
        df['coercivity_oe'] = pd.to_numeric(df[h_col], errors='coerce')
    else:
        # Apply conversion row by row
        def convert_row(row):
            val = row[h_col]
            unit = row[unit_col] if unit_col else None
            if pd.isna(val):
                return np.nan
            if pd.isna(unit):
                logger.warning(f"Missing unit for coercivity value {val}. Assuming Oe.")
                return float(val)
            return normalize_unit(val, unit, H_TO_OE, "Coercivity")
        
        df['coercivity_oe'] = df.apply(convert_row, axis=1)
    
    return df

def normalize_saturation_magnetization(df: pd.DataFrame) -> pd.DataFrame:
    """
    Standardize saturation magnetization column to emu/gram (emu/g).
    
    Args:
        df: Input DataFrame
        
    Returns:
        DataFrame with 'saturation_magnetization_emu_g' column added
    """
    df = df.copy()
    
    # Identify source columns
    ms_col = None
    unit_col = None
    
    for col in MS_COLUMNS:
        if col in df.columns:
            ms_col = col
            break
    
    for col in MS_UNIT_COLUMNS:
        if col in df.columns:
            unit_col = col
            break
    
    if ms_col is None:
        logger.warning("No saturation magnetization column found. Skipping Ms normalization.")
        df['saturation_magnetization_emu_g'] = np.nan
        return df

    if unit_col is None:
        logger.warning(f"Unit column for saturation magnetization not found. Assuming all values in '{ms_col}' are already in emu/g.")
        df['saturation_magnetization_emu_g'] = pd.to_numeric(df[ms_col], errors='coerce')
    else:
        def convert_row(row):
            val = row[ms_col]
            unit = row[unit_col] if unit_col else None
            if pd.isna(val):
                return np.nan
            if pd.isna(unit):
                logger.warning(f"Missing unit for Ms value {val}. Assuming emu/g.")
                return float(val)
            
            unit_str = str(unit).strip().lower().replace(' ', '')
            
            # Special handling for Tesla (T) if density is available
            if 't' in unit_str and 'density' in df.columns:
                logger.warning("Tesla unit detected. Conversion to emu/g requires density. Skipping conversion for this row.")
                return np.nan
            elif 't' in unit_str:
                logger.warning("Tesla unit detected but density column missing. Cannot convert to emu/g. Skipping conversion for this row.")
                return np.nan
            
            return normalize_unit(val, unit, MS_TO_EMU_G, "Saturation Magnetization")
        
        df['saturation_magnetization_emu_g'] = df.apply(convert_row, axis=1)
    
    return df

def standardize_units(df: pd.DataFrame) -> pd.DataFrame:
    """
    Main entry point to standardize both coercivity and saturation magnetization.
    
    Args:
        df: Input DataFrame with raw hysteresis data
        
    Returns:
        DataFrame with normalized columns 'coercivity_oe' and 'saturation_magnetization_emu_g'
    """
    logger.info("Starting unit normalization for hysteresis parameters.")
    
    df = normalize_coercivity(df)
    df = normalize_saturation_magnetization(df)
    
    logger.info(f"Normalization complete. Created columns: coercivity_oe, saturation_magnetization_emu_g")
    
    return df

def main():
    """
    CLI entry point for unit normalization.
    Expects input CSV and output CSV paths as arguments, or uses defaults.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Standardize hysteresis units to Oe and emu/g")
    parser.add_argument("--input", type=str, default="data/processed/alloys_raw.csv",
                        help="Path to input CSV with raw data")
    parser.add_argument("--output", type=str, default="data/processed/alloys_units_normalized.csv",
                        help="Path to output CSV with normalized units")
    args = parser.parse_args()
    
    input_path = Path(args.input)
    output_path = Path(args.output)
    
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        return 1
    
    logger.info(f"Loading data from {input_path}")
    df = pd.read_csv(input_path)
    
    logger.info(f"Loaded {len(df)} rows")
    
    df_normalized = standardize_units(df)
    
    logger.info(f"Saving normalized data to {output_path}")
    df_normalized.to_csv(output_path, index=False)
    
    logger.info("Done.")
    return 0

if __name__ == "__main__":
    # Setup basic logging if not already configured
    logging.basicConfig(level=logging.INFO)
    exit(main())
