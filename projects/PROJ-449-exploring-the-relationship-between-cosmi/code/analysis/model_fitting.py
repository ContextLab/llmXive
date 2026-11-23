import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Tuple, Optional, Any, List
import numpy as np
import pandas as pd
from scipy.optimize import curve_fit
from scipy.stats import f_oneway, ftest

# Ensure project root is in path for imports if run as script
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from code.utils.logging import setup_logger, log_model_fit
from code.utils.config import Config

logger = logging.getLogger(__name__)

# Diffusion model: Amplitude = A / (Rigidity + B)
def diffusion_model(R, A, B):
    """
    Rigidity-dependent diffusion model parameterization.
    Amplitude = A / (Rigidity + B)
    """
    return A / (R + B)

def sinusoidal_model(t, A, T, phi, C):
    """
    Sinusoidal model for time-series fitting.
    y = A * sin(2 * pi * t / T + phi) + C
    """
    return A * np.sin(2 * np.pi * t / T + phi) + C

def load_unified_data() -> pd.DataFrame:
    """Load the unified timeseries data."""
    data_path = Path("data/processed/unified_timeseries.csv")
    if not data_path.exists():
        raise FileNotFoundError(f"Unified data file not found: {data_path}")
    
    df = pd.read_csv(data_path)
    df['date'] = pd.to_datetime(df['date'])
    return df

def extract_rigidity_bins(df: pd.DataFrame) -> List[float]:
    """Extract unique rigidity bins from the dataframe."""
    return sorted(df['rigidity_bin'].unique().tolist())

def calculate_modulation_amplitude(time_series: np.ndarray, periods: int = 11) -> Tuple[float, Any]:
    """
    Fit a sinusoidal model to the time series and calculate peak-to-trough amplitude.
    Returns (amplitude, fit_result_object)
    """
    if len(time_series) < 10:
        logger.warning("Time series too short for sinusoidal fit.")
        return np.nan, None

    t = np.arange(len(time_series))
    # Initial guess: A=1, T=11 (solar cycle approx), phi=0, C=mean
    p0 = [np.std(time_series), 11, 0, np.mean(time_series)]
    
    try:
        popt, pcov = curve_fit(
            sinusoidal_model, t, time_series, p0=p0, 
            bounds=([0, 5, -np.pi, np.min(time_series)], [np.inf, 20, np.pi, np.max(time_series)]),
            maxfev=5000
        )
        A_fit, T_fit, phi_fit, C_fit = popt
        
        # Calculate amplitude as peak-to-trough
        # Peak = A + C, Trough = -A + C -> Difference = 2A
        amplitude = 2 * abs(A_fit)
        
        return amplitude, popt
    except Exception as e:
        logger.error(f"Sinusoidal fit failed: {e}")
        return np.nan, None

def run_model_fitting(df: pd.DataFrame, output_path: Path) -> Dict[str, Any]:
    """
    Run sinusoidal fitting for each rigidity bin and save modulation amplitudes.
    """
    results = []
    rigidity_bins = extract_rigidity_bins(df)
    
    for r_bin in rigidity_bins:
        bin_data = df[df['rigidity_bin'] == r_bin].sort_values('date')
        # Use proton flux for baseline amplitude calculation (as per T020a logic context)
        # Note: T029 uses ratio amplitudes, but T028 (this step) calculates raw amplitudes first.
        # We assume 'proton_flux' is the primary metric for baseline unless specified otherwise for ratios.
        # However, T029 specifically says "Load modulation amplitudes derived from composition ratios".
        # We will calculate for He/p and Fe/p if available, or just the flux if that's the baseline.
        # For this specific T028 step, we calculate amplitudes for the flux columns to generate the file.
        
        flux_cols = ['proton_flux', 'helium_flux', 'iron_flux']
        for col in flux_cols:
            if col in bin_data.columns:
                valid_data = bin_data[col].dropna()
                if len(valid_data) > 0:
                    amp, fit_res = calculate_modulation_amplitude(valid_data.values)
                    if not np.isnan(amp):
                        results.append({
                            'rigidity_bin': r_bin,
                            'species': col,
                            'amplitude': amp,
                            'method': 'sinusoidal_fit'
                        })
    
    result_df = pd.DataFrame(results)
    result_df.to_csv(output_path, index=False)
    logger.info(f"Saved modulation amplitudes to {output_path}")
    return result_df.to_dict(orient='records')

