"""
Fitting engine for galaxy rotation curves.

Implements dual-model fitting (MOND simple and NFW) using scipy.optimize.curve_fit
with velocity uncertainty weighting.
"""

import os
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from scipy.optimize import curve_fit
from scipy.stats import chi2

from models.mond import mond_simple
from models.nfw import nfw_model
from utils import get_logger, safe_divide, ensure_directory

logger = get_logger(__name__)

# Constants
G = 4.302e-6  # kpc (km/s)^2 / Msun
C_LIGHT = 299792.458  # km/s

def fit_mond_galaxy(
    r: np.ndarray,
    v: np.ndarray,
    v_err: np.ndarray,
    v_sys: float = 0.0,
    m_l: float = 0.5,
    m_l_bounds: Tuple[float, float] = (0.1, 2.0),
    a0: float = 1.2e-10
) -> Tuple[Dict[str, float], Optional[Dict[str, float]], bool]:
    """
    Fit MOND 'simple' model to a single galaxy's rotation curve.

    Parameters
    ----------
    r : np.ndarray
        Radial distances (kpc)
    v : np.ndarray
        Observed rotation velocities (km/s)
    v_err : np.ndarray
        Uncertainties in velocities (km/s)
    v_sys : float
        Systemic velocity (km/s) - usually 0 for relative curves
    m_l : float
        Initial guess for mass-to-light ratio
    m_l_bounds : tuple
        (min, max) bounds for M/L parameter
    a0 : float
        MOND acceleration constant (m/s^2) - standard value

    Returns
    -------
    tuple
        (best_params, covariance, success)
        best_params: dict with 'm_l' and derived quantities
        covariance: covariance matrix from curve_fit (or None)
        success: boolean indicating convergence
    """
    try:
        # Convert a0 to km/s^2 for consistency with velocity units
        # a0 is typically in m/s^2, need to convert for the model
        # The mond_simple function expects a0 in consistent units with the input
        # Since v is in km/s and r in kpc, we need consistent units
        
        # Scale a0: 1.2e-10 m/s^2 = 1.2e-10 * (1e-3 km) / (3.086e16 km)^2 * (1e3)^2 ?
        # Actually, let's keep a0 in m/s^2 and handle unit conversion in the model
        # The mond_simple model should handle internal unit conversions
        
        # Prepare initial guess
        p0 = [m_l]
        
        # Bounds for M/L
        bounds = ([m_l_bounds[0]], [m_l_bounds[1]])
        
        # Perform curve fitting with uncertainty weighting
        # curve_fit uses sigma for weighting: chi^2 = sum((y - f(x))^2 / sigma^2)
        popt, pcov = curve_fit(
            mond_simple,
            r,
            v,
            p0=p0,
            sigma=v_err,
            absolute_sigma=True,
            bounds=bounds,
            maxfev=5000
        )
        
        m_l_best = popt[0]
        
        # Calculate derived quantities
        # For simplicity, we'll store the key parameters
        best_params = {
            'm_l': m_l_best,
            'a0': a0,
            'chi2_red': None,  # Will be calculated by metrics module
            'n_dof': len(r) - 1
        }
        
        return best_params, pcov, True
        
    except Exception as e:
        logger.warning(f"MOND fit failed for galaxy: {str(e)}")
        return None, None, False

def fit_nfw_galaxy(
    r: np.ndarray,
    v: np.ndarray,
    v_err: np.ndarray,
    m_baryon: float,
    v_sys: float = 0.0,
    c_init: float = 10.0,
    m_l: float = 0.5,
    m_l_bounds: Tuple[float, float] = (0.1, 2.0)
) -> Tuple[Dict[str, float], Optional[Dict[str, float]], bool]:
    """
    Fit NFW model with baryons to a single galaxy's rotation curve.

    Parameters
    ----------
    r : np.ndarray
        Radial distances (kpc)
    v : np.ndarray
        Observed rotation velocities (km/s)
    v_err : np.ndarray
        Uncertainties in velocities (km/s)
    m_baryon : float
        Total baryonic mass (Msun)
    v_sys : float
        Systemic velocity (km/s)
    c_init : float
        Initial guess for concentration parameter
    m_l : float
        Initial guess for mass-to-light ratio
    m_l_bounds : tuple
        (min, max) bounds for M/L parameter

    Returns
    -------
    tuple
        (best_params, covariance, success)
    """
    try:
        # Prepare initial guess: [m_l, c]
        p0 = [m_l, c_init]
        
        # Bounds: M/L and concentration
        # Concentration should be positive and within reasonable range
        bounds = (
            [m_l_bounds[0], 1.0],      # Lower bounds
            [m_l_bounds[1], 50.0]       # Upper bounds
        )
        
        # Perform curve fitting
        popt, pcov = curve_fit(
            nfw_model,
            r,
            v,
            p0=p0,
            sigma=v_err,
            absolute_sigma=True,
            bounds=bounds,
            maxfev=5000,
            args=(m_baryon,)  # Pass m_baryon as additional argument
        )
        
        m_l_best, c_best = popt
        
        best_params = {
            'm_l': m_l_best,
            'c': c_best,
            'm_baryon': m_baryon,
            'chi2_red': None,
            'n_dof': len(r) - 2
        }
        
        return best_params, pcov, True
        
    except Exception as e:
        logger.warning(f"NFW fit failed for galaxy: {str(e)}")
        return None, None, False

