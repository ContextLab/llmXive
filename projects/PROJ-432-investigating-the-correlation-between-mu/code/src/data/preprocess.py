import pandas as pd
import numpy as np
import logging
from pathlib import Path
from typing import Union

# Import constants if available, otherwise define defaults matching spec
# The spec references Grieder (1985) parameters.
# Default Grieder parameters for T_eff calculation:
# T_eff = Integral (T(z) * W(z) dz) / Integral (W(z) dz)
# Weight function W(z) approximated by a Gaussian centered at z_peak with sigma.
# Standard values often used: z_peak ~ 12km (or pressure ~200hPa), sigma ~ 4km.
# We will read from constants.yaml if it exists, else use defaults.
try:
    import yaml
    from src.config.constants import get_config
    # Assuming constants.py or similar loads the yaml. 
    # If not, we fallback to defaults below.
    CONFIG = get_config()
    Z_PEAK_KM = CONFIG.get('grieder', {}).get('z_peak_km', 12.0)
    SIGMA_KM = CONFIG.get('grieder', {}).get('sigma_km', 4.0)
    PRESSURE_LEVELS = CONFIG.get('era5', {}).get('pressure_levels', [1000, 925, 850, 700, 500, 400, 300, 250, 200, 150, 100, 70, 50, 30, 20, 10])
except (ImportError, FileNotFoundError, KeyError):
    # Fallback defaults
    Z_PEAK_KM = 12.0
    SIGMA_KM = 4.0
    # Standard ERA5 levels often used in these studies
    PRESSURE_LEVELS = [1000, 925, 850, 700, 500, 400, 300, 250, 200, 150, 100, 70, 50, 30, 20, 10]

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def pressure_to_altitude(p_hpa: Union[float, pd.Series]) -> Union[float, pd.Series]:
    """
    Approximate geometric altitude from pressure using the hypsometric equation.
    Assumes standard atmosphere: T0=288.15K, L=-0.0065 K/m.
    Returns altitude in km.
    """
    # Simplified approximation: h = -7000 * ln(p/1013.25) (rough estimate)
    # More accurate using hypsometric equation with mean temp.
    # Let's use a standard conversion: h = 44330 * (1 - (p/1013.25)**(1/5.255)) meters
    p = np.array(p_hpa) if not isinstance(p_hpa, np.ndarray) else p_hpa
    h_m = 44330 * (1 - (p / 1013.25) ** (1 / 5.255))
    return h_m / 1000.0  # Convert to km

def calculate_weight_function(altitudes_km: np.ndarray, z_peak: float, sigma: float) -> np.ndarray:
    """
    Calculate the weight function W(z) based on Grieder (1985).
    W(z) = exp(-0.5 * ((z - z_peak) / sigma)^2)
    """
    return np.exp(-0.5 * ((altitudes_km - z_peak) / sigma) ** 2)

