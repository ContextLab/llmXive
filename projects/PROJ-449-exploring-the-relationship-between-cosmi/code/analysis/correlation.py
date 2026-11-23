import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
import numpy as np
import pandas as pd
from scipy import stats
from scipy.optimize import curve_fit

# Add project root to path for imports if running as script
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.utils.logging import setup_logger, log_correlation_result
from code.utils.config import Config

# Initialize logger
logger = setup_logger("correlation_analysis")
CONFIG = Config()

def sinusoidal_model(t, A, T, phi, C):
    """
    Sinusoidal model for solar cycle modulation.
    t: time (in years or days, consistent with data)
    A: amplitude
    T: period
    phi: phase shift
    C: offset
    """
    return A * np.sin(2 * np.pi * t / T + phi) + C

def calculate_autocorrelation_time_scale(series: pd.Series, max_lag: int = 100) -> float:
    """
    Calculate the autocorrelation time scale (tau) for a time series.
    Uses the integral of the autocorrelation function up to the first zero crossing 
    or max_lag, approximated by summing rho_k^2.
    
    Formula: tau ≈ 1 + 2 * sum(rho_k^2) for k=1 to k_max where rho_k is autocorrelation at lag k.
    Returns the sum factor (1 + 2 * sum(rho_k^2)) which is used to adjust N.
    """
    n = len(series)
    if n < 2:
        return 1.0
    
    # Normalize series
    series_norm = (series - series.mean()) / series.std()
    
    # Calculate autocorrelation up to max_lag
    autocorr_values = []
    for k in range(1, max_lag + 1):
        if k >= n:
            break
        # Calculate autocorrelation at lag k
        rho_k = np.corrcoef(series_norm[:-k], series_norm[k:])[0, 1]
        if np.isnan(rho_k):
            break
        autocorr_values.append(rho_k)
    
    if not autocorr_values:
        return 1.0
        
    # Sum of rho_k^2
    sum_rho_sq = sum(r ** 2 for r in autocorr_values)
    
    # Effective factor: 1 + 2 * sum(rho_k^2)
    edof_factor = 1.0 + 2.0 * sum_rho_sq
    
    # Prevent division by zero or extremely small values
    if edof_factor < 1.0:
        edof_factor = 1.0
        
    return edof_factor

def calculate_effective_degrees_of_freedom(series1: pd.Series, series2: pd.Series, max_lag: int = 100) -> float:
    """
    Calculate the Effective Degrees of Freedom (EDOF) for two time series.
    
    Logic:
    1. Calculate autocorrelation time scale (tau) for both series.
    2. Compute EDOF as N / (1 + 2 * sum(rho_k^2)) where rho_k is autocorrelation at lag k.
    3. Use the geometric mean of the adjustment factors for both series.
    
    Returns the effective sample size (EDOF).
    """
    n = min(len(series1), len(series2))
    if n < 2:
        return float(n)
    
    # Calculate adjustment factors for both series
    factor1 = calculate_autocorrelation_time_scale(series1, max_lag)
    factor2 = calculate_autocorrelation_time_scale(series2, max_lag)
    
    # Use geometric mean of factors for combined adjustment
    combined_factor = np.sqrt(factor1 * factor2)
    
    # Calculate EDOF
    edof = n / combined_factor
    
    # Ensure EDOF is at least 2 (minimum for correlation)
    edof = max(2.0, edof)
    
    logger.info(f"EDOF calculation: N={n}, factor1={factor1:.2f}, factor2={factor2:.2f}, combined_factor={combined_factor:.2f}, EDOF={edof:.2f}")
    
    return edof

def adjust_pvalue_for_autocorrelation(p_value: float, n_raw: int, n_edof: int, method: str = "edof") -> float:
    """
    Adjust p-value for autocorrelation using Effective Degrees of Freedom.
    
    For Pearson correlation, the t-statistic is: t = r * sqrt((n-2)/(1-r^2))
    With autocorrelation, we replace n with edof: t_adj = r * sqrt((edof-2)/(1-r^2))
    
    This function recalculates the p-value using the adjusted t-statistic.
    """
    if p_value is None or np.isnan(p_value):
        return p_value
        
    if n_edof < 3:
        # Cannot compute meaningful p-value with edof < 3
        logger.warning(f"EDOF too low ({n_edof}) for p-value adjustment, returning original p-value")
        return p_value
    
    # For now, we'll use a simpler approximation: scale p-value by ratio of degrees of freedom
    # More rigorous approach would require recalculating from correlation coefficient
    # This is a conservative adjustment that accounts for reduced effective sample size
    
    # Note: The exact relationship is complex, but a common approximation is:
    # p_adj ≈ p_raw ^ (n_edof / n_raw) for small p-values
    # However, we'll use a more direct approach by recalculating from r if we have it
    
    # For this implementation, we'll return the original p-value but log the EDOF
    # The actual adjustment requires the correlation coefficient, which we'll handle in the main function
    return p_value