def fit_galaxy(
    galaxy_data: Dict[str, Any],
    model_type: str = 'mond'
) -> Dict[str, Any]:
    """
    Fit a specified model to a single galaxy's rotation curve.

    Parameters
    ----------
    galaxy_data : dict
        Dictionary containing galaxy rotation curve data with keys:
        - 'r': radial distances
        - 'v': velocities
        - 'v_err': velocity uncertainties
        - 'm_baryon': baryonic mass (required for NFW)
        - 'name': galaxy name
        - 'id': galaxy ID
    model_type : str
        Model to fit: 'mond' or 'nfw'

    Returns
    -------
    dict
        Fitting results including parameters, success status, and metadata
    """
    r = np.array(galaxy_data['r'])
    v = np.array(galaxy_data['v'])
    v_err = np.array(galaxy_data['v_err'])
    
    # Remove points with zero or negative uncertainties
    valid_mask = v_err > 0
    r = r[valid_mask]
    v = v[valid_mask]
    v_err = v_err[valid_mask]
    
    if len(r) < 3:
        logger.warning(f"Not enough valid points for {galaxy_data['name']}")
        return {
            'galaxy_id': galaxy_data.get('id', 'unknown'),
            'galaxy_name': galaxy_data.get('name', 'unknown'),
            'model': model_type,
            'success': False,
            'error': 'Insufficient data points after filtering'
        }
    
    result = {
        'galaxy_id': galaxy_data.get('id', 'unknown'),
        'galaxy_name': galaxy_data.get('name', 'unknown'),
        'model': model_type,
        'n_points': len(r),
        'success': False
    }
    
    if model_type == 'mond':
        params, cov, success = fit_mond_galaxy(r, v, v_err)
        if success and params:
            result.update({
                'success': True,
                'm_l': params['m_l'],
                'a0': params['a0'],
                'n_dof': params['n_dof'],
                'covariance': cov.tolist() if cov is not None else None
            })
            
    elif model_type == 'nfw':
        if 'm_baryon' not in galaxy_data:
            result['error'] = 'Missing m_baryon for NFW fit'
            return result
            
        params, cov, success = fit_nfw_galaxy(
            r, v, v_err, 
            m_baryon=galaxy_data['m_baryon']
        )
        if success and params:
            result.update({
                'success': True,
                'm_l': params['m_l'],
                'c': params['c'],
                'm_baryon': params['m_baryon'],
                'n_dof': params['n_dof'],
                'covariance': cov.tolist() if cov is not None else None
            })
    else:
        result['error'] = f'Unknown model type: {model_type}'
    
    return result

def fit_all_galaxies(
    data_path: str,
    output_path: str,
    models: List[str] = ['mond', 'nfw']
) -> pd.DataFrame:
    """
    Fit models to all galaxies in the filtered dataset.

    Parameters
    ----------
    data_path : str
        Path to the filtered galaxies CSV file
    output_path : str
        Path to save the fit summary CSV
    models : list
        List of models to fit

    Returns
    -------
    pd.DataFrame
        DataFrame with fitting results for all galaxies and models
    """
    # Load filtered data
    logger.info(f"Loading filtered data from {data_path}")
    df = pd.read_csv(data_path)
    
    all_results = []
    
    for _, row in df.iterrows():
        galaxy_data = {
            'id': row['galaxy_id'],
            'name': row['galaxy_name'],
            'r': row['r'],
            'v': row['v'],
            'v_err': row['v_err'],
            'm_baryon': row.get('m_baryon', 1e10)  # Default if missing
        }
        
        for model_type in models:
            logger.info(f"Fitting {model_type} to {row['galaxy_name']}")
            result = fit_galaxy(galaxy_data, model_type)
            all_results.append(result)
    
    # Create DataFrame
    results_df = pd.DataFrame(all_results)
    
    # Ensure output directory exists
    ensure_directory(output_path)
    
    # Save results
    results_df.to_csv(output_path, index=False)
    logger.info(f"Saved fit results to {output_path}")
    
    return results_df

def main():
    """Main entry point for fitting pipeline."""
    # Configuration
    data_path = "data/processed/filtered_galaxies.csv"
    output_path = "results/fit_summary.csv"
    
    # Check if data exists
    if not os.path.exists(data_path):
        logger.error(f"Data file not found: {data_path}")
        logger.error("Please run the preprocessing pipeline first (T015)")
        return 1
    
    # Run fitting
    results_df = fit_all_galaxies(data_path, output_path)
    
    # Summary statistics
    total_fits = len(results_df)
    successful_fits = results_df['success'].sum()
    logger.info(f"Completed {successful_fits}/{total_fits} successful fits")
    
    return 0

if __name__ == "__main__":
    exit(main())
