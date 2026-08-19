"""
Model fitting for rigidity-dependent diffusion analysis.

Implements least-squares optimization to fit a physics-based parameterization
to modulation amplitudes derived from cosmic ray time-series analysis.

Model: Amplitude = A / (Rigidity + B)
"""
import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Tuple, Optional, Any

import numpy as np
import pandas as pd
from scipy.optimize import curve_fit
from scipy import stats

# Setup project paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
PROCESSED_DIR = DATA_DIR / "processed"
AMPLITUDES_FILE = PROCESSED_DIR / "modulation_amplitudes.csv"
RESULTS_FILE = PROCESSED_DIR / "model_fit_results.json"

# Ensure logging is configured
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def diffusion_model(rigidity: np.ndarray, A: float, B: float) -> np.ndarray:
    """
    Physics-based parameterization for rigidity-dependent diffusion.
    
    Amplitude = A / (Rigidity + B)
    
    Args:
        rigidity: Array of rigidity values (GV)
        A: Amplitude scaling parameter (dimensionless)
        B: Rigidity offset parameter (GV)
        
    Returns:
        Predicted modulation amplitudes
    """
    # Prevent division by zero or negative denominators
    # B should be positive to ensure physical meaning (rigidity offset)
    denominator = rigidity + B
    # Add small epsilon to prevent division by zero if B is near zero
    # though curve_fit should handle this with bounds
    return A / (denominator + 1e-10)


