import logging
from typing import Optional, Tuple, List, Dict, Any
import numpy as np
import pandas as pd
import config

logger = logging.getLogger(__name__)

def calculate_quiescent_xuv(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate quiescent XUV luminosity (L_X) based on rotation period or fallback proxy.
    
    Primary: Wright et al. (2018) relation if Rotation Period is available.
    Fallback: Fixed proxy L_X = 10^-4 * L_bol if Rotation Period is missing.
    
    Output unit: erg/s
    """
    df = df.copy()
    
    # Check if Rotation Period column exists
    if 'Rotation Period' in df.columns:
        # Convert to float, handling potential non-numeric values
        rot_period = pd.to_numeric(df['Rotation Period'], errors='coerce')
        
        # Identify rows with valid rotation periods
        valid_rot_mask = ~rot_period.isna() & (rot_period > 0)
        
        # Wright et al. (2018) relation: L_X/L_bol = 10^-3.5 * (P_rot/10)^-2.7
        # L_X = L_bol * 10^-3.5 * (P_rot/10)^-2.7
        # Note: L_bol is expected to be in erg/s in the input dataframe
        
        if 'L_bol' not in df.columns:
            logger.warning("L_bol column not found. Cannot calculate L_X using rotation period.")
            df['L_X'] = np.nan
        else:
            L_bol = df['L_bol'].astype(float)
            
            # Calculate ratio
            ratio = np.power(10, -3.5) * np.power(rot_period[valid_rot_mask] / 10.0, -2.7)
            L_X_valid = L_bol[valid_rot_mask] * ratio
            
            df.loc[valid_rot_mask, 'L_X'] = L_X_valid
            df.loc[~valid_rot_mask, 'L_X'] = np.nan
            
            # Log fallback cases
            fallback_count = (~valid_rot_mask).sum()
            if fallback_count > 0:
                logger.warning(f"Rotation period missing or invalid for {fallback_count} rows. Using fallback proxy.")
    else:
        logger.warning("Rotation Period column missing. Using fallback proxy for all rows.")
        fallback_count = len(df)
    
    # Apply fallback for missing/NaN values
    fallback_mask = df['L_X'].isna()
    if fallback_mask.any():
        # Fallback: L_X = 10^-4 * L_bol
        if 'L_bol' in df.columns:
            df.loc[fallback_mask, 'L_X'] = 1e-4 * df.loc[fallback_mask, 'L_bol'].astype(float)
            logger.info(f"Applied fallback L_X = 10^-4 * L_bol for {fallback_mask.sum()} rows.")
        else:
            logger.error("L_bol column missing. Cannot apply fallback L_X calculation.")
            # Leave as NaN, will be handled later or cause failure downstream
    
    return df

def calculate_cumulative_flux(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate cumulative XUV flux: F_XUV = F_quiescent + sum(flare_contributions)
    
    F_quiescent = L_X / (4 * pi * a^2)
    Flare contribution = E_flare * f_XUV / (4 * pi * a^2)
    
    Where:
    - L_X: Quiescent XUV luminosity (erg/s)
    - a: Semi-major axis (cm)
    - E_flare: Flare energy (erg)
    - f_XUV: Conversion factor (default from config)
    
    Returns DataFrame with 'cumulative_flux' column in erg/s/cm^2.
    """
    df = df.copy()
    
    # Ensure required columns exist
    required_cols = ['L_X', 'semi_major_axis', 'flare_count', 'total_flare_energy']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns for cumulative flux calculation: {missing_cols}")
    
    # Constants
    pi = np.pi
    f_XUV = config.f_XUV  # Default from config.py
    
    # Convert semi_major_axis to cm if in AU (common unit)
    # Assuming input is in AU, convert to cm: 1 AU = 1.496e13 cm
    # If already in cm, this conversion will be wrong, so we assume AU based on typical exoplanet data
    a_cm = df['semi_major_axis'].astype(float) * 1.496e13
    
    # Calculate quiescent flux: F_quiescent = L_X / (4 * pi * a^2)
    F_quiescent = df['L_X'].astype(float) / (4 * pi * a_cm**2)
    
    # Calculate total flare contribution
    # Total flare energy is sum of all flare energies for the star
    # F_flare_total = (E_flare_total * f_XUV) / (4 * pi * a^2)
    E_flare_total = df['total_flare_energy'].astype(float)
    F_flare_total = (E_flare_total * f_XUV) / (4 * pi * a_cm**2)
    
    # Cumulative flux
    df['cumulative_flux'] = F_quiescent + F_flare_total
    
    logger.info(f"Cumulative XUV flux calculated for {len(df)} systems.")
    
    return df

def calculate_retention_fraction(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate atmospheric retention fraction using energy-limited escape model.
    
    Instantaneous mass loss rate: dM/dt = (epsilon * pi * R_p^3 * F_XUV) / (G * M_p * K_tide)
    
    Integrated mass loss over system age: delta_M = dM/dt * age
    
    Retention = 1 - (delta_M / M_atm_initial)
    where M_atm_initial = 0.01 * M_p (1% of planet mass)
    
    Returns DataFrame with 'mass_loss_rate' (g/s), 'total_mass_loss' (g), and 'retention_fraction' (0-1).
    """
    df = df.copy()
    
    # Required columns
    required_cols = ['cumulative_flux', 'radius', 'mass', 'system_age']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns for retention calculation: {missing_cols}")
    
    # Constants from config
    epsilon = config.eta  # Efficiency
    G = config.G  # Gravitational constant in cgs
    K_tide = config.K_tide
    
    # Convert units to cgs
    # radius: Jupiter radii or Earth radii? Assume Earth radii (R_earth = 6.371e8 cm)
    # mass: Earth masses or Jupiter masses? Assume Earth masses (M_earth = 5.972e27 g)
    # If data is in different units, conversion factors need to be adjusted
    
    # Assuming input radius is in Earth radii, mass in Earth masses
    R_p_cm = df['radius'].astype(float) * 6.371e8  # R_earth in cm
    M_p_g = df['mass'].astype(float) * 5.972e27   # M_earth in g
    age_gyr = df['system_age'].astype(float)
    age_s = age_gyr * 1e9 * 365.25 * 24 * 3600  # Convert Gyr to seconds
    
    # Calculate instantaneous mass loss rate: dM/dt
    # dM/dt = (epsilon * pi * R_p^3 * F_XUV) / (G * M_p * K_tide)
    numerator = epsilon * np.pi * (R_p_cm**3) * df['cumulative_flux'].astype(float)
    denominator = G * M_p_g * K_tide
    dM_dt = numerator / denominator  # g/s
    
    # Total mass loss over system age (assuming constant rate)
    total_mass_loss = dM_dt * age_s  # g
    
    # Initial atmospheric mass (1% of planet mass)
    M_atm_initial = 0.01 * M_p_g
    
    # Retention fraction
    # Retention = 1 - (total_mass_loss / M_atm_initial)
    # Clamp to [0, 1] to handle cases where loss > initial
    retention = 1.0 - (total_mass_loss / M_atm_initial)
    retention = retention.clip(lower=0.0, upper=1.0)
    
    df['mass_loss_rate'] = dM_dt
    df['total_mass_loss'] = total_mass_loss
    df['retention_fraction'] = retention
    
    logger.info(f"Retention fraction calculated for {len(df)} systems.")
    
    return df

def calculate_unphysical_flag(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate a boolean flag for unphysical mass loss rates.
    
    Flag is True if mass_loss_rate > 10% of planet mass per Gyr.
    Threshold: 0.1 * M_p / (1 Gyr) = 0.1 * M_p / (3.154e16 s)
    
    Returns DataFrame with 'is_unphysical' column.
    """
    df = df.copy()
    
    if 'mass_loss_rate' not in df.columns or 'mass' not in df.columns:
        raise ValueError("mass_loss_rate and mass columns required for unphysical flag calculation.")
    
    # Constants
    M_p_g = df['mass'].astype(float) * 5.972e27  # Assuming Earth masses
    threshold_per_gyr = 0.1 * M_p_g / (1e9 * 365.25 * 24 * 3600)  # g/s
    
    # Flag rows where mass loss rate exceeds threshold
    df['is_unphysical'] = df['mass_loss_rate'] > threshold_per_gyr
    
    unphysical_count = df['is_unphysical'].sum()
    logger.info(f"Identified {unphysical_count} systems with unphysical mass loss rates (>10% M_p/Gyr).")
    
    return df

def apply_unphysical_filter(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filter out rows where is_unphysical is True.
    
    Returns filtered DataFrame with only valid systems.
    """
    if 'is_unphysical' not in df.columns:
        raise ValueError("is_unphysical column required. Run calculate_unphysical_flag first.")
    
    initial_count = len(df)
    df_filtered = df[~df['is_unphysical']].copy()
    filtered_count = initial_count - len(df_filtered)
    
    logger.info(f"Filtered out {filtered_count} unphysical systems. {len(df_filtered)} remain.")
    
    return df_filtered

def validate_derived_columns(df: pd.DataFrame) -> Tuple[pd.DataFrame, bool]:
    """
    Validate that derived columns contain no NaN values for valid inputs.
    
    Checks columns: 'cumulative_flux', 'mass_loss_rate', 'retention_fraction'
    
    Returns:
        Tuple of (DataFrame, bool) where bool is True if validation passes.
        
    Raises:
        ValueError if NaN values are found in derived columns.
    """
    required_derived_cols = ['cumulative_flux', 'mass_loss_rate', 'retention_fraction']
    missing_cols = [col for col in required_derived_cols if col not in df.columns]
    
    if missing_cols:
        raise ValueError(f"Missing derived columns for validation: {missing_cols}")
    
    nan_found = False
    for col in required_derived_cols:
        nan_count = df[col].isna().sum()
        if nan_count > 0:
            logger.error(f"NaN values found in {col}: {nan_count} rows.")
            nan_found = True
    
    if nan_found:
        raise ValueError("Validation failed: NaN values found in derived columns.")
    
    logger.info("Validation passed: No NaN values in derived columns.")
    return df, True

def run_physics_pipeline(input_path: str, output_path: str) -> pd.DataFrame:
    """
    Run the complete physics pipeline:
    1. Read merged_filtered.csv
    2. Calculate quiescent XUV
    3. Calculate cumulative flux
    4. Calculate retention fraction
    5. Flag and filter unphysical systems
    6. Validate derived columns
    7. Write to derived_physics.csv
    
    Args:
        input_path: Path to data/processed/merged_filtered.csv
        output_path: Path to data/processed/derived_physics.csv
        
    Returns:
        Final processed DataFrame
    """
    # Read input
    df = pd.read_csv(input_path)
    logger.info(f"Read {len(df)} rows from {input_path}")
    
    # Step 1: Quiescent XUV
    df = calculate_quiescent_xuv(df)
    
    # Step 2: Cumulative Flux
    df = calculate_cumulative_flux(df)
    
    # Step 3: Retention Fraction
    df = calculate_retention_fraction(df)
    
    # Step 4: Unphysical Flag
    df = calculate_unphysical_flag(df)
    
    # Step 5: Filter Unphysical
    df = apply_unphysical_filter(df)
    
    # Step 6: Validate Derived Columns (T026)
    df, valid = validate_derived_columns(df)
    if not valid:
        raise RuntimeError("Physics pipeline failed validation.")
    
    # Prepare output columns
    output_cols = ['host_star_id', 'cumulative_flux', 'mass_loss_rate', 'retention_fraction', 'is_valid']
    # Add is_valid based on is_unphysical (inverted)
    df['is_valid'] = ~df['is_unphysical']
    
    # Select output columns (ensure they exist)
    available_cols = [col for col in output_cols if col in df.columns]
    df_output = df[available_cols].copy()
    
    # Write output
    df_output.to_csv(output_path, index=False)
    logger.info(f"Wrote {len(df_output)} rows to {output_path}")
    
    return df_output

if __name__ == "__main__":
    import logging
    from pathlib import Path
    
    logging.basicConfig(level=logging.INFO)
    
    input_file = "data/processed/merged_filtered.csv"
    output_file = "data/processed/derived_physics.csv"
    
    if Path(input_file).exists():
        run_physics_pipeline(input_file, output_file)
    else:
        logger.error(f"Input file not found: {input_file}")
        raise FileNotFoundError(f"Input file not found: {input_file}")
