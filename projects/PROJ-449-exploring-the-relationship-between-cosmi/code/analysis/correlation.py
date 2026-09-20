"""
Correlation analysis module for cosmic ray flux and solar activity.
Implements lagged Pearson/Spearman correlations across rigidity bins.
Includes control analysis for absolute fluxes and baseline modulation amplitude derivation.
"""
import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
import pandas as pd
import numpy as np
from scipy import stats
from scipy.optimize import curve_fit

# Import local config and logging
from code.utils.config import CONFIG
from code.utils.logging import setup_logger

logger = setup_logger(__name__)

def sinusoidal_model(t, A, phi, T, C):
    """
    Simple sinusoidal model for solar modulation.
    A: Amplitude, phi: Phase, T: Period, C: Constant offset
    """
    return A * np.sin(2 * np.pi * (t - phi) / T) + C

def calculate_lagged_correlations(
    time_series: pd.DataFrame,
    target_col: str,
    solar_col: str = 'sunspot_number',
    max_lag_months: int = 12,
    method: str = 'pearson'
) -> Dict[int, Dict[str, float]]:
    """
    Calculate correlations between a target time series and solar activity
    with lags ranging from -max_lag_months to +max_lag_months.

    Args:
        time_series: DataFrame with 'date', target column, and solar column.
        target_col: Name of the column to correlate (e.g., 'He/p' or 'proton_flux').
        solar_col: Name of the solar activity column.
        max_lag_months: Maximum lag in months (positive and negative).
        method: 'pearson' or 'spearman'.

    Returns:
        Dict mapping lag (months) to {'coefficient': float, 'p_value': float}.
    """
    results = {}
    
    # Ensure date is datetime
    if not pd.api.types.is_datetime64_any_dtype(time_series['date']):
        time_series = time_series.copy()
        time_series['date'] = pd.to_datetime(time_series['date'])
    
    # Sort by date
    time_series = time_series.sort_values('date')
    
    target = time_series[target_col].values
    solar = time_series[solar_col].values
    dates = time_series['date'].values

    if len(target) != len(solar):
        raise ValueError(f"Length mismatch between target ({len(target)}) and solar ({len(solar)}) data.")

    # Filter out NaNs
    valid_mask = ~(np.isnan(target) | np.isnan(solar))
    target = target[valid_mask]
    solar = solar[valid_mask]

    if len(target) < 10:
        logger.warning(f"Insufficient data points ({len(target)}) for correlation in target {target_col}.")
        return {m: {'coefficient': np.nan, 'p_value': np.nan} for m in range(-max_lag_months, max_lag_months + 1)}

    for lag in range(-max_lag_months, max_lag_months + 1):
        # Shift solar data by lag months
        # Approximation: 1 month = 30.44 days
        lag_days = int(lag * 30.44)
        
        shifted_solar = np.roll(solar, -lag_days)
        
        # If lag is positive, we shift solar forward (solar leads), so we need to align indices
        # If lag is negative, solar lags.
        # Using numpy roll is a simple approximation for time-series alignment if dates are evenly spaced.
        # For strict date alignment, we would re-index by date, but roll is efficient for daily data.
        
        # Handle edge effects (NaNs at boundaries)
        if lag > 0:
            shifted_solar[:lag_days] = np.nan
        elif lag < 0:
            shifted_solar[lag_days:] = np.nan
        
        # Create mask for valid pairs
        valid_pair_mask = ~(np.isnan(shifted_solar))
        
        if np.sum(valid_pair_mask) < 10:
            results[lag] = {'coefficient': np.nan, 'p_value': np.nan}
            continue

        corr_target = target[valid_pair_mask]
        corr_solar = shifted_solar[valid_pair_mask]

        if method == 'pearson':
            corr, p_val = stats.pearsonr(corr_target, corr_solar)
        elif method == 'spearman':
            corr, p_val = stats.spearmanr(corr_target, corr_solar)
        else:
            raise ValueError(f"Unknown correlation method: {method}")

        results[lag] = {'coefficient': float(corr), 'p_value': float(p_val)}

    return results