def calculate_t_eff(df: pd.DataFrame) -> pd.Series:
    """
    Calculate Effective Temperature (T_eff) for each day in the dataframe.
    
    The input DataFrame 'df' is expected to be the aligned daily data (from T012)
    or a raw daily aggregation where temperature values are available for multiple
    pressure levels per date.
    
    Expected columns in df:
    - 'date': datetime or string
    - 'pressure_level': pressure in hPa (1000, 925, ..., 10)
    - 'temperature': temperature in Kelvin or Celsius (assumed Kelvin for physics, 
      but if Celsius, conversion needed. ERA5 is usually Kelvin or Celsius depending on product. 
      Let's assume Kelvin as per standard atmospheric physics, or handle conversion if needed.
      Standard ERA5 temperature is in Kelvin.
    - 't_eff_value': (Optional) if we are appending, but here we calculate it.
    
    If the input is a wide format (dates as index, pressure levels as columns), 
    we need to pivot. However, the task says 'save results to t_eff_values.csv',
    implying we process the aligned data.
    
    Assumption: The input df is in 'long' format (one row per date-pressure combination)
    OR we pivot it. Given T012 produces 'aligned_daily.csv', let's assume it might be wide
    or long. The robust way is to pivot if necessary.
    
    If the input is already daily aggregated with multiple rows per date (one per pressure level),
    we group by date.
    
    Steps:
    1. Ensure 'date' is datetime.
    2. Convert pressure to altitude.
    3. Calculate weights for each pressure level.
    4. For each date, compute weighted average of temperature.
       T_eff = sum(T_i * W_i) / sum(W_i)
    5. Handle missing pressure levels via linear interpolation of temperature vs altitude.
    
    Returns:
    pd.Series: T_eff values indexed by date.
    """
    if df.empty:
        return pd.Series(dtype=float)

    df = df.copy()
    
    # Ensure date is datetime
    if not pd.api.types.is_datetime64_any_dtype(df['date']):
        df['date'] = pd.to_datetime(df['date'])
    
    # Sort to ensure consistent processing
    df = df.sort_values(['date', 'pressure_level'])

    # Convert pressure to altitude (km)
    # We need to do this for the whole column if pressure_level is uniform across dates
    # or group-wise if it varies (it shouldn't).
    if 'altitude_km' not in df.columns:
        df['altitude_km'] = pressure_to_altitude(df['pressure_level'])

    # Calculate weights (constant across dates for same pressure levels)
    # We compute weights based on the unique pressure levels present
    unique_pressures = df['pressure_level'].unique()
    unique_altitudes = pressure_to_altitude(unique_pressures)
    
    # If we have missing pressure levels, we might need to interpolate T before weighting?
    # The spec says: "include linear interpolation for missing pressure levels"
    # This implies: If a date is missing a pressure level (e.g., no data at 200hPa),
    # we interpolate the temperature at that altitude using neighbors, THEN apply weights.
    
    # Strategy:
    # 1. Define the full set of target pressure levels (from constants or standard list).
    # 2. For each date, ensure we have T at all target levels via interpolation.
    # 3. Apply weights.
    
    target_pressures = PRESSURE_LEVELS
    target_altitudes = pressure_to_altitude(target_pressures)
    weights = calculate_weight_function(target_altitudes, Z_PEAK_KM, SIGMA_KM)
    
    t_eff_values = []
    
    # Group by date
    for date, group in df.groupby('date'):
        # Create a mapping of altitude -> temperature for this date
        # Using the available data points
        altitudes = group['altitude_km'].values
        temps = group['temperature'].values
        
        # Check for NaNs in available data
        valid_mask = ~np.isnan(temps)
        if not np.any(valid_mask):
            logger.warning(f"No valid temperature data for {date}")
            t_eff_values.append({'date': date, 't_eff_value': np.nan})
            continue
        
        valid_altitudes = altitudes[valid_mask]
        valid_temps = temps[valid_mask]
        
        # Sort by altitude for interpolation
        sort_idx = np.argsort(valid_altitudes)
        valid_altitudes = valid_altitudes[sort_idx]
        valid_temps = valid_temps[sort_idx]
        
        # Interpolate to target altitudes
        # If we have fewer than 2 points, we cannot interpolate linearly meaningfully
        if len(valid_altitudes) < 2:
            logger.warning(f"Insufficient data points ({len(valid_altitudes)}) for interpolation on {date}. Using available mean or NaN.")
            # If only one point, maybe use that? But T_eff requires a profile.
            # Spec says "linear interpolation". If insufficient, maybe skip or use available.
            # Let's try to use the single point if available, but it's not a profile.
            # Better to return NaN if we can't build a profile.
            t_eff_values.append({'date': date, 't_eff_value': np.nan})
            continue
        
        # Interpolate temperature at target altitudes
        # Use 'linear' interpolation. Extrapolate? No, usually clamp or NaN.
        # Let's use 'linear' and set extrapolated to NaN or fill with edge values?
        # Standard practice: if outside range, use nearest or NaN. 
        # We'll use 'linear' and then mask NaNs if outside range.
        try:
            interpolated_temps = np.interp(target_altitudes, valid_altitudes, valid_temps)
        except ValueError:
            logger.error(f"Interpolation failed for {date}")
            t_eff_values.append({'date': date, 't_eff_value': np.nan})
            continue
        
        # Apply weights
        # T_eff = sum(T_interp * W) / sum(W)
        # Note: Weights are calculated for ALL target levels. 
        # If interpolation resulted in NaN (e.g., outside range), we should handle it.
        # np.interp returns values within range. If target is outside, it returns edge values?
        # np.interp behavior: extrapolates with edge values. This might be acceptable.
        
        numerator = np.sum(interpolated_temps * weights)
        denominator = np.sum(weights)
        
        if denominator == 0:
            t_eff_values.append({'date': date, 't_eff_value': np.nan})
        else:
            t_eff = numerator / denominator
            t_eff_values.append({'date': date, 't_eff_value': t_eff})
    
    result_df = pd.DataFrame(t_eff_values)
    result_df['date'] = pd.to_datetime(result_df['date'])
    return result_df.set_index('date')['t_eff_value']

def run_preprocessing(input_path: str, output_path: str):
    """
    Main entry point to run T_eff calculation and save to CSV.
    """
    logger.info(f"Loading data from {input_path}")
    df = pd.read_csv(input_path)
    
    logger.info("Calculating T_eff values...")
    t_eff_series = calculate_t_eff(df)
    
    # Convert to DataFrame for saving
    result_df = t_eff_series.reset_index()
    result_df.columns = ['date', 't_eff_value']
    
    # Ensure output directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Saving results to {output_path}")
    result_df.to_csv(output_path, index=False)
    
    logger.info("Preprocessing complete.")

if __name__ == "__main__":
    # Default paths relative to project root
    INPUT_FILE = "data/processed/aligned_daily.csv"
    OUTPUT_FILE = "data/processed/t_eff_values.csv"
    
    import sys
    if len(sys.argv) > 1:
        INPUT_FILE = sys.argv[1]
    if len(sys.argv) > 2:
        OUTPUT_FILE = sys.argv[2]
        
    run_preprocessing(INPUT_FILE, OUTPUT_FILE)
