"""
Model fitting module for deriving modulation amplitudes from cosmic ray time series.

This module performs sinusoidal fits to the time-series data for each rigidity bin,
calculates the peak-to-trough difference (modulation amplitude), and saves the results
to data/processed/modulation_amplitudes.csv.

It also supports fitting a rigidity-dependent diffusion model to these amplitudes.
"""
import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Tuple, Optional, Any, List
import numpy as np
import pandas as pd
from scipy.optimize import curve_fit
from scipy.stats import f
from code.utils.logging import setup_logger
from code.utils.config import Config

# Initialize logger
logger = setup_logger(__name__)

# Load configuration
config = Config()

# Define paths
DATA_DIR = Path(config.data_dir)
PROCESSED_DIR = DATA_DIR / "processed"
UNIFIED_TIMESERIES_PATH = PROCESSED_DIR / "unified_timeseries.csv"
MODULATION_AMPLITUDES_PATH = PROCESSED_DIR / "modulation_amplitudes.csv"
MODEL_TREND_PATH = PROCESSED_DIR / "model_trend.json"

def sinusoidal_model(t: np.ndarray, A: float, B: float, C: float, D: float) -> np.ndarray:
    """
    Sinusoidal model for cosmic ray flux modulation.
    
    Parameters:
        t: Time array (in days or months)
        A: Amplitude of modulation
        B: Phase offset (in same units as t)
        C: Mean flux level
        D: Trend slope (optional linear trend)
    
    Returns:
        Model values
    """
    # Period is approximately 11 years = 132 months
    period = 132.0  # months
    return A * np.sin(2 * np.pi * (t - B) / period) + C + D * t

def load_unified_data() -> pd.DataFrame:
    """
    Load the unified timeseries data from disk.
    
    Returns:
        DataFrame with columns: date, rigidity_bin, proton_flux, helium_flux, heavy_flux, sunspot_number
    """
    if not UNIFIED_TIMESERIES_PATH.exists():
        logger.error(f"Unified timeseries file not found: {UNIFIED_TIMESERIES_PATH}")
        raise FileNotFoundError(f"Unified timeseries file not found: {UNIFIED_TIMESERIES_PATH}")
    
    df = pd.read_csv(UNIFIED_TIMESERIES_PATH, parse_dates=['date'])
    logger.info(f"Loaded {len(df)} rows from {UNIFIED_TIMESERIES_PATH}")
    return df

def extract_rigidity_bins(df: pd.DataFrame) -> List[float]:
    """
    Extract unique rigidity bins from the data.
    
    Parameters:
        df: DataFrame with rigidity_bin column
    
    Returns:
        List of unique rigidity bin values
    """
    return sorted(df['rigidity_bin'].unique().tolist())