def calculate_rigidity_bin_correlations(
    unified_data: pd.DataFrame
) -> Tuple[List[Dict], pd.DataFrame]:
    """
    Iterate over all rigidity bins and perform two distinct correlation sets:
    1. Composition Ratios (He/p, Fe/p) vs Sunspot
    2. Control Analysis: Absolute Fluxes (proton, helium, heavy) vs Sunspot
    
    Also derives baseline modulation amplitudes for absolute fluxes.

    Args:
        unified_data: DataFrame containing date, rigidity_bin, fluxes, and sunspot_number.

    Returns:
        Tuple of (list of correlation results, DataFrame of modulation amplitudes).
    """
    correlation_results = []
    amplitude_data = []
    
    # Get unique rigidity bins
    # Ensure rigidity_bin is numeric
    if 'rigidity_bin' not in unified_data.columns:
        raise ValueError("Input data must contain 'rigidity_bin' column.")
    
    unique_bins = sorted(unified_data['rigidity_bin'].dropna().unique())
    
    if len(unique_bins) == 0:
        logger.warning("No rigidity bins found in data.")
        return correlation_results, pd.DataFrame(columns=['rigidity_bin', 'amplitude', 'method'])

    logger.info(f"Processing {len(unique_bins)} rigidity bins.")

    for rigidity in unique_bins:
        bin_data = unified_data[unified_data['rigidity_bin'] == rigidity].copy()
        bin_data = bin_data.sort_values('date')
        
        if len(bin_data) < 30:
            logger.warning(f"Skipping rigidity bin {rigidity}: insufficient data points ({len(bin_data)}).")
            continue

        # 1. Composition Ratios
        ratios_to_check = []
        if 'He_p_ratio' in bin_data.columns:
            ratios_to_check.append(('He/p', 'He_p_ratio'))
        if 'Fe_p_ratio' in bin_data.columns:
            ratios_to_check.append(('Fe/p', 'Fe_p_ratio'))
        
        # Fallback if ratios not pre-calculated (unlikely per T014, but safe)
        if not ratios_to_check and 'helium_flux' in bin_data.columns and 'proton_flux' in bin_data.columns:
            # Calculate on the fly if needed, but T014 should have done this
            # Assuming T014 created He_p_ratio and Fe_p_ratio columns
            pass 

        for name, col in ratios_to_check:
            try:
                corr_res = calculate_lagged_correlations(bin_data, col, 'sunspot_number', CONFIG.LAG_WINDOW_MONTHS, 'pearson')
                # Find max correlation for summary
                max_corr = max(corr_res.values(), key=lambda x: abs(x['coefficient']) if not np.isnan(x['coefficient']) else -999)
                max_lag = next(k for k, v in corr_res.items() if v == max_corr)
                
                correlation_results.append({
                    'rigidity_bin': float(rigidity),
                    'metric_type': 'ratio',
                    'metric_name': name,
                    'max_lag_months': max_lag,
                    'correlation_coefficient': max_corr['coefficient'],
                    'p_value': max_corr['p_value'],
                    'all_lags': json.dumps(corr_res) # Store full lag scan
                })
            except Exception as e:
                logger.error(f"Error calculating ratio correlation for {name} at rigidity {rigidity}: {e}")

        # 2. Control Analysis: Absolute Fluxes
        flux_cols = []
        if 'proton_flux' in bin_data.columns:
            flux_cols.append(('proton_flux', 'proton_flux'))
        if 'helium_flux' in bin_data.columns:
            flux_cols.append(('helium_flux', 'helium_flux'))
        if 'heavy_flux' in bin_data.columns:
            flux_cols.append(('heavy_flux', 'heavy_flux'))
        
        for name, col in flux_cols:
            try:
                # Calculate correlations
                corr_res = calculate_lagged_correlations(bin_data, col, 'sunspot_number', CONFIG.LAG_WINDOW_MONTHS, 'pearson')
                
                # Derive Baseline Modulation Amplitude
                # Fit sinusoidal model to the time series
                time_index = np.arange(len(bin_data))
                flux_values = bin_data[col].values
                
                # Remove NaNs for fitting
                valid_fit_mask = ~np.isnan(flux_values)
                if np.sum(valid_fit_mask) < 10:
                    amplitude = np.nan
                else:
                    t_fit = time_index[valid_fit_mask]
                    y_fit = flux_values[valid_fit_mask]
                    
                    # Initial guess: A=0.1, phi=0, T=11*365 (solar cycle ~11 years), C=mean
                    # Normalize time to years for T guess? Or keep in days.
                    # Assuming daily data, T ~ 4015 days.
                    p0 = [0.1 * np.max(y_fit), 0, 4015, np.mean(y_fit)]
                    
                    try:
                        popt, _ = curve_fit(sinusoidal_model, t_fit, y_fit, p0=p0, maxfev=2000)
                        A_fit = popt[0]
                        # Amplitude is peak-to-trough difference: 2 * A (if model is A*sin... + C)
                        # The formula in task: max(fit) - min(fit) = 2*A
                        amplitude = 2 * abs(A_fit)
                    except Exception as fit_err:
                        logger.warning(f"Fit failed for {name} at rigidity {rigidity}: {fit_err}. Using fallback.")
                        amplitude = np.ptp(y_fit) # Fallback: peak-to-peak range of raw data

                # Store amplitude
                amplitude_data.append({
                    'rigidity_bin': float(rigidity),
                    'amplitude': amplitude,
                    'method': 'sinusoidal_fit'
                })
                
                # Store correlation result
                max_corr = max(corr_res.values(), key=lambda x: abs(x['coefficient']) if not np.isnan(x['coefficient']) else -999)
                max_lag = next(k for k, v in corr_res.items() if v == max_corr)
                
                correlation_results.append({
                    'rigidity_bin': float(rigidity),
                    'metric_type': 'absolute_flux',
                    'metric_name': name,
                    'max_lag_months': max_lag,
                    'correlation_coefficient': max_corr['coefficient'],
                    'p_value': max_corr['p_value'],
                    'all_lags': json.dumps(corr_res)
                })
                
            except Exception as e:
                logger.error(f"Error processing absolute flux {name} at rigidity {rigidity}: {e}")

    return correlation_results, pd.DataFrame(amplitude_data)