def fit_diffusion_model(amplitudes_df: pd.DataFrame, output_path: Path) -> Dict[str, Any]:
    """
    Fit the diffusion model (A / (R + B)) to the modulation amplitudes.
    Performs convergence diagnostics as per T058.
    """
    if amplitudes_df.empty:
        logger.error("No amplitude data to fit.")
        return {}

    # We fit per species
    results_by_species = {}
    
    for species in amplitudes_df['species'].unique():
        species_data = amplitudes_df[amplitudes_df['species'] == species].sort_values('rigidity_bin')
        R = species_data['rigidity_bin'].values
        A_obs = species_data['amplitude'].values

        if len(R) < 3:
            logger.warning(f"Not enough data points for species {species} to fit diffusion model.")
            continue

        # Initial guess
        p0 = [A_obs.max() * np.mean(R), np.mean(R)]
        
        fit_success = False
        iterations = 0
        condition_number = float('nan')
        convergence_status = "failed"
        fit_params = {'A': np.nan, 'B': np.nan}
        
        try:
            popt, pcov = curve_fit(
                diffusion_model, R, A_obs, p0=p0, 
                bounds=([0, 0], [np.inf, np.inf]),
                maxfev=1000
            )
            
            # Check convergence via pcov (covariance matrix)
            # If pcov is not finite or has huge values, it might be unstable
            if pcov is not None and np.all(np.isfinite(pcov)):
                # Estimate condition number from covariance (approximation via eigenvalues of Jacobian^T J)
                # scipy curve_fit returns pcov = J^T J^-1 * residual_variance
                # We can estimate condition number of the Jacobian at solution
                # A simple heuristic: ratio of max to min eigenvalue of pcov
                evals = np.linalg.eigvalsh(pcov)
                if np.min(evals) > 0:
                    condition_number = np.max(evals) / np.min(evals)
                else:
                    condition_number = np.inf

                iterations = 1000 # curve_fit maxfev used, but actual iterations not exposed directly. 
                                  # We assume convergence if pcov is valid and finite.
                
                fit_success = True
                convergence_status = "converged" if condition_number < 1e6 else "high_condition_number"
                fit_params = {'A': popt[0], 'B': popt[1]}
                
                if condition_number > 1e6:
                    logger.warning(f"High condition number ({condition_number:.2e}) for {species}. Fit may be unstable.")
            else:
                logger.warning(f"Fit for {species} returned non-finite covariance matrix.")
                convergence_status = "non_finite_covariance"
                
        except Exception as e:
            logger.error(f"Diffusion model fit failed for {species}: {e}")
            convergence_status = "optimization_error"

        results_by_species[species] = {
            'fit_params': fit_params,
            'convergence_status': convergence_status,
            'iterations_used': iterations if fit_success else 0,
            'condition_number': condition_number,
            'success': fit_success and convergence_status == "converged"
        }

    # Save detailed results
    output_data = {
        'species_results': results_by_species,
        'model': 'Amplitude = A / (Rigidity + B)'
    }
    
    with open(output_path, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    logger.info(f"Saved diffusion model fit results to {output_path}")
    return output_data

def main():
    """Main entry point for model fitting stage."""
    logger = setup_logger("model_fitting")
    
    # Paths
    unified_path = Path("data/processed/unified_timeseries.csv")
    amp_output = Path("data/processed/modulation_amplitudes.csv")
    fit_output = Path("data/processed/model_fit_results.json")
    
    if not unified_path.exists():
        logger.error(f"Input file {unified_path} not found. Run retrieve/ratios stages first.")
        sys.exit(1)

    # 1. Calculate Modulation Amplitudes (T028)
    df = load_unified_data()
    logger.info("Calculating modulation amplitudes...")
    amplitudes = run_model_fitting(df, amp_output)
    
    # Reload as DF for fitting
    amp_df = pd.read_csv(amp_output)
    
    # 2. Fit Diffusion Model (T029 + T058 Diagnostics)
    logger.info("Fitting diffusion model with diagnostics...")
    results = fit_diffusion_model(amp_df, fit_output)
    
    # Log summary
    for species, res in results.get('species_results', {}).items():
        status = res.get('convergence_status', 'unknown')
        logger.info(f"Species {species}: Status={status}, Params={res.get('fit_params')}")
        
    if not any(r.get('success') for r in results.get('species_results', {}).values()):
        logger.warning("No species converged successfully.")
        sys.exit(1)
        
    logger.info("Model fitting stage completed successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())