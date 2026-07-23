"""
Physics calculations for stellar flare and exoplanet atmospheric retention.
Implements energy-limited escape model and XUV flux calculations.
"""
import logging
from typing import Optional
import numpy as np
import pandas as pd
import config

logger = logging.getLogger(__name__)

def calculate_quiescent_xuv(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate quiescent XUV luminosity (L_X) for each star.
    
    Primary: Uses Wright et al. (2018) relation if Rotation Period is available.
    Fallback: Uses fixed proxy if Rotation Period is missing.
    
    Args:
        df: DataFrame containing stellar parameters including 'bolometric_luminosity'
            and optionally 'rotation_period'.
            
    Returns:
        DataFrame with 'quiescent_L_X' column added (erg/s).
    """
    df = df.copy()
    
    # Check for rotation period availability
    has_rotation = 'rotation_period' in df.columns and not df['rotation_period'].isna().all()
    
    if has_rotation:
        logger.info("Calculating L_X using Wright et al. (2018) relation with rotation periods.")
        # Wright et al. (2018) relation: L_X/L_bol = 10^(-3.5) * (P_rot / 10 days)^(-2.7)
        # Constants from literature approximation
        P_rot = df['rotation_period'].astype(float)
        L_bol = df['bolometric_luminosity'].astype(float)
        
        # Avoid division by zero or negative values
        P_rot = P_rot.replace(0, np.nan)
        P_rot = P_rot.mask(P_rot <= 0, np.nan)
        
        # Calculate ratio
        ratio = 10**(-3.5) * (P_rot / 10.0)**(-2.7)
        df['quiescent_L_X'] = ratio * L_bol
        
        # Log fallback usage for missing rotation periods
        missing_rot = df['rotation_period'].isna().sum()
        if missing_rot > 0:
            logger.warning(f"{missing_rot} records missing rotation period; using fallback proxy.")
            fallback_mask = df['rotation_period'].isna()
            df.loc[fallback_mask, 'quiescent_L_X'] = 1e-4 * df.loc[fallback_mask, 'bolometric_luminosity']
    else:
        logger.warning("No rotation periods available. Using fixed proxy L_X = 10^-4 * L_bol.")
        L_bol = df['bolometric_luminosity'].astype(float)
        df['quiescent_L_X'] = 1e-4 * L_bol
        
    return df

def calculate_cumulative_flux(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate cumulative XUV flux (F_XUV) including quiescent and flare contributions.
    
    Formula: F_XUV = F_quiescent + sum(E_flare * f_XUV / (4 * pi * a^2))
    
    Args:
        df: DataFrame with 'quiescent_L_X', 'flare_energy', 'semi_major_axis', 
            and 'system_age'.
            
    Returns:
        DataFrame with 'cumulative_flux' column added (erg/s/cm^2).
    """
    df = df.copy()
    
    # Constants
    f_XUV = config.F_XUV  # Conversion factor for flare energy to XUV
    pi = np.pi
    
    # Quiescent flux at planet distance: F = L / (4 * pi * a^2)
    # Ensure units: L_X in erg/s, a in cm (assuming input is in AU or similar, convert if needed)
    # Assuming semi_major_axis is in AU, convert to cm: 1 AU = 1.496e13 cm
    AU_TO_CM = 1.496e13
    a_cm = df['semi_major_axis'].astype(float) * AU_TO_CM
    
    F_quiescent = df['quiescent_L_X'] / (4 * pi * a_cm**2)
    
    # Flare contribution: sum of (E_flare * f_XUV) / (4 * pi * a^2)
    # Assuming flare_energy is in erg
    if 'flare_energy' in df.columns:
        # If multiple flares per star are aggregated, flare_energy might be total or per event
        # Assuming 'flare_energy' here is the total integrated flare energy for the star
        E_total_XUV = df['flare_energy'].astype(float) * f_XUV
        F_flare = E_total_XUV / (4 * pi * a_cm**2)
    else:
        logger.warning("No flare_energy column found. Assuming zero flare contribution.")
        F_flare = 0.0
        
    df['cumulative_flux'] = F_quiescent + F_flare
    
    return df

def calculate_retention_fraction(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate atmospheric retention fraction using the energy-limited escape model.
    
    Formula: M_dot = (epsilon * pi * R_p^3 * F_XUV) / (G * M_p * K_tide)
    Retention = 1 - (integral(M_dot dt) / M_atm_initial)
    where M_atm_initial = 0.01 * M_p
    
    Args:
        df: DataFrame with 'cumulative_flux', 'radius', 'mass', 'system_age'.
            
    Returns:
        DataFrame with 'mass_loss_rate' and 'retention_fraction' columns.
    """
    df = df.copy()
    
    # Constants
    epsilon = config.EFFICIENCY  # Default 0.15
    G = config.G  # Gravitational constant
    K_tide = config.K_TIDE  # Default 1.0
    M_ATM_BASELINE = 0.01  # Fraction of planet mass
    
    # Convert units to CGS
    # Radius: assume input is in Earth Radii (R_earth = 6.371e8 cm) or similar
    # Mass: assume input is in Earth Masses (M_earth = 5.972e27 g)
    # If inputs are in solar units, adjust accordingly. Assuming Earth units for exoplanets.
    R_EARTH_CM = 6.371e8
    M_EARTH_G = 5.972e27
    
    R_p_cm = df['radius'].astype(float) * R_EARTH_CM
    M_p_g = df['mass'].astype(float) * M_EARTH_G
    age_gyr = df['system_age'].astype(float)
    age_s = age_gyr * 1e9 * 365.25 * 24 * 3600  # Convert Gyr to seconds
    
    F_XUV = df['cumulative_flux'].astype(float)
    
    # Mass loss rate: M_dot = (epsilon * pi * R_p^3 * F_XUV) / (G * M_p * K_tide)
    # Units: (dimensionless * cm^3 * erg/s/cm^2) / (cm^3/g/s^2 * g * dimensionless)
    # erg = g*cm^2/s^2, so numerator: g*cm^2/s^2 * cm / s^2 = g*cm^3/s^4 ? 
    # Let's check: F_XUV is erg/s/cm^2 = g/s^3.
    # Numerator: cm^3 * g/s^3 = g*cm^3/s^3
    # Denominator: (cm^3/g/s^2) * g = cm^3/s^2
    # Result: (g*cm^3/s^3) / (cm^3/s^2) = g/s. Correct.
    
    numerator = epsilon * np.pi * (R_p_cm**3) * F_XUV
    denominator = G * M_p_g * K_tide
    
    M_dot = numerator / denominator  # g/s
    
    # Integrate over time (assuming constant rate for simplicity, or linear decay if age varies)
    # Total mass lost = M_dot * age_s
    M_lost = M_dot * age_s
    
    # Initial atmosphere mass
    M_atm_initial = M_ATM_BASELINE * M_p_g
    
    # Retention fraction
    # Avoid division by zero
    M_atm_initial = M_atm_initial.replace(0, np.nan)
    retention = 1.0 - (M_lost / M_atm_initial)
    
    # Clamp retention to [0, 1] for physical plausibility in visualization (though negative means total loss)
    # We keep negative values to indicate total erosion, but flag them if needed.
    
    df['mass_loss_rate'] = M_dot
    df['retention_fraction'] = retention
    
    return df

def calculate_unphysical_flag(df: pd.DataFrame) -> pd.DataFrame:
    """
    Flag records where mass loss rate > 10% of planet mass per Gyr.
    
    Threshold: 0.10 * M_p / (1 Gyr)
    
    Args:
        df: DataFrame with 'mass_loss_rate', 'mass'.
            
    Returns:
        DataFrame with 'is_unphysical' boolean column.
    """
    df = df.copy()
    
    M_EARTH_G = 5.972e27
    GYR_TO_S = 1e9 * 365.25 * 24 * 3600
    
    M_p_g = df['mass'].astype(float) * M_EARTH_G
    threshold_rate = (0.10 * M_p_g) / GYR_TO_S
    
    M_dot = df['mass_loss_rate'].astype(float)
    
    df['is_unphysical'] = M_dot > threshold_rate
    
    return df

def apply_unphysical_filter(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filter out records flagged as unphysical.
    
    Args:
        df: DataFrame with 'is_unphysical' column.
            
    Returns:
        Filtered DataFrame.
    """
    logger.info(f"Filtering out {df['is_unphysical'].sum()} unphysical records.")
    return df[~df['is_unphysical']].reset_index(drop=True)

def validate_derived_columns(df: pd.DataFrame) -> bool:
    """
    Validate that derived columns contain no NaN values for valid inputs.
    
    Checks columns: 'cumulative_flux', 'mass_loss_rate', 'retention_fraction'.
    Raises ValueError if NaNs are found.
    
    Args:
        df: DataFrame with derived physics columns.
            
    Returns:
        True if validation passes.
            
    Raises:
        ValueError: If NaNs are detected in required derived columns.
    """
    derived_cols = ['cumulative_flux', 'mass_loss_rate', 'retention_fraction']
    missing_cols = [col for col in derived_cols if col not in df.columns]
    
    if missing_cols:
        logger.error(f"Missing derived columns: {missing_cols}")
        raise ValueError(f"Missing required derived columns: {missing_cols}")
        
    nan_counts = {col: df[col].isna().sum() for col in derived_cols}
    
    if any(count > 0 for count in nan_counts.values()):
        error_msg = "NaN values detected in derived columns:\n"
        for col, count in nan_counts.items():
            if count > 0:
                error_msg += f"  - {col}: {count} NaNs\n"
        logger.error(error_msg)
        raise ValueError("NaN values detected in derived columns. Check input data for missing values.")
        
    logger.info("Validation passed: No NaN values in derived columns.")
    return True

def run_physics_pipeline(input_path: str, output_path: str) -> None:
    """
    Execute the full physics pipeline: read, calculate, filter, validate, save.
    
    Args:
        input_path: Path to 'data/processed/merged_filtered.csv'.
        output_path: Path to write 'data/processed/derived_physics.csv'.
    """
    logger.info(f"Starting physics pipeline. Input: {input_path}, Output: {output_path}")
    
    # Read input
    df = pd.read_csv(input_path)
    logger.info(f"Read {len(df)} records from {input_path}")
    
    # Calculate physics
    df = calculate_quiescent_xuv(df)
    df = calculate_cumulative_flux(df)
    df = calculate_retention_fraction(df)
    
    # Flag and filter unphysical
    df = calculate_unphysical_flag(df)
    df = apply_unphysical_filter(df)
    
    # Validate derived columns (T026)
    validate_derived_columns(df)
    
    # Save output
    df.to_csv(output_path, index=False)
    logger.info(f"Pipeline complete. Saved {len(df)} valid records to {output_path}")

if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    run_physics_pipeline("data/processed/merged_filtered.csv", "data/processed/derived_physics.csv")
