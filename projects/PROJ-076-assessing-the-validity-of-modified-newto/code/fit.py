"""
Fitting engine for MOND and NFW models to galaxy rotation curves.
Uses scipy.optimize.curve_fit with velocity uncertainty weighting.
"""
import os
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from scipy.optimize import curve_fit
from scipy.stats import chi2

# Import models from sibling files
from models.mond import mond_simple_velocity
from models.nfw import nfw_with_baryons
from utils import get_logger, set_global_seed

# Initialize logger
logger = get_logger(__name__)

def fit_mond_galaxy(
    r: np.ndarray,
    v_obs: np.ndarray,
    v_err: np.ndarray,
    v_sys: float = 0.0,
    a0: float = 1.2e-10,
    seed: Optional[int] = None
) -> Dict[str, Any]:
    """
    Fit the MOND 'simple' model to a single galaxy's rotation curve.

    Parameters
    ----------
    r : np.ndarray
        Radial distances (kpc)
    v_obs : np.ndarray
        Observed circular velocities (km/s)
    v_err : np.ndarray
        Uncertainties in observed velocities (km/s)
    v_sys : float
        Systemic velocity offset (km/s), default 0.0
    a0 : float
        MOND acceleration constant (m/s^2), default 1.2e-10
    seed : int, optional
        Random seed for reproducibility

    Returns
    -------
    dict
        Fitting results including parameters, covariance, success status, and message.
    """
    if seed is not None:
        set_global_seed(seed)

    # Initial guess for M/L ratio (mass-to-light ratio)
    # Typical values range from 0.5 to 2.0
    initial_guess = [1.0]  # [M/L]

    try:
        # Define the wrapper function for curve_fit
        def mond_wrapper(r, ml):
            return mond_simple_velocity(r, ml, a0, v_sys)

        # Perform curve fitting with uncertainties as weights
        popt, pcov = curve_fit(
            mond_wrapper,
            r,
            v_obs,
            p0=initial_guess,
            sigma=v_err,
            absolute_sigma=True,
            maxfev=5000
        )

        perr = np.sqrt(np.diag(pcov))

        return {
            "success": True,
            "params": {"M/L": popt[0]},
            "param_errors": {"M/L": perr[0]},
            "covariance": pcov.tolist(),
            "message": "Fit converged successfully"
        }

    except Exception as e:
        logger.warning(f"MOND fit failed for galaxy: {str(e)}")
        return {
            "success": False,
            "params": {},
            "param_errors": {},
            "covariance": [],
            "message": str(e)
        }

def fit_nfw_galaxy(
    r: np.ndarray,
    v_obs: np.ndarray,
    v_err: np.ndarray,
    v_sys: float = 0.0,
    M_baryon: float = 1.0e10,
    alpha: float = 0.24,
    c_std: float = 0.1,
    seed: Optional[int] = None
) -> Dict[str, Any]:
    """
    Fit the NFW model with baryons to a single galaxy's rotation curve.

    Parameters
    ----------
    r : np.ndarray
        Radial distances (kpc)
    v_obs : np.ndarray
        Observed circular velocities (km/s)
    v_err : np.ndarray
        Uncertainties in observed velocities (km/s)
    v_sys : float
        Systemic velocity offset (km/s), default 0.0
    M_baryon : float
        Baryonic mass (solar masses), default 1.0e10
    alpha : float
        Exponent for concentration prior (FR-005), default 0.24
    c_std : float
        Standard deviation for concentration prior in dex, default 0.1
    seed : int, optional
        Random seed for reproducibility

    Returns
    -------
    dict
        Fitting results including parameters, covariance, success status, and message.
    """
    if seed is not None:
        set_global_seed(seed)

    # Initial guess for scale radius (kpc)
    # Typical values range from 5 to 50 kpc
    initial_guess = [10.0]  # [r_s]

    try:
        # Define the wrapper function for curve_fit
        def nfw_wrapper(r, r_s):
            return nfw_with_baryons(r, r_s, M_baryon, alpha, c_std, v_sys)

        # Perform curve fitting with uncertainties as weights
        popt, pcov = curve_fit(
            nfw_wrapper,
            r,
            v_obs,
            p0=initial_guess,
            sigma=v_err,
            absolute_sigma=True,
            maxfev=5000,
            bounds=(0, np.inf)  # Scale radius must be positive
        )

        perr = np.sqrt(np.diag(pcov))

        return {
            "success": True,
            "params": {"r_s": popt[0]},
            "param_errors": {"r_s": perr[0]},
            "covariance": pcov.tolist(),
            "message": "Fit converged successfully"
        }

    except Exception as e:
        logger.warning(f"NFW fit failed for galaxy: {str(e)}")
        return {
            "success": False,
            "params": {},
            "param_errors": {},
            "covariance": [],
            "message": str(e)
        }

