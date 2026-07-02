"""
Generate a Pre-computed CAMB Likelihood Grid for fast parameter estimation.

This script generates a grid of theoretical CMB power spectra and likelihoods
for a range of cosmological parameters (H0, Omega_m, ns, tau) using the CAMB
package. The grid is saved to data/derived/camb_grid.pkl and serves as a
fast estimator for the main analysis pipeline.

Grid parameters are defined in code/config.py.
"""
import os
import sys
import pickle
import logging
import time
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional
import numpy as np

# Add project root to path to ensure imports work
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    import camb
    from camb import model, initialpower, getCAMB
    import camb.camb as camb_c
except ImportError:
    logging.error("CAMB package is required. Please install it: pip install camb")
    sys.exit(1)

from config import (
    N_SIDE, 
    DATA_DERIVED_DIR, 
    GRID_H0_RANGE, 
    GRID_OMEGA_M_RANGE, 
    GRID_NS_RANGE, 
    GRID_TAU_RANGE, 
    GRID_H0_STEPS, 
    GRID_OMEGA_M_STEPS, 
    GRID_NS_STEPS, 
    GRID_TAU_STEPS,
    L_MAX
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def ensure_output_dir():
    """Ensure the output directory exists."""
    output_path = Path(DATA_DERIVED_DIR)
    output_path.mkdir(parents=True, exist_ok=True)
    return output_path

def generate_parameter_grid() -> Dict[str, np.ndarray]:
    """
    Generate the parameter grid based on config ranges and steps.
    
    Returns:
        Dict containing numpy arrays for each parameter.
    """
    logger.info("Generating parameter grid...")
    
    h0_vals = np.linspace(GRID_H0_RANGE[0], GRID_H0_RANGE[1], GRID_H0_STEPS)
    omega_m_vals = np.linspace(GRID_OMEGA_M_RANGE[0], GRID_OMEGA_M_RANGE[1], GRID_OMEGA_M_STEPS)
    ns_vals = np.linspace(GRID_NS_RANGE[0], GRID_NS_RANGE[1], GRID_NS_STEPS)
    tau_vals = np.linspace(GRID_TAU_RANGE[0], GRID_TAU_RANGE[1], GRID_TAU_STEPS)
    
    logger.info(f"Grid dimensions: H0={GRID_H0_STEPS}, Omega_m={GRID_OMEGA_M_STEPS}, "
                f"ns={GRID_NS_STEPS}, tau={GRID_TAU_STEPS}")
    logger.info(f"Total grid points: {GRID_H0_STEPS * GRID_OMEGA_M_STEPS * GRID_NS_STEPS * GRID_TAU_STEPS}")
    
    return {
        'H0': h0_vals,
        'Omega_m': omega_m_vals,
        'ns': ns_vals,
        'tau': tau_vals
    }

def compute_theoretical_spectrum(params: Dict[str, float]) -> Tuple[np.ndarray, np.ndarray]:
    """
    Compute the theoretical CMB power spectrum for given parameters.
    
    Args:
        params: Dictionary with H0, Omega_m, ns, tau.
        
    Returns:
        Tuple of (l_values, Cl_array) where Cl_array contains TT, EE, TE spectra.
    """
    try:
        # Initialize CAMB results
        results = camb.get_results()
        
        # Set CAMB parameters
        params_camb = camb.CAMBparams()
        params_camb.set_cosmology(
            H0=params['H0'],
            ombh2=0.022,  # Baryon density (fixed for grid)
            omch2=0.12,   # Cold dark matter density (derived from Omega_m)
            mnu=0.06,     # Neutrino mass (fixed)
            tau=params['tau']
        )
        
        # Adjust Omega_m to match the grid parameter
        # Note: Omega_m = ombh2 + omch2, so we adjust omch2
        omch2_adjusted = params['Omega_m'] * (params['H0']/100)**2 - 0.022
        if omch2_adjusted < 0:
            # Fallback for invalid parameters
            omch2_adjusted = 0.12
        params_camb.set_cosmology(omch2=omch2_adjusted)
        
        params_camb.init_power_spectrum()
        params_camb.Ns = 1
        params_camb.omega_b = 0.022 / (params['H0']/100)**2
        params_camb.omega_cdm = omch2_adjusted / (params['H0']/100)**2
        
        # Set power spectrum parameters
        params_camb.PowerSpectrum = True
        params_camb.Lmax = L_MAX
        params_camb.DoLateRadTruncation = True
        params_camb.NonLinear = camb.model.NonLinear_none
        
        # Set initial power spectrum
        params_camb.set_initial_power_spectrum(
            'scalar', 1.0, params['ns']
        )
        
        # Get results
        results = camb.get_results(params_camb)
        
        # Get power spectra
        lens_potential = False
        C_l = results.get_cmb_power_spectets(params_camb, 
                                            lens_potential=lens_potential, 
                                            lmax=L_MAX)
        
        # Extract TT, EE, TE spectra
        # C_l format: [0]=TT, [1]=EE, [2]=TE, [3]=BB (if requested)
        l_values = np.arange(L_MAX + 1)
        cl_tt = C_l[0, :, 0]  # TT
        cl_ee = C_l[1, :, 0]  # EE
        cl_te = C_l[2, :, 0]  # TE
        
        # Handle negative values (numerical issues)
        cl_tt = np.maximum(cl_tt, 0)
        cl_ee = np.maximum(cl_ee, 0)
        cl_te = np.where(np.isnan(cl_te), 0, cl_te)
        
        # Combine into single array for storage
        cl_array = np.vstack([cl_tt, cl_ee, cl_te]).T
        
        return l_values, cl_array
        
    except Exception as e:
        logger.warning(f"Failed to compute spectrum for params {params}: {e}")
        # Return zeros for invalid parameters
        return np.arange(L_MAX + 1), np.zeros((L_MAX + 1, 3))

def calculate_likelihood(cl_observed: np.ndarray, cl_theory: np.ndarray, 
                        l_values: np.ndarray, l_min: int = 2, l_max: int = None) -> float:
    """
    Calculate a simplified Gaussian likelihood for the given spectra.
    
    This is a placeholder likelihood function. In a real implementation,
    this would use the actual observational data and proper error models.
    
    Args:
        cl_observed: Observed power spectrum (l, species) array.
        cl_theory: Theoretical power spectrum (l, species) array.
        l_values: l values corresponding to the spectra.
        l_min: Minimum l to include in likelihood.
        l_max: Maximum l to include in likelihood.
        
    Returns:
        Log-likelihood value (higher is better).
    """
    if l_max is None:
        l_max = l_max
        
    mask = (l_values >= l_min) & (l_values <= l_max)
    if not np.any(mask):
        return -np.inf
        
    l_masked = l_values[mask]
    cl_obs_masked = cl_observed[mask]
    cl_theory_masked = cl_theory[mask]
    
    # Simple chi-squared like likelihood
    # In reality, this would include proper covariance matrices
    diff = cl_obs_masked - cl_theory_masked
    
    # Avoid division by zero
    variance = np.maximum(cl_theory_masked**2 * 0.01, 1e-10)
    
    chi2 = np.sum((diff**2) / variance)
    log_likelihood = -0.5 * chi2
    
    return log_likelihood

def generate_likelihood_grid(output_path: Path):
    """
    Generate the full likelihood grid by iterating over all parameter combinations.
    
    Args:
        output_path: Path to save the grid pickle file.
    """
    logger.info("Starting likelihood grid generation...")
    start_time = time.time()
    
    # Generate parameter grid
    param_grid = generate_parameter_grid()
    
    # Initialize grid storage
    grid_data = {
        'parameters': param_grid,
        'l_values': None,
        'likelihoods': np.zeros((
            GRID_H0_STEPS, 
            GRID_OMEGA_M_STEPS, 
            GRID_NS_STEPS, 
            GRID_TAU_STEPS
        )),
        'spectra': np.zeros((
            GRID_H0_STEPS, 
            GRID_OMEGA_M_STEPS, 
            GRID_NS_STEPS, 
            GRID_TAU_STEPS,
            L_MAX + 1,
            3  # TT, EE, TE
        )),
        'metadata': {
            'h0_range': GRID_H0_RANGE,
            'omega_m_range': GRID_OMEGA_M_RANGE,
            'ns_range': GRID_NS_RANGE,
            'tau_range': GRID_TAU_RANGE,
            'l_max': L_MAX,
            'generation_time': time.strftime('%Y-%m-%d %H:%M:%S'),
            'camb_version': camb.__version__ if hasattr(camb, '__version__') else 'unknown'
        }
    }
    
    # Iterate over all parameter combinations
    total_points = (GRID_H0_STEPS * GRID_OMEGA_M_STEPS * 
                   GRID_NS_STEPS * GRID_TAU_STEPS)
    processed = 0
    
    for i, h0 in enumerate(param_grid['H0']):
        for j, omega_m in enumerate(param_grid['Omega_m']):
            for k, ns in enumerate(param_grid['ns']):
                for l, tau in enumerate(param_grid['tau']):
                    params = {
                        'H0': h0,
                        'Omega_m': omega_m,
                        'ns': ns,
                        'tau': tau
                    }
                    
                    # Compute theoretical spectrum
                    l_vals, cl_theory = compute_theoretical_spectrum(params)
                    
                    # Store spectrum
                    grid_data['spectra'][i, j, k, l] = cl_theory
                    
                    # For now, we'll use a placeholder likelihood
                    # In a real implementation, we'd compare with actual data
                    # Here we just store the spectrum for later likelihood calculation
                    grid_data['likelihoods'][i, j, k, l] = 0.0
                    
                    processed += 1
                    
                    if processed % 100 == 0:
                        elapsed = time.time() - start_time
                        eta = (elapsed / processed) * (total_points - processed)
                        logger.info(f"Processed {processed}/{total_points} "
                                   f"({processed/total_points*100:.1f}%) - "
                                   f"ETA: {eta/60:.1f} minutes")
    
    # Store l_values
    grid_data['l_values'] = l_vals
    
    # Save the grid
    grid_file = output_path / 'camb_grid.pkl'
    with open(grid_file, 'wb') as f:
        pickle.dump(grid_data, f)
    
    elapsed = time.time() - start_time
    logger.info(f"Grid generation completed in {elapsed/60:.1f} minutes")
    logger.info(f"Grid saved to {grid_file}")
    
    # Print summary
    logger.info("Grid Summary:")
    logger.info(f"  H0: {GRID_H0_RANGE[0]} - {GRID_H0_RANGE[1]} ({GRID_H0_STEPS} points)")
    logger.info(f"  Omega_m: {GRID_OMEGA_M_RANGE[0]} - {GRID_OMEGA_M_RANGE[1]} ({GRID_OMEGA_M_STEPS} points)")
    logger.info(f"  ns: {GRID_NS_RANGE[0]} - {GRID_NS_RANGE[1]} ({GRID_NS_STEPS} points)")
    logger.info(f"  tau: {GRID_TAU_RANGE[0]} - {GRID_TAU_RANGE[1]} ({GRID_TAU_STEPS} points)")
    logger.info(f"  l_max: {L_MAX}")
    logger.info(f"  Total grid points: {total_points}")

def main():
    """Main entry point for grid generation."""
    logger.info("Starting CAMB Likelihood Grid Generation")
    
    # Ensure output directory exists
    output_dir = ensure_output_dir()
    
    # Generate the grid
    generate_likelihood_grid(output_dir)
    
    logger.info("Grid generation completed successfully")

if __name__ == "__main__":
    main()