def load_amplitudes(filepath: Path) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Load modulation amplitudes from CSV file.
    
    Args:
        filepath: Path to modulation_amplitudes.csv
        
    Returns:
        Tuple of (species, rigidity_array, amplitude_array)
    """
    if not filepath.exists():
        raise FileNotFoundError(
            f"Amplitude file not found: {filepath}. "
            "Ensure T028 has been completed successfully."
        )
    
    df = pd.read_csv(filepath)
    
    required_cols = ['species', 'rigidity', 'amplitude']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in {filepath}: {missing_cols}")
    
    # Convert to numpy arrays
    species = df['species'].values
    rigidity = df['rigidity'].values.astype(float)
    amplitude = df['amplitude'].values.astype(float)
    
    # Filter out invalid values (NaN, zero, negative rigidity)
    valid_mask = ~(np.isnan(rigidity) | np.isnan(amplitude)) & (rigidity > 0)
    
    logger.info(f"Loaded {len(rigidity)} data points, {valid_mask.sum()} valid")
    
    return species[valid_mask], rigidity[valid_mask], amplitude[valid_mask]


def fit_diffusion_model(
    rigidity: np.ndarray, 
    amplitude: np.ndarray,
    species: Optional[str] = None
) -> Dict[str, Any]:
    """
    Fit the rigidity-dependent diffusion model to amplitude data.
    
    Uses least-squares optimization with physically meaningful bounds.
    
    Args:
        rigidity: Array of rigidity values (GV)
        amplitude: Array of modulation amplitudes
        species: Optional species identifier for logging
        
    Returns:
        Dictionary containing fit parameters, statistics, and metadata
    """
    if len(rigidity) < 2:
        raise ValueError(
            f"Insufficient data points for fitting: {len(rigidity)}. "
            "Need at least 2 points."
        )
    
    logger.info(f"Fitting diffusion model for {species or 'all species'} "
               f"with {len(rigidity)} data points")
    
    # Initial parameter guesses based on physical expectations
    # A: Expected amplitude scale (typically 0.1-1.0 for cosmic rays)
    # B: Expected rigidity offset (typically 0.1-5.0 GV)
    initial_guess = [0.5, 1.0]
    
    # Parameter bounds: (lower, upper) for each parameter
    # A must be positive, B must be positive
    bounds = ([1e-6, 1e-6], [10.0, 10.0])
    
    try:
        popt, pcov = curve_fit(
            diffusion_model,
            rigidity,
            amplitude,
            p0=initial_guess,
            bounds=bounds,
            maxfev=10000,  # Increased max iterations for convergence
            ftol=1e-8,
            xtol=1e-8,
            gtol=1e-8
        )
        
        A_fit, B_fit = popt
        perr = np.sqrt(np.diag(pcov))
        A_err, B_err = perr
        
    except RuntimeError as e:
        logger.error(f"Curve fitting failed: {e}")
        raise RuntimeError(
            f"Model fitting failed to converge: {e}. "
            "Try adjusting bounds or initial guesses."
        )
    
    # Calculate goodness of fit
    y_pred = diffusion_model(rigidity, A_fit, B_fit)
    residuals = amplitude - y_pred
    
    # R-squared calculation
    ss_res = np.sum(residuals**2)
    ss_tot = np.sum((amplitude - np.mean(amplitude))**2)
    r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0
    
    # F-test for statistical significance
    n = len(rigidity)
    p = 2  # Number of fitted parameters (A, B)
    
    if n > p and ss_res > 0:
        f_statistic = ((ss_tot - ss_res) / p) / (ss_res / (n - p))
        p_value = 1 - stats.f.cdf(f_statistic, p, n - p)
    else:
        f_statistic = np.nan
        p_value = np.nan
    
    # Calculate RMSE
    rmse = np.sqrt(np.mean(residuals**2))
    
    result = {
        'species': species,
        'n_points': int(len(rigidity)),
        'parameters': {
            'A': float(A_fit),
            'A_std_error': float(A_err),
            'B': float(B_fit),
            'B_std_error': float(B_err)
        },
        'goodness_of_fit': {
            'r_squared': float(r_squared),
            'f_statistic': float(f_statistic) if not np.isnan(f_statistic) else None,
            'p_value': float(p_value) if not np.isnan(p_value) else None,
            'rmse': float(rmse)
        },
        'convergence': {
            'success': True,
            'message': 'Model fitting completed successfully'
        }
    }
    
    logger.info(f"Fit results for {species or 'all'}: A={A_fit:.4f}±{A_err:.4f}, "
               f"B={B_fit:.4f}±{B_err:.4f}, R²={r_squared:.4f}")
    
    return result


def run_model_fitting(
    input_file: Optional[Path] = None,
    output_file: Optional[Path] = None
) -> Dict[str, Any]:
    """
    Main function to run model fitting pipeline.
    
    Args:
        input_file: Path to modulation_amplitudes.csv (default: auto-detect)
        output_file: Path for results JSON (default: auto-detect)
        
    Returns:
        Dictionary containing all fit results by species
    """
    input_path = input_file or AMPLITUDES_FILE
    output_path = output_file or RESULTS_FILE
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Load data
    species_arr, rigidity_arr, amplitude_arr = load_amplitudes(input_path)
    
    # Group by species
    unique_species = np.unique(species_arr)
    all_results = {
        'metadata': {
            'input_file': str(input_path),
            'output_file': str(output_path),
            'model': 'Amplitude = A / (Rigidity + B)',
            'total_points': int(len(rigidity_arr)),
            'species_count': int(len(unique_species))
        },
        'fits': {}
    }
    
    # Fit model for each species
    for species in unique_species:
        mask = species_arr == species
        rigidity_spec = rigidity_arr[mask]
        amplitude_spec = amplitude_arr[mask]
        
        logger.info(f"Processing species: {species} ({len(rigidity_spec)} points)")
        
        try:
            fit_result = fit_diffusion_model(
                rigidity_spec, 
                amplitude_spec, 
                species=str(species)
            )
            all_results['fits'][str(species)] = fit_result
        except Exception as e:
            logger.error(f"Failed to fit model for {species}: {e}")
            all_results['fits'][str(species)] = {
                'species': str(species),
                'convergence': {
                    'success': False,
                    'message': str(e)
                }
            }
    
    # Save results
    with open(output_path, 'w') as f:
        json.dump(all_results, f, indent=2)
    
    logger.info(f"Results saved to {output_path}")
    
    return all_results


def main():
    """Entry point for model fitting script."""
    logger.info("Starting rigidity-dependent diffusion model fitting")
    
    try:
        results = run_model_fitting()
        
        # Print summary
        print("\n=== Model Fitting Summary ===")
        print(f"Total data points: {results['metadata']['total_points']}")
        print(f"Species fitted: {len(results['fits'])}")
        
        for species, fit_data in results['fits'].items():
            if fit_data.get('convergence', {}).get('success'):
                params = fit_data['parameters']
                fit_stats = fit_data['goodness_of_fit']
                print(f"\n{species}:")
                print(f"  A = {params['A']:.4f} ± {params['A_std_error']:.4f}")
                print(f"  B = {params['B']:.4f} ± {params['B_std_error']:.4f}")
                print(f"  R² = {fit_stats['r_squared']:.4f}")
                if fit_stats['p_value'] is not None:
                    print(f"  p-value = {fit_stats['p_value']:.4e}")
            else:
                print(f"\n{species}: FAILED - {fit_data['convergence']['message']}")
        
        print(f"\nResults saved to: {RESULTS_FILE}")
        
    except Exception as e:
        logger.error(f"Model fitting pipeline failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()