def fit_galaxy(
    galaxy_data: Dict[str, Any],
    model_type: str = "mond",
    seed: Optional[int] = None
) -> Dict[str, Any]:
    """
    Fit a specified model to a single galaxy's rotation curve.

    Parameters
    ----------
    galaxy_data : dict
        Dictionary containing galaxy data with keys:
        - 'r': radial distances
        - 'v_obs': observed velocities
        - 'v_err': velocity uncertainties
        - 'v_sys': systemic velocity (optional)
        - 'M_baryon': baryonic mass (for NFW)
        - 'galaxy_id': identifier
    model_type : str
        Model to fit: "mond" or "nfw"
    seed : int, optional
        Random seed for reproducibility

    Returns
    -------
    dict
        Combined fitting results with galaxy_id and model_type.
    """
    r = np.array(galaxy_data['r'])
    v_obs = np.array(galaxy_data['v_obs'])
    v_err = np.array(galaxy_data['v_err'])
    v_sys = galaxy_data.get('v_sys', 0.0)
    galaxy_id = galaxy_data.get('galaxy_id', 'unknown')

    if model_type == "mond":
        a0 = galaxy_data.get('a0', 1.2e-10)
        result = fit_mond_galaxy(r, v_obs, v_err, v_sys, a0, seed)
    elif model_type == "nfw":
        M_baryon = galaxy_data.get('M_baryon', 1.0e10)
        alpha = galaxy_data.get('alpha', 0.24)
        c_std = galaxy_data.get('c_std', 0.1)
        result = fit_nfw_galaxy(r, v_obs, v_err, v_sys, M_baryon, alpha, c_std, seed)
    else:
        raise ValueError(f"Unknown model type: {model_type}")

    result['galaxy_id'] = galaxy_id
    result['model_type'] = model_type
    return result

def fit_all_galaxies(
    galaxies: List[Dict[str, Any]],
    models: List[str] = ["mond", "nfw"],
    seed: Optional[int] = None
) -> List[Dict[str, Any]]:
    """
    Fit all specified models to all galaxies in the dataset.

    Parameters
    ----------
    galaxies : list of dict
        List of galaxy data dictionaries
    models : list of str
        Models to fit for each galaxy
    seed : int, optional
        Random seed for reproducibility

    Returns
    -------
    list of dict
        List of fitting results for each galaxy-model combination.
    """
    all_results = []

    for galaxy in galaxies:
        for model_type in models:
            logger.info(f"Fitting {model_type} model to galaxy {galaxy.get('galaxy_id', 'unknown')}")
            result = fit_galaxy(galaxy, model_type, seed)
            all_results.append(result)

    return all_results

def main():
    """
    Main entry point for the fitting engine.
    Loads filtered galaxy data, fits models, and saves results.
    """
    # Load configuration
    from config import load_config
    config = load_config()

    # Set global seed if specified
    seed = config.get('random_seed')
    if seed is not None:
        set_global_seed(seed)

    # Load filtered galaxy data
    data_path = Path(config.get('data', {}).get('processed_path', 'data/processed/filtered_galaxies.csv'))
    if not data_path.exists():
        logger.error(f"Data file not found: {data_path}")
        return

    df = pd.read_csv(data_path)
    logger.info(f"Loaded {len(df)} galaxies from {data_path}")

    # Convert dataframe to list of galaxy dictionaries
    galaxies = []
    for _, row in df.iterrows():
        galaxy = {
            'galaxy_id': row['galaxy_id'],
            'r': np.array(row['r'].strip('[]').split(), dtype=float),
            'v_obs': np.array(row['v_obs'].strip('[]').split(), dtype=float),
            'v_err': np.array(row['v_err'].strip('[]').split(), dtype=float),
            'v_sys': row.get('v_sys', 0.0),
            'M_baryon': row.get('M_baryon', 1.0e10),
            'a0': row.get('a0', 1.2e-10),
            'alpha': row.get('alpha', 0.24),
            'c_std': row.get('c_std', 0.1)
        }
        galaxies.append(galaxy)

    # Fit all models
    models = config.get('models', ['mond', 'nfw'])
    results = fit_all_galaxies(galaxies, models, seed)

    # Save results
    output_path = Path(config.get('results', {}).get('fit_results_path', 'results/fit_results.csv'))
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Convert results to DataFrame for saving
    results_list = []
    for res in results:
        row = {
            'galaxy_id': res['galaxy_id'],
            'model_type': res['model_type'],
            'success': res['success'],
            'message': res['message']
        }
        if res['success']:
            for param, value in res['params'].items():
                row[f'{param}_value'] = value
            for param, error in res['param_errors'].items():
                row[f'{param}_error'] = error
        results_list.append(row)

    results_df = pd.DataFrame(results_list)
    results_df.to_csv(output_path, index=False)
    logger.info(f"Saved fitting results to {output_path}")

    return results

if __name__ == "__main__":
    main()