def calculate_lagged_correlations(
    flux_series: pd.Series,
    sunspot_series: pd.Series,
    lags_months: List[int],
    method: str = "pearson",
    max_autocorr_lag: int = 100
) -> List[Dict[str, Any]]:
    """
    Calculate time-lagged correlations between flux and sunspot series.
    
    Args:
        flux_series: Time series of flux values (pandas Series with datetime index)
        sunspot_series: Time series of sunspot numbers (pandas Series with datetime index)
        lags_months: List of integer month lags to test (e.g., -12 to +12)
        method: 'pearson' or 'spearman'
        max_autocorr_lag: Maximum lag for autocorrelation calculation
        
    Returns:
        List of dictionaries containing lag, correlation coefficient, p-value, and EDOF
    """
    results = []
    
    # Ensure both series have same index and are aligned
    common_index = flux_series.index.intersection(sunspot_series.index)
    flux_aligned = flux_series.loc[common_index]
    sunspot_aligned = sunspot_series.loc[common_index]
    
    # Drop NaN values
    mask = ~(flux_aligned.isna() | sunspot_aligned.isna())
    flux_clean = flux_aligned[mask]
    sunspot_clean = sunspot_aligned[mask]
    
    if len(flux_clean) < 10:
        logger.warning(f"Insufficient data points ({len(flux_clean)}) for correlation analysis")
        return results
    
    # Calculate EDOF for the raw series
    n_raw = len(flux_clean)
    edof = calculate_effective_degrees_of_freedom(flux_clean, sunspot_clean, max_autocorr_lag)
    
    logger.info(f"EDOF for baseline series: N={n_raw}, EDOF={edof:.2f}")
    
    for lag in lags_months:
        # Shift sunspot series by lag months
        # Convert months to days (approx 30.44 days per month)
        lag_days = int(lag * 30.44)
        
        # Shift the sunspot series
        sunspot_shifted = sunspot_clean.shift(-lag_days)  # Negative lag means sunspot leads
        
        # Align again after shift
        common_idx = flux_clean.index.intersection(sunspot_shifted.index)
        flux_lag = flux_clean.loc[common_idx]
        sunspot_lag = sunspot_shifted.loc[common_idx]
        
        # Drop NaN
        mask_lag = ~(flux_lag.isna() | sunspot_lag.isna())
        flux_final = flux_lag[mask_lag]
        sunspot_final = sunspot_lag[mask_lag]
        
        if len(flux_final) < 10:
            continue
        
        # Calculate correlation
        if method == "pearson":
            corr, p_raw = stats.pearsonr(flux_final, sunspot_final)
        elif method == "spearman":
            corr, p_raw = stats.spearmanr(flux_final, sunspot_final)
        else:
            raise ValueError(f"Unsupported correlation method: {method}")
        
        # Calculate EDOF for this specific lag
        edof_lag = calculate_effective_degrees_of_freedom(flux_final, sunspot_final, max_autocorr_lag)
        
        # Adjust p-value using EDOF
        # Recalculate t-statistic with adjusted degrees of freedom
        if not np.isnan(corr) and abs(corr) < 1.0 and edof_lag >= 3:
            # t = r * sqrt((n-2)/(1-r^2))
            t_stat = corr * np.sqrt((edof_lag - 2) / (1 - corr**2))
            # Two-tailed p-value
            p_adj = 2 * (1 - stats.t.cdf(abs(t_stat), edof_lag - 2))
        else:
            p_adj = p_raw
            if edof_lag < 3:
                logger.warning(f"EDOF too low ({edof_lag}) for lag {lag}, using raw p-value")
        
        result = {
            "lag_months": lag,
            "correlation": float(corr),
            "p_value_raw": float(p_raw) if not np.isnan(p_raw) else None,
            "p_value_adjusted": float(p_adj) if not np.isnan(p_adj) else None,
            "edof": float(edof_lag),
            "n_samples": len(flux_final),
            "method": method
        }
        
        results.append(result)
        log_correlation_result(f"Lag {lag} months: r={corr:.3f}, p_raw={p_raw:.4f}, p_adj={p_adj:.4f}, EDOF={edof_lag:.1f}")
    
    return results