def main():
    """
    Main entry point for the correlation stage.
    1. Loads unified_timeseries.csv.
    2. Runs correlation analysis.
    3. Saves correlation_results.json, correlation_summary.csv, and modulation_amplitudes_baseline.csv.
    """
    logger.info("Starting Correlation Analysis Stage (T020).")
    
    input_file = Path(CONFIG.PROCESSED_DIR) / "unified_timeseries.csv"
    if not input_file.exists():
        raise FileNotFoundError(f"Input file not found: {input_file}. Run retrieve/ratios stages first.")
    
    logger.info(f"Loading data from {input_file}")
    df = pd.read_csv(input_file, parse_dates=['date'])
    
    # Validate columns
    required_cols = ['date', 'rigidity_bin', 'proton_flux', 'helium_flux', 'heavy_flux', 'sunspot_number']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in input: {missing}")
    
    # Check for ratio columns (should be present if T014 ran, else calculate)
    if 'He_p_ratio' not in df.columns and 'helium_flux' in df.columns and 'proton_flux' in df.columns:
        logger.info("Calculating He/p ratio on the fly (T014 may have been skipped).")
        df['He_p_ratio'] = df['helium_flux'] / df['proton_flux'].replace(0, np.nan)
    if 'Fe_p_ratio' not in df.columns and 'heavy_flux' in df.columns and 'proton_flux' in df.columns:
        logger.info("Calculating Fe/p ratio on the fly (T014 may have been skipped).")
        df['Fe_p_ratio'] = df['heavy_flux'] / df['proton_flux'].replace(0, np.nan)

    # Run analysis
    results_list, amplitude_df = calculate_rigidity_bin_correlations(df)
    
    if not results_list:
        logger.error("No correlation results generated. Check data quality.")
        return

    # Save JSON (Full results with all lags)
    json_path = Path(CONFIG.PROCESSED_DIR) / "correlation_results.json"
    with open(json_path, 'w') as f:
        json.dump(results_list, f, indent=2, default=str)
    logger.info(f"Saved full correlation results to {json_path}")
    
    # Save CSV (Summary)
    summary_df = pd.DataFrame(results_list)
    csv_path = Path(CONFIG.PROCESSED_DIR) / "correlation_summary.csv"
    summary_df.to_csv(csv_path, index=False)
    logger.info(f"Saved correlation summary to {csv_path}")
    
    # Save Modulation Amplitudes (Baseline for T029)
    amp_path = Path(CONFIG.PROCESSED_DIR) / "modulation_amplitudes_baseline.csv"
    amplitude_df.to_csv(amp_path, index=False)
    logger.info(f"Saved baseline modulation amplitudes to {amp_path}")
    
    logger.info("Correlation Stage completed successfully.")

if __name__ == "__main__":
    main()
