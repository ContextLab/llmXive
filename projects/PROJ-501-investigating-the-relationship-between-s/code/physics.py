import logging
from typing import Optional
import numpy as np
import pandas as pd
import config

logger = logging.getLogger(__name__)

def calculate_quiescent_xuv(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate quiescent X-ray luminosity (L_X) for each star.
    
    PRIMARY: Wright et al. (2018) relation if Rotation Period is available:
    L_X / L_bol = 10^(-3.5) * (P_rot / 10 days)^(-2.7)
    
    FALLBACK: If Rotation Period is missing, use fixed proxy:
    L_X = 10^(-4) * L_bol
    
    Output is in erg/s.
    """
    df = df.copy()
    
    # Ensure L_bol is in erg/s (if in solar luminosities, convert)
    # Assuming L_bol in the dataset is in erg/s. If in L_sun, multiply by 3.828e33
    if 'L_bol' in df.columns:
        # Check if values look like solar units (order of magnitude ~1) vs erg/s (~1e33)
        if df['L_bol'].max() < 100.0:
            logger.warning("Assuming L_bol is in solar units, converting to erg/s.")
            df['L_bol_erg'] = df['L_bol'] * 3.828e33
        else:
            df['L_bol_erg'] = df['L_bol']
    else:
        raise ValueError("Column 'L_bol' is missing from the input DataFrame.")
    
    if 'Rotation Period' in df.columns and not df['Rotation Period'].isna().all():
        logger.info("Using Rotation Period for quiescent XUV calculation (Wright et al. 2018).")
        # L_X / L_bol = 10^(-3.5) * (P_rot / 10)^(-2.7)
        # L_X = L_bol * 10^(-3.5) * (P_rot / 10)^(-2.7)
        p_rot = df['Rotation Period']
        ratio = (10 ** -3.5) * ((p_rot / 10.0) ** -2.7)
        df['L_X_quiescent'] = df['L_bol_erg'] * ratio
        
        # Log warnings for rows where P_rot was NaN but others were used
        nan_mask = df['Rotation Period'].isna()
        if nan_mask.any():
            logger.warning(f"{nan_mask.sum()} rows missing Rotation Period; using fallback for these.")
            # Apply fallback for NaN rows
            fallback_ratio = 10 ** -4
            df.loc[nan_mask, 'L_X_quiescent'] = df.loc[nan_mask, 'L_bol_erg'] * fallback_ratio
    else:
        logger.warning("Rotation Period column missing or all NaN. Using fallback L_X = 10^-4 * L_bol for all rows.")
        df['L_X_quiescent'] = df['L_bol_erg'] * (10 ** -4)
    
    return df

def calculate_cumulative_flux(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute cumulative XUV flux (F_XUV) at the planet's orbital distance.
    
    Formula: F_XUV = F_quiescent + sum(flare_contributions)
    
    Where:
    - F_quiescent = L_X_quiescent / (4 * pi * a^2)
    - Flare contribution = (E_flare * f_XUV) / (4 * pi * a^2)
    
    Inputs:
    - df: DataFrame with columns 'L_X_quiescent' (erg/s), 'semi_major_axis' (cm or AU?),
          and potentially a list of flare energies or a pre-aggregated flare energy sum.
    
    Assumption: The input `df` comes from `merged_filtered.csv` or a similar intermediate.
    If flare data is in a separate long-format table, this function expects `df` to have
    a column 'total_flare_energy' (erg) representing the sum of E_flare * f_XUV for the system,
    OR it expects a list of flare events to aggregate.
    
    Based on task context, we assume `df` has 'semi_major_axis' (in cm) and 'total_flare_energy' (erg).
    If 'total_flare_energy' is not present, we calculate it from flare data if available, 
    otherwise assume 0.
    
    Returns: DataFrame with 'cumulative_flux' (erg/s/cm^2).
    """
    df = df.copy()
    
    # Constants
    f_XUV = config.F_XUV  # Fixed conversion factor (default 0.1)
    pi = np.pi
    
    # Ensure semi_major_axis is in cm
    # If the input is in AU (common for exoplanets), convert: 1 AU = 1.496e13 cm
    if 'semi_major_axis' in df.columns:
        # Heuristic: if max value < 10, assume AU; if > 1e12, assume cm
        if df['semi_major_axis'].max() < 100.0:
            logger.info("Assuming semi_major_axis is in AU, converting to cm.")
            a_cm = df['semi_major_axis'] * 1.496e13
        else:
            a_cm = df['semi_major_axis']
    else:
        raise ValueError("Column 'semi_major_axis' is missing from the input DataFrame.")
    
    # Calculate quiescent flux: F_quiescent = L_X / (4 * pi * a^2)
    # L_X is in erg/s, a is in cm -> F in erg/s/cm^2
    if 'L_X_quiescent' not in df.columns:
        raise ValueError("Column 'L_X_quiescent' is missing. Run calculate_quiescent_xuv first.")
    
    F_quiescent = df['L_X_quiescent'] / (4 * pi * (a_cm ** 2))
    
    # Calculate flare contribution
    # If 'total_flare_energy' (already multiplied by f_XUV) exists, use it.
    # Otherwise, if 'flare_energy_sum' exists (raw E_flare sum), multiply by f_XUV.
    # If neither, assume 0.
    if 'total_flare_energy' in df.columns:
        # Assume this column is already E_flare * f_XUV
        E_flare_XUV = df['total_flare_energy']
        logger.debug("Using 'total_flare_energy' column directly.")
    elif 'flare_energy_sum' in df.columns:
        E_flare_XUV = df['flare_energy_sum'] * f_XUV
        logger.debug("Calculated flare energy using 'flare_energy_sum' and f_XUV.")
    else:
        logger.warning("No flare energy column found. Assuming zero flare contribution.")
        E_flare_XUV = pd.Series(0.0, index=df.index)
    
    # Flare flux contribution (averaged over time? The task implies cumulative sum of energy / area)
    # The formula in the task: sum(E_flare * f_XUV / (4 * pi * a^2))
    # This results in units of erg/cm^2. However, to add to F_quiescent (erg/s/cm^2),
    # we need a rate. The task description says "Cumulative XUV Flux".
    # In many astrophysical contexts, this is the time-averaged flux.
    # If E_flare is the total energy over the system's lifetime (or observation period),
    # and we want an equivalent average flux, we divide by the time period (Age).
    # However, the task formula: F_XUV = F_quiescent + sum(...) implies adding an energy term to a power term?
    # Let's re-read: "F_XUV = F_quiescent + sum (E_flare * f_XUV / (4 pi a^2))"
    # If F_quiescent is a rate (erg/s/cm^2), and the sum is energy/area (erg/cm^2), they are dimensionally inconsistent.
    # Interpretation: The "sum" term represents the *time-averaged* flare flux.
    # Average Flare Flux = (Total Flare Energy * f_XUV) / (4 pi a^2 * Age)
    # But the task formula doesn't show division by Age.
    # Alternative Interpretation: The "cumulative flux" is actually the total energy fluence (erg/cm^2) over the lifetime,
    # and F_quiescent is converted to fluence as well (F_quiescent * Age).
    # Given the subsequent step is "mass loss rate" which depends on instantaneous flux,
    # it is highly likely the intended output is an AVERAGE FLUX (erg/s/cm^2).
    # We will assume the "sum" in the task description implies the time-averaged contribution.
    # To get average flux from total energy: F_avg = E_total / (4 pi a^2 * Age).
    # If Age is missing, we cannot compute this accurately.
    
    # Let's look at the task again: "Compute F_XUV = F_quiescent + sum(...)"
    # If we strictly follow the prompt's formula without Age, we get a dimension mismatch.
    # However, if the input 'flare_energy_sum' is actually a *rate* (erg/s) or the prompt implies
    # the sum is over a normalized time, it might work.
    # Most robust approach for "Cumulative Flux" in this context (mass loss modeling):
    # It is the time-averaged XUV flux experienced by the planet.
    # F_avg = F_quiescent + (E_flare_total * f_XUV) / (4 * pi * a^2 * Age)
    
    # Check for Age
    if 'age' in df.columns or 'system_age' in df.columns:
        age_col = 'age' if 'age' in df.columns else 'system_age'
        age = df[age_col]
        # If age is in Gyr, convert to seconds (1 Gyr = 3.154e16 s)
        if age.max() < 14: # Assume Gyr if < 14
            age_s = age * 3.154e16
        else:
            age_s = age
    else:
        # If no age, we cannot average the flare energy.
        # Fallback: Assume the flare energy provided is already an average rate?
        # Or assume a default age?
        logger.warning("System age missing. Cannot average flare energy. Assuming flare contribution is 0 for flux calculation or using default age.")
        # If we must output a flux, and we have no age, we cannot convert E to F.
        # We will assume the input 'flare_energy_sum' might be the time-integrated value, 
        # and without age, we skip the flare part or assume age=1 Gyr?
        # Let's use a default age of 5 Gyr (typical for M-dwarfs) if missing, as per config if available?
        # config.DEFAULT_M_DWARF_AGE is in Gyr?
        if hasattr(config, 'DEFAULT_M_DWARF_AGE'):
            default_age_gyr = config.DEFAULT_M_DWARF_AGE
            logger.warning(f"Using default M-dwarf age {default_age_gyr} Gyr for flare flux averaging.")
            age_s = pd.Series(default_age_gyr * 3.154e16, index=df.index)
        else:
            # Cannot proceed with averaging. Set flare flux to 0.
            logger.error("System age missing and no default configured. Flare flux contribution set to 0.")
            F_flare_avg = pd.Series(0.0, index=df.index)
            df['cumulative_flux'] = F_quiescent + F_flare_avg
            return df
    
    # Calculate average flare flux
    # F_flare_avg = (E_flare_XUV) / (4 * pi * a^2 * Age)
    F_flare_avg = E_flare_XUV / (4 * pi * (a_cm ** 2) * age_s)
    
    df['cumulative_flux'] = F_quiescent + F_flare_avg
    
    return df

def calculate_retention_fraction(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate atmospheric retention fraction.
    
    1. Calculate instantaneous mass loss rate dM/dt using energy-limited model:
       dM/dt = (epsilon * pi * Rp^3 * F_XUV) / (G * Mp * K_tide)
       
    2. Integrate over system age (assuming constant rate for simplicity or using trapezoidal if time-series).
       Total Mass Loss = dM/dt * Age
       
    3. Calculate Initial Atmosphere Mass:
       M_atm_initial = 0.01 * Mp
       
    4. Retention Fraction = 1 - (Total Mass Loss / M_atm_initial)
       (Clamped to [0, 1])
    """
    df = df.copy()
    
    # Constants
    epsilon = config.EFFICIENCY  # Default 0.15
    K_tide = config.K_TIDE       # Default 1.0
    G = config.G                 # Gravitational constant
    
    # Ensure units are consistent (cgs)
    # Rp in cm, Mp in g, F_XUV in erg/s/cm^2, Age in s
    
    # Check for radius and mass
    if 'radius' not in df.columns or 'mass' not in df.columns:
        raise ValueError("Columns 'radius' and 'mass' are required.")
    
    # Assume radius is in Earth radii or Jupiter radii? Convert to cm.
    # Heuristic: if max < 100, assume Earth radii (6.371e8 cm) or Jupiter (7.149e9)?
    # Usually exoplanet radius is in R_earth or R_jup.
    # Let's assume R_earth if values are small (1-20), R_jup if larger (1-20 but different scale).
    # Standard convention in many archives: R_earth.
    if df['radius'].max() < 20.0:
        logger.info("Assuming radius is in Earth radii (R_earth).")
        R_p = df['radius'] * 6.371e8
    elif df['radius'].max() < 200.0:
        logger.info("Assuming radius is in Jupiter radii (R_jup).")
        R_p = df['radius'] * 7.1492e9
    else:
        R_p = df['radius'] # Assume cm
    
    # Mass: Assume Earth masses or Jupiter masses?
    if df['mass'].max() < 100.0:
        logger.info("Assuming mass is in Earth masses (M_earth).")
        M_p = df['mass'] * 5.972e27
    elif df['mass'].max() < 1000.0:
        logger.info("Assuming mass is in Jupiter masses (M_jup).")
        M_p = df['mass'] * 1.898e30
    else:
        M_p = df['mass'] # Assume g
    
    # F_XUV
    if 'cumulative_flux' not in df.columns:
        raise ValueError("Column 'cumulative_flux' is missing. Run calculate_cumulative_flux first.")
    F_XUV = df['cumulative_flux']
    
    # Age
    if 'age' in df.columns:
        age = df['age']
    elif 'system_age' in df.columns:
        age = df['system_age']
    else:
        raise ValueError("System age column missing.")
    
    # Convert age to seconds if in Gyr
    if age.max() < 14:
        age_s = age * 3.154e16
    else:
        age_s = age
    
    # Calculate dM/dt
    # dM/dt = (epsilon * pi * R_p^3 * F_XUV) / (G * M_p * K_tide)
    numerator = epsilon * np.pi * (R_p ** 3) * F_XUV
    denominator = G * M_p * K_tide
    dMdt = numerator / denominator  # g/s
    
    # Total mass loss over age
    total_mass_loss = dMdt * age_s
    
    # Initial atmosphere mass
    M_atm_initial = 0.01 * M_p
    
    # Retention fraction
    # Avoid division by zero
    with np.errstate(divide='ignore', invalid='ignore'):
        retention = 1.0 - (total_mass_loss / M_atm_initial)
    
    # Clamp to [0, 1]
    retention = retention.clip(lower=0.0, upper=1.0)
    
    df['retention_fraction'] = retention
    df['mass_loss_rate'] = dMdt
    
    return df

def calculate_unphysical_flag(df: pd.DataFrame) -> pd.DataFrame:
    """
    Flag rows where mass loss rate > 10% of planet mass per Gyr.
    Threshold = 0.10 * M_p / (1 Gyr) = 0.10 * M_p / 3.154e16 s
    """
    df = df.copy()
    
    if 'mass' not in df.columns or 'mass_loss_rate' not in df.columns:
        raise ValueError("Columns 'mass' and 'mass_loss_rate' are required.")
    
    # Reconstruct M_p in grams (same logic as above)
    if df['mass'].max() < 100.0:
        M_p = df['mass'] * 5.972e27
    elif df['mass'].max() < 1000.0:
        M_p = df['mass'] * 1.898e30
    else:
        M_p = df['mass']
    
    # Threshold: 10% per Gyr
    threshold = 0.10 * M_p / 3.154e16
    
    df['is_unphysical'] = df['mass_loss_rate'] > threshold
    
    return df

def apply_unphysical_filter(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filter out rows where is_unphysical is True.
    """
    return df[~df['is_unphysical']].copy()

def run_physics_pipeline(input_path: str, output_path: str) -> None:
    """
    Main pipeline: Read merged_filtered.csv, apply physics models, filter, save.
    """
    logger.info(f"Reading input data from {input_path}")
    df = pd.read_csv(input_path)
    
    # 1. Quiescent XUV
    logger.info("Calculating quiescent XUV luminosity...")
    df = calculate_quiescent_xuv(df)
    
    # 2. Cumulative Flux
    logger.info("Calculating cumulative XUV flux...")
    df = calculate_cumulative_flux(df)
    
    # 3. Retention Fraction
    logger.info("Calculating retention fraction...")
    df = calculate_retention_fraction(df)
    
    # 4. Unphysical Flag
    logger.info("Calculating unphysical flags...")
    df = calculate_unphysical_flag(df)
    
    # 5. Filter
    initial_count = len(df)
    df = apply_unphysical_filter(df)
    logger.info(f"Filtered {initial_count - len(df)} unphysical rows.")
    
    # Save
    logger.info(f"Saving results to {output_path}")
    df.to_csv(output_path, index=False)
    logger.info("Physics pipeline complete.")

if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.INFO)
    run_physics_pipeline("data/processed/merged_filtered.csv", "data/processed/derived_physics.csv")