def calculate_rigidity_bin_correlations(
    data: pd.DataFrame,
    sunspot_data: pd.DataFrame,
    lags_months: List[int] = list(range(-12, 13)),
    method: str = "pearson",
    min_samples: int = 100,
    max_autocorr_lag: int = 100
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Calculate lagged correlations for each rigidity bin.
    
    Args:
        data: DataFrame with columns: date, rigidity_bin, proton_flux, helium_flux, iron_flux
        sunspot_data: DataFrame with columns: date, sunspot_number
        lags_months: List of lag values in months
        method: Correlation method ('pearson' or 'spearman')
        min_samples: Minimum number of samples required for analysis
        max_autocorr_lag: Maximum lag for autocorrelation calculation
        
    Returns:
        Dictionary mapping rigidity_bin to list of correlation results
    """
    all_results = {}
    
    # Merge data
    merged = data.merge(sunspot_data, on="date", how="inner")
    merged["date"] = pd.to_datetime(merged["date"])
    merged = merged.set_index("date")
    
    # Get unique rigidity bins
    rigidity_bins = merged["rigidity_bin"].unique()
    
    for rigidity_bin in rigidity_bins:
        bin_data = merged[merged["rigidity_bin"] == rigidity_bin]
        
        # Check for sufficient samples
        valid_proton = bin_data["proton_flux"].notna()
        if valid_proton.sum() < min_samples:
            logger.warning(f"Rigidity bin {rigidity_bin} has only {valid_proton.sum()} valid samples (< {min_samples}), skipping")
            continue
        
        # Calculate for He/p ratio
        he_p_data = bin_data.copy()
        he_p_data["he_p_ratio"] = he_p_data["helium_flux"] / he_p_data["proton_flux"]
        he_p_data = he_p_data.dropna(subset=["he_p_ratio", "sunspot_number"])
        
        if len(he_p_data) >= min_samples:
            he_p_results = calculate_lagged_correlations(
                he_p_data["he_p_ratio"],
                he_p_data["sunspot_number"],
                lags_months,
                method,
                max_autocorr_lag
            )
            all_results[f"{rigidity_bin}_he_p"] = he_p_results
            logger.info(f"Completed He/p correlation for rigidity bin {rigidity_bin}")
        
        # Calculate for Fe/p ratio
        fe_p_data = bin_data.copy()
        fe_p_data["fe_p_ratio"] = fe_p_data["iron_flux"] / fe_p_data["proton_flux"]
        fe_p_data = fe_p_data.dropna(subset=["fe_p_ratio", "sunspot_number"])
        
        if len(fe_p_data) >= min_samples:
            fe_p_results = calculate_lagged_correlations(
                fe_p_data["fe_p_ratio"],
                fe_p_data["sunspot_number"],
                lags_months,
                method,
                max_autocorr_lag
            )
            all_results[f"{rigidity_bin}_fe_p"] = fe_p_results
            logger.info(f"Completed Fe/p correlation for rigidity bin {rigidity_bin}")
        
        # Calculate for absolute proton flux (control)
        proton_data = bin_data.dropna(subset=["proton_flux", "sunspot_number"])
        if len(proton_data) >= min_samples:
            proton_results = calculate_lagged_correlations(
                proton_data["proton_flux"],
                proton_data["sunspot_number"],
                lags_months,
                method,
                max_autocorr_lag
            )
            all_results[f"{rigidity_bin}_proton"] = proton_results
            logger.info(f"Completed proton flux correlation for rigidity bin {rigidity_bin}")
    
    return all_results

def save_correlation_results(results: Dict[str, List[Dict[str, Any]]], output_dir: Path):
    """
    Save correlation results to JSON and CSV files.
    
    Args:
        results: Dictionary of correlation results
        output_dir: Directory to save output files
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Save JSON
    json_path = output_dir / "correlation_results.json"
    with open(json_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    logger.info(f"Saved correlation results to {json_path}")
    
    # Save CSV summary
    csv_path = output_dir / "correlation_summary.csv"
    rows = []
    for series_key, series_results in results.items():
        for result in series_results:
            row = {
                "series": series_key,
                "lag_months": result["lag_months"],
                "correlation": result["correlation"],
                "p_value_raw": result["p_value_raw"],
                "p_value_adjusted": result["p_value_adjusted"],
                "edof": result["edof"],
                "n_samples": result["n_samples"],
                "method": result["method"]
            }
            rows.append(row)
    
    df = pd.DataFrame(rows)
    df.to_csv(csv_path, index=False)
    logger.info(f"Saved correlation summary to {csv_path}")

def main():
    """
    Main function to run correlation analysis with EDOF adjustment.
    """
    logger.info("Starting correlation analysis with EDOF adjustment")
    
    # Load data
    data_path = Path("data/processed/unified_timeseries.csv")
    if not data_path.exists():
        logger.error(f"Data file not found: {data_path}")
        sys.exit(1)
    
    data = pd.read_csv(data_path)
    data["date"] = pd.to_datetime(data["date"])
    data = data.set_index("date")
    
    # Prepare sunspot data
    sunspot_data = data[["sunspot_number"]].copy()
    sunspot_data = sunspot_data.dropna()
    
    # Define lag range
    lags_months = list(range(-12, 13))
    
    # Run analysis
    results = calculate_rigidity_bin_correlations(
        data.reset_index(),
        sunspot_data.reset_index(),
        lags_months=lags_months,
        method="pearson",
        min_samples=100,
        max_autocorr_lag=100
    )
    
    # Save results
    output_dir = Path("data/processed")
    save_correlation_results(results, output_dir)
    
    logger.info("Correlation analysis completed successfully")
    return results

if __name__ == "__main__":
    main()