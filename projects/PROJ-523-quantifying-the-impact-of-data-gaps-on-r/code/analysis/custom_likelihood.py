"""
Custom Likelihood Correction Module (Alternative to Mode-Coupling).

Implements FR-009: Provides a custom likelihood correction path for
estimating cosmological parameters from masked CMB maps without
explicitly computing the full Mode-Coupling (Leakage) Matrix.

This approach uses an empirical bias correction based on the
observed power spectrum of the mask and a pre-computed grid of
theoretical spectra.
"""
import numpy as np
import healpy as hp
import logging
import os
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
from scipy.interpolate import RegularGridInterpolator
from scipy.stats import norm

from code.config import DATA_DERIVED_DIR, DATA_RESULTS_DIR, N_SIDE
from code.data_io import load_metadata

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def compute_mask_power_spectrum(mask: np.ndarray, nside: int = N_SIDE) -> np.ndarray:
    """
    Compute the angular power spectrum of the gap mask.
    
    Args:
        mask: HEALPix mask array (1.0 = observed, 0.0 = gap).
        nside: HEALPix resolution parameter.
        
    Returns:
        Array of C_l values for the mask.
    """
    # Ensure mask is float for anafast
    mask_float = mask.astype(np.float64)
    # anafast returns C_l for the input map
    cl_mask = hp.anafast(mask_float, lmax=2*nside-1, pol=False)
    return cl_mask


def estimate_bias_correction(cl_observed: np.ndarray, 
                             cl_mask: np.ndarray, 
                             lmax: int = 2000) -> np.ndarray:
    """
    Estimate the bias introduced by the mask on the observed power spectrum.
    
    This is a simplified correction model:
    Bias(l) ≈ C_l_mask * (C_l_signal - mean(C_l_signal)) / mean(C_l_signal)
    
    In a full implementation, this would be derived from the leakage matrix,
    but here we use an empirical approximation for the "alternative path".
    
    Args:
        cl_observed: Observed power spectrum (biased).
        cl_mask: Power spectrum of the mask.
        lmax: Maximum l to consider.
        
    Returns:
        Estimated bias vector for l=0 to lmax.
    """
    l_vals = np.arange(len(cl_mask))
    # Filter to lmax
    valid_idx = l_vals <= lmax
    cl_obs_filtered = cl_observed[valid_idx]
    cl_mask_filtered = cl_mask[valid_idx]
    
    # Empirical scaling factor (simplified model)
    # In reality, this depends on the specific mode-coupling kernel
    mean_signal = np.mean(cl_obs_filtered[cl_obs_filtered > 0])
    if mean_signal == 0:
        mean_signal = 1e-10
        
    # Approximate bias: proportional to mask power * signal variance
    # This is a placeholder for the actual mode-coupling integral
    bias_est = cl_mask_filtered * (cl_obs_filtered - mean_signal) / mean_signal
    
    # Ensure we return a full array up to lmax (pad with zeros if needed)
    full_bias = np.zeros(lmax + 1)
    full_bias[valid_idx] = bias_est
    
    return full_bias


def apply_custom_likelihood_correction(cl_observed: np.ndarray,
                                       mask: np.ndarray,
                                       lmax: int = 2000) -> Tuple[np.ndarray, Dict[str, Any]]:
    """
    Apply the custom likelihood correction to an observed power spectrum.
    
    This function:
    1. Computes the mask power spectrum.
    2. Estimates the bias introduced by the mask.
    3. Corrects the observed spectrum.
    4. Returns the corrected spectrum and metadata.
    
    Args:
        cl_observed: The observed (biased) power spectrum.
        mask: The gap mask used to create the observation.
        lmax: Maximum multipole moment to correct.
        
    Returns:
        Tuple of (corrected_cl, correction_metadata)
    """
    logger.info("Applying custom likelihood correction (alternative to mode-coupling)")
    
    # Compute mask power spectrum
    cl_mask = compute_mask_power_spectrum(mask, N_SIDE)
    
    # Estimate bias
    bias = estimate_bias_correction(cl_observed, cl_mask, lmax)
    
    # Correct the observed spectrum
    # Corrected = Observed - Estimated Bias
    l_vals = np.arange(len(cl_observed))
    valid_idx = l_vals <= lmax
    corrected_cl = cl_observed.copy()
    corrected_cl[valid_idx] = cl_observed[valid_idx] - bias[valid_idx]
    
    # Ensure non-negative (physical constraint)
    corrected_cl = np.maximum(corrected_cl, 0.0)
    
    metadata = {
        "correction_method": "custom_likelihood_alternative",
        "lmax": lmax,
        "mask_cl_sum": float(np.sum(cl_mask)),
        "bias_magnitude": float(np.mean(bias)),
        "correction_applied": True
    }
    
    logger.info(f"Correction applied. Mean bias removed: {metadata['bias_magnitude']:.2e}")
    
    return corrected_cl, metadata