def calculate_modulation_amplitude(df: pd.DataFrame, rigidity_bin: float) -> Tuple[float, Dict[str, Any]]:
    """
    Perform sinusoidal fit for a specific rigidity bin and calculate modulation amplitude.
    
    Parameters:
        df: DataFrame with time series data for a specific rigidity bin
        rigidity_bin: The rigidity bin value
    
    Returns:
        Tuple of (amplitude, fit_info) where fit_info contains parameters and diagnostics
    """
    if len(df) < 10:
        logger.warning(f"Insufficient data points ({len(df)}) for rigidity bin {rigidity_bin}")
        return np.nan, {'error': 'insufficient_data', 'n_points': len(df)}
    
    # Prepare time array (convert to months since start)
    df = df.sort_values('date').reset_index(drop=True)
    start_date = df['date'].min()
    df['time_months'] = (df['date'] - start_date).dt.days / 30.44  # Approximate months
    
    t = df['time_months'].values
    y = df['proton_flux'].values  # Use proton flux for amplitude calculation
    
    # Remove NaN values
    valid_mask = ~np.isnan(y)
    t = t[valid_mask]
    y = y[valid_mask]
    
    if len(t) < 10:
        logger.warning(f"Insufficient valid data points ({len(t)}) for rigidity bin {rigidity_bin} after NaN removal")
        return np.nan, {'error': 'insufficient_valid_data', 'n_points': len(t)}
    
    # Normalize y for better fitting
    y_mean = np.mean(y)
    y_std = np.std(y)
    if y_std < 1e-10:
        logger.warning(f"Zero variance in data for rigidity bin {rigidity_bin}")
        return np.nan, {'error': 'zero_variance', 'n_points': len(t)}
    
    y_norm = (y - y_mean) / y_std
    
    # Initial parameter guesses
    # A: amplitude (normalized), B: phase, C: mean (0 after normalization), D: slope
    A0 = 0.1  # Expected small modulation amplitude
    B0 = 0.0  # Phase offset
    C0 = 0.0  # Mean (already normalized)
    D0 = 0.0  # No trend initially
    
    p0 = [A0, B0, C0, D0]
    
    try:
        # Perform curve fitting
        popt, pcov = curve_fit(
            sinusoidal_model, t, y_norm,
            p0=p0,
            bounds=([0, -100, -10, -0.1], [1, 100, 10, 0.1]),
            maxfev=5000
        )
        
        # Extract fitted parameters
        A_fit, B_fit, C_fit, D_fit = popt
        
        # Calculate fitted values
        y_fit = sinusoidal_model(t, *popt)
        
        # Calculate amplitude in original units
        amplitude_original = A_fit * y_std
        
        # Calculate peak-to-trough difference
        max_fit = np.max(y_fit)
        min_fit = np.min(y_fit)
        peak_to_trough = max_fit - min_fit
        
        # Convert back to original units
        amplitude_original_ptt = peak_to_trough * y_std
        
        # Calculate R²
        ss_res = np.sum((y_norm - y_fit) ** 2)
        ss_tot = np.sum((y_norm - np.mean(y_norm)) ** 2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0
        
        fit_info = {
            'parameters': {
                'A': float(A_fit),
                'B': float(B_fit),
                'C': float(C_fit),
                'D': float(D_fit)
            },
            'r_squared': float(r_squared),
            'n_points': len(t),
            'method': 'sinusoidal_fit',
            'amplitude_original': float(amplitude_original),
            'peak_to_trough_original': float(amplitude_original_ptt)
        }
        
        return float(amplitude_original_ptt), fit_info
        
    except Exception as e:
        logger.warning(f"Curve fitting failed for rigidity bin {rigidity_bin}: {str(e)}")
        return np.nan, {'error': str(e), 'n_points': len(t)}

def run_model_fitting() -> pd.DataFrame:
    """
    Run model fitting for all rigidity bins and save results.
    
    Returns:
        DataFrame with modulation amplitudes for all rigidity bins
    """
    logger.info("Starting model fitting for all rigidity bins...")
    
    # Load unified data
    df = load_unified_data()
    
    # Extract unique rigidity bins
    rigidity_bins = extract_rigidity_bins(df)
    logger.info(f"Found {len(rigidity_bins)} unique rigidity bins: {rigidity_bins}")
    
    # Results storage
    results = []
    
    for rigidity_bin in rigidity_bins:
        logger.info(f"Processing rigidity bin: {rigidity_bin}")
        
        # Filter data for this rigidity bin
        df_bin = df[df['rigidity_bin'] == rigidity_bin].copy()
        
        # Calculate modulation amplitude
        amplitude, fit_info = calculate_modulation_amplitude(df_bin, rigidity_bin)
        
        # Store results
        result = {
            'rigidity_bin': rigidity_bin,
            'amplitude': amplitude,
            'method': 'sinusoidal_fit'
        }
        
        # Add fit info if available
        if 'error' not in fit_info:
            result.update({
                'r_squared': fit_info['r_squared'],
                'n_points': fit_info['n_points'],
                'A': fit_info['parameters']['A'],
                'B': fit_info['parameters']['B'],
                'C': fit_info['parameters']['C'],
                'D': fit_info['parameters']['D']
            })
        else:
            result['error'] = fit_info.get('error', 'unknown')
            result['n_points'] = fit_info.get('n_points', 0)
        
        results.append(result)
    
    # Create results DataFrame
    results_df = pd.DataFrame(results)
    
    # Save to CSV
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    results_df.to_csv(MODULATION_AMPLITUDES_PATH, index=False)
    logger.info(f"Saved modulation amplitudes to {MODULATION_AMPLITUDES_PATH}")
    
    return results_df

def fit_diffusion_model(amplitudes_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Fit a rigidity-dependent diffusion model to the modulation amplitudes.
    
    Model: Amplitude = A / (Rigidity + B)
    
    Parameters:
        amplitudes_df: DataFrame with rigidity_bin and amplitude columns
    
    Returns:
        Dictionary with fitted parameters and diagnostics
    """
    # Filter out rows with NaN amplitudes
    valid_df = amplitudes_df.dropna(subset=['amplitude'])
    
    if len(valid_df) < 2:
        logger.warning("Insufficient data points for diffusion model fitting")
        return {'error': 'insufficient_data', 'n_points': len(valid_df)}
    
    rigidity = valid_df['rigidity_bin'].values
    amplitude = valid_df['amplitude'].values
    
    # Define diffusion model
    def diffusion_model(r: np.ndarray, A: float, B: float) -> np.ndarray:
        return A / (r + B)
    
    # Initial parameter guesses
    A0 = np.max(amplitude) * np.mean(rigidity)
    B0 = np.mean(rigidity)
    
    p0 = [A0, B0]
    
    try:
        # Perform curve fitting
        popt, pcov = curve_fit(
            diffusion_model, rigidity, amplitude,
            p0=p0,
            bounds=([0, 0], [np.inf, np.inf]),
            maxfev=5000
        )
        
        A_fit, B_fit = popt
        
        # Calculate fitted values
        y_fit = diffusion_model(rigidity, A_fit, B_fit)
        
        # Calculate R²
        ss_res = np.sum((amplitude - y_fit) ** 2)
        ss_tot = np.sum((amplitude - np.mean(amplitude)) ** 2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0
        
        # Calculate F-statistic
        n = len(amplitude)
        p = 2  # number of parameters
        dof = n - p
        f_statistic = (r_squared / p) / ((1 - r_squared) / dof) if dof > 0 and r_squared < 1 else np.inf
        
        # Calculate p-value for F-test
        p_value = 1 - f.cdf(f_statistic, p, dof) if dof > 0 else 1.0
        
        fit_result = {
            'parameters': {
                'A': float(A_fit),
                'B': float(B_fit)
            },
            'r_squared': float(r_squared),
            'f_statistic': float(f_statistic),
            'p_value': float(p_value),
            'degrees_of_freedom': dof,
            'n_points': n,
            'method': 'diffusion_model'
        }
        
        logger.info(f"Diffusion model fit: A={A_fit:.4f}, B={B_fit:.4f}, R²={r_squared:.4f}, p-value={p_value:.4f}")
        
        return fit_result
        
    except Exception as e:
        logger.warning(f"Diffusion model fitting failed: {str(e)}")
        return {'error': str(e), 'n_points': len(amplitude)}

def main():
    """
    Main entry point for model fitting stage.
    """
    logger.info("=== Model Fitting Stage ===")
    
    try:
        # Run model fitting for all rigidity bins
        amplitudes_df = run_model_fitting()
        
        # Fit diffusion model to amplitudes
        diffusion_result = fit_diffusion_model(amplitudes_df)
        
        # Save diffusion model results
        if 'error' not in diffusion_result:
            with open(MODEL_TREND_PATH, 'w') as f:
                json.dump(diffusion_result, f, indent=2)
            logger.info(f"Saved diffusion model trend to {MODEL_TREND_PATH}")
        
        logger.info("Model fitting stage completed successfully")
        return amplitudes_df, diffusion_result
        
    except Exception as e:
        logger.error(f"Model fitting stage failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()