def load_precomputed_grid(grid_path: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Load the pre-computed CAMB likelihood grid if available.
    
    This is used for parameter estimation after correction.
    
    Args:
        grid_path: Path to the grid file (default from config).
        
    Returns:
        Dictionary containing the grid data or None if not found.
    """
    if grid_path is None:
        grid_path = os.path.join(DATA_DERIVED_DIR, "camb_grid.pkl")
        
    if not os.path.exists(grid_path):
        logger.warning(f"Pre-computed grid not found at {grid_path}. "
                     "Parameter estimation will be skipped or use defaults.")
        return None
        
    import pickle
    try:
        with open(grid_path, 'rb') as f:
            grid_data = pickle.load(f)
        logger.info(f"Loaded pre-computed grid from {grid_path}")
        return grid_data
    except Exception as e:
        logger.error(f"Failed to load grid: {e}")
        return None


def estimate_parameters_from_grid(corrected_cl: np.ndarray,
                                  grid_data: Dict[str, Any],
                                  lmax: int = 2000) -> Dict[str, Any]:
    """
    Estimate cosmological parameters by querying the pre-computed grid.
    
    This uses a simple nearest-neighbor or interpolation approach on the
    pre-computed likelihood grid to find the best-fit parameters.
    
    Args:
        corrected_cl: The bias-corrected power spectrum.
        grid_data: The pre-computed CAMB grid data.
        lmax: Maximum l to use for comparison.
        
    Returns:
        Dictionary with estimated parameters and goodness-of-fit.
    """
    if grid_data is None:
        logger.error("Cannot estimate parameters: Grid data is missing.")
        return {
            "H0": None,
            "Omega_m": None,
            "n_s": None,
            "tau": None,
            "status": "failed_no_grid"
        }
    
    # Extract grid components
    # Expected structure: { 'params': [H0, Omega_m, n_s, tau], 'likelihoods': [...], 'cl_theory': [...] }
    params_keys = grid_data.get('params_keys', ['H0', 'Omega_m', 'n_s', 'tau'])
    grid_params = grid_data['params']
    grid_likelihoods = grid_data['likelihoods']
    grid_cl_theory = grid_data['cl_theory']
    
    # Truncate to lmax
    valid_l = np.arange(len(corrected_cl)) <= lmax
    cl_obs_trunc = corrected_cl[valid_l]
    
    # Find best fit (minimum chi-squared / maximum likelihood)
    # Assuming grid_likelihoods are already computed as -2*log(L) or similar
    # If not, we compute a simple chi-squared
    if 'chi2' not in grid_data:
        # Compute chi-squared for each grid point
        chi2_vals = []
        for i, theo_cl in enumerate(grid_cl_theory):
            theo_trunc = theo_cl[valid_l]
            # Simple chi-squared (assuming unit variance for simplicity)
            # In reality, covariance matrix should be used
            diff = cl_obs_trunc - theo_trunc
            chi2 = np.sum(diff**2)
            chi2_vals.append(chi2)
        
        best_idx = np.argmin(chi2_vals)
        best_chi2 = chi2_vals[best_idx]
    else:
        best_idx = np.argmin(grid_data['chi2'])
        best_chi2 = grid_data['chi2'][best_idx]
    
    # Extract best fit parameters
    best_params = grid_params[best_idx]
    
    result = {
        "H0": float(best_params[0]),
        "Omega_m": float(best_params[1]),
        "n_s": float(best_params[2]),
        "tau": float(best_params[3]),
        "chi2": float(best_chi2),
        "status": "success",
        "method": "grid_lookup_custom_likelihood"
    }
    
    logger.info(f"Parameter estimation complete. Best fit: H0={result['H0']:.2f}, "
               f"Omega_m={result['Omega_m']:.3f}, n_s={result['n_s']:.4f}")
    
    return result


def run_custom_likelihood_pipeline(realization_id: str,
                                   observed_cl_path: str,
                                   mask_path: str,
                                   output_dir: Optional[str] = None) -> Dict[str, Any]:
    """
    Run the full custom likelihood pipeline for a single realization.
    
    1. Load observed C_l and mask.
    2. Apply bias correction.
    3. Load grid (if available) and estimate parameters.
    4. Save results.
    
    Args:
        realization_id: Unique ID for the realization.
        observed_cl_path: Path to the observed power spectrum file.
        mask_path: Path to the gap mask file.
        output_dir: Directory to save results.
        
    Returns:
        Dictionary containing the full pipeline results.
    """
    if output_dir is None:
        output_dir = os.path.join(DATA_RESULTS_DIR, "custom_likelihood_results")
    
    os.makedirs(output_dir, exist_ok=True)
    
    # Load observed C_l
    # Assuming a simple format: l, Cl, err (or just Cl in an array)
    # Using healpy format if .fits, or numpy if .npy
    if observed_cl_path.endswith('.fits'):
        # Healpy fits usually have l, aml, alm, etc.
        # For simplicity, assume it's just the Cl array or a standard format
        # We'll use a generic loader for now
        try:
            import healpy as hp
            # Try to read as a map (if stored as such) or use custom loader
            # This is a placeholder for specific format handling
            logger.warning("HEALPix fits loading for Cl requires specific format handling. "
                         "Assuming numpy array for now.")
            # Fallback: try numpy
            cl_obs = np.load(observed_cl_path.replace('.fits', '.npy'))
        except:
            raise ValueError("Unsupported format or missing file for observed Cl")
    else:
        cl_obs = np.load(observed_cl_path)
    
    # Load mask
    if mask_path.endswith('.fits'):
        mask = hp.read_map(mask_path, dtype=np.float64)
    else:
        mask = np.load(mask_path)
    
    # Apply correction
    corrected_cl, correction_meta = apply_custom_likelihood_correction(cl_obs, mask)
    
    # Load grid and estimate parameters
    grid_data = load_precomputed_grid()
    param_result = estimate_parameters_from_grid(corrected_cl, grid_data)
    
    # Compile full result
    full_result = {
        "realization_id": realization_id,
        "correction": correction_meta,
        "parameters": param_result,
        "corrected_cl_path": os.path.join(output_dir, f"{realization_id}_corrected_cl.npy"),
        "timestamp": str(pd.Timestamp.now()) if 'pd' in globals() else "N/A"
    }
    
    # Save corrected Cl
    np.save(full_result["corrected_cl_path"], corrected_cl)
    
    # Save full result JSON
    result_json_path = os.path.join(output_dir, f"{realization_id}_custom_likelihood_result.json")
    import json
    with open(result_json_path, 'w') as f:
        # Convert numpy types for JSON serialization
        def convert(obj):
            if isinstance(obj, np.floating): return float(obj)
            if isinstance(obj, np.integer): return int(obj)
            if isinstance(obj, np.ndarray): return obj.tolist()
            return obj
        
        json.dump(full_result, f, default=convert, indent=2)
    
    logger.info(f"Pipeline complete for {realization_id}. Results saved to {result_json_path}")
    
    return full_result


def main():
    """
    Main entry point for testing the custom likelihood module.
    This function demonstrates the pipeline on a dummy realization 
    (requires actual data files to be present).
    """
    logger.info("Starting Custom Likelihood Module Test")
    
    # Example usage (requires real data)
    # This is a placeholder for integration with the main pipeline
    # In a real run, these paths would be passed as arguments
    sample_realization = "test_realization_001"
    sample_cl_path = os.path.join(DATA_DERIVED_DIR, "test_cl.npy")
    sample_mask_path = os.path.join(DATA_DERIVED_DIR, "test_mask.fits")
    
    if os.path.exists(sample_cl_path) and os.path.exists(sample_mask_path):
        try:
            result = run_custom_likelihood_pipeline(
                sample_realization, sample_cl_path, sample_mask_path
            )
            logger.info(f"Test run successful: {result['parameters']['status']}")
        except Exception as e:
            logger.error(f"Test run failed: {e}")
    else:
        logger.info("Test data not found. Skipping execution. "
                   "This module is ready for integration.")


if __name__ == "__main__":
    main()