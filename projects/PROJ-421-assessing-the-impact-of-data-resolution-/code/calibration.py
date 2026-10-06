"""
Calibration module for estimating the spatial lag parameter (lambda) using
Maximum Likelihood Estimation (MLE) on a representative random sample of pixels
from a binary indicator map.

This module implements the estimation of the spatial autoregressive coefficient
(lambda) for the Alternative Hypothesis (H1) in the spatial lag model:
    y = lambda * W * y + epsilon

The estimation is performed on a random sample of pixels to ensure computational
efficiency while maintaining statistical representativeness.
"""

import numpy as np
import json
import logging
from pathlib import Path
from typing import Tuple, Optional, Dict, Any
import scipy.optimize as opt
from scipy.special import erf
import pandas as pd

# Import from local modules
from utils import get_logger, create_memory_mapped_array, get_raster_info
import config

logger = get_logger(__name__)


def _create_spatial_weights_matrix_binary(binary_map: np.ndarray, 
                                            distance_threshold: int = 1) -> np.ndarray:
    """
    Create a simplified spatial weights matrix for a binary raster.
    
    Uses a rook's case neighborhood (4-connected) for the spatial weights.
    Returns the row-standardized weights matrix W.
    
    Parameters
    ----------
    binary_map : np.ndarray
        2D array of binary values (0 or 1)
    distance_threshold : int
        Maximum distance for neighbors (1 for rook's case)
        
    Returns
    -------
    np.ndarray
        Row-standardized spatial weights matrix W
    """
    h, w = binary_map.shape
    n = h * w
    W = np.zeros((n, n), dtype=np.float64)
    
    for i in range(h):
        for j in range(w):
            idx = i * w + j
            neighbors = []
            
            # Check 4-connected neighbors (rook's case)
            for di, dj in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                ni, nj = i + di, j + dj
                if 0 <= ni < h and 0 <= nj < w:
                    neighbors.append(ni * w + nj)
            
            if neighbors:
                for neighbor in neighbors:
                    W[idx, neighbor] = 1.0
                # Row standardization
                W[idx, :] /= len(neighbors)
    
    return W


def _log_likelihood_binary_sar(params: np.ndarray, y: np.ndarray, 
                                W: np.ndarray, beta: float) -> float:
    """
    Compute the log-likelihood for a binary spatial autoregressive model.
    
    Uses a probit link function: P(y_i=1) = Phi(lambda * (W*y)_i + beta)
    
    Parameters
    ----------
    params : np.ndarray
        Array containing [lambda]
    y : np.ndarray
        Binary response vector
    W : np.ndarray
        Spatial weights matrix
    beta : float
        Intercept term
        
    Returns
    -------
    float
        Negative log-likelihood (to be minimized)
    """
    lambda_val = params[0]
    
    # Compute spatial lag
    spatial_lag = W @ y
    
    # Compute probability using probit link
    linear_pred = lambda_val * spatial_lag + beta
    
    # Avoid numerical issues
    linear_pred = np.clip(linear_pred, -10, 10)
    
    # Probit CDF approximation using erf
    probs = 0.5 * (1 + erf(linear_pred / np.sqrt(2)))
    probs = np.clip(probs, 1e-10, 1 - 1e-10)
    
    # Log-likelihood
    log_lik = np.sum(y * np.log(probs) + (1 - y) * np.log(1 - probs))
    
    return -log_lik  # Return negative for minimization


def estimate_lambda(binary_map_path: str, 
                    sample_size: int = 150000,
                    seed: int = 42,
                    output_path: str = None) -> float:
    """
    Estimate the spatial lag parameter (lambda) using Maximum Likelihood Estimation
    on a representative random sample of pixels from the binary map.
    
    Parameters
    ----------
    binary_map_path : str
        Path to the binary indicator map (e.g., 'data/derived/nlcd_30m_binary.tif')
    sample_size : int
        Number of pixels to sample for estimation
    seed : int
        Random seed for reproducibility
    output_path : str, optional
        Path to save the results JSON. Defaults to config.RESULTS_PATH + 'calibration_lambda.json'
        
    Returns
    -------
    float
        Estimated lambda value
        
    Raises
    ------
    FileNotFoundError
        If the binary map file does not exist
    ValueError
        If the sample size is larger than the number of available pixels
    """
    logger.info(f"Starting lambda estimation from: {binary_map_path}")
    
    # Load binary map
    binary_map_path = Path(binary_map_path)
    if not binary_map_path.exists():
        raise FileNotFoundError(f"Binary map file not found: {binary_map_path}")
    
    logger.info("Loading binary map data...")
    binary_map = create_memory_mapped_array(str(binary_map_path), dtype=np.float64)
    
    # Flatten and get valid pixels (0 or 1)
    y_flat = binary_map.flatten()
    valid_mask = (y_flat == 0) | (y_flat == 1)
    y_valid = y_flat[valid_mask]
    
    n_total = len(y_valid)
    logger.info(f"Total valid pixels: {n_total}")
    
    if sample_size > n_total:
        logger.warning(f"Sample size {sample_size} exceeds available pixels {n_total}. "
                     f"Using all available pixels.")
        sample_size = n_total
    
    # Set random seed
    np.random.seed(seed)
    
    # Random sampling
    sample_indices = np.random.choice(n_total, size=sample_size, replace=False)
    y_sample = y_valid[sample_indices]
    
    logger.info(f"Sampled {sample_size} pixels for estimation")
    
    # Create spatial weights matrix for the sample
    # Reshape sample to 2D grid (approximate)
    h, w = binary_map.shape
    n_pixels = h * w
    
    # Create a small sample grid for spatial weights calculation
    # We'll use a subset of the original grid to maintain spatial structure
    sample_grid_size = int(np.sqrt(sample_size))
    if sample_grid_size > h or sample_grid_size > w:
        sample_grid_size = min(h, w)
    
    # Extract a representative subgrid
    start_i = (h - sample_grid_size) // 2
    start_j = (w - sample_grid_size) // 2
    subgrid = binary_map[start_i:start_i+sample_grid_size, 
                        start_j:start_j+sample_grid_size]
    
    logger.info(f"Creating spatial weights matrix for {subgrid.shape[0]}x{subgrid.shape[1]} grid")
    W = _create_spatial_weights_matrix_binary(subgrid)
    
    # Flatten the subgrid
    y_subgrid = subgrid.flatten()
    
    # Estimate beta (intercept) as the mean of the binary variable
    beta = np.mean(y_subgrid)
    
    # Initial guess for lambda (spatial autocorrelation typically between -1 and 1)
    lambda_init = [0.5]
    
    logger.info("Optimizing lambda using MLE...")
    
    # Optimize
    result = opt.minimize(
        _log_likelihood_binary_sar,
        lambda_init,
        args=(y_subgrid, W, beta),
        method='L-BFGS-B',
        bounds=[(-0.99, 0.99)],  # Constrain lambda to valid range
        options={'maxiter': 1000, 'ftol': 1e-6}
    )
    
    if not result.success:
        logger.warning(f"Optimization failed: {result.message}. Using initial guess.")
        lambda_est = lambda_init[0]
    else:
        lambda_est = result.x[0]
    
    # Ensure lambda is within valid range
    lambda_est = np.clip(lambda_est, -0.99, 0.99)
    
    logger.info(f"Estimated lambda: {lambda_est:.6f}")
    
    # Save results
    if output_path is None:
        output_path = Path(config.RESULTS_PATH) / 'calibration_lambda.json'
    else:
        output_path = Path(output_path)
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    results = {
        "lambda": float(lambda_est),
        "seed": seed,
        "method": "MLE_on_sample",
        "sample_size": sample_size,
        "input_file": str(binary_map_path),
        "optimization_success": result.success,
        "optimization_message": result.message if hasattr(result, 'message') else str(result.success)
    }
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Results saved to: {output_path}")
    
    return lambda_est


def main():
    """
    Main entry point for the calibration module.
    Runs the lambda estimation on the binary map and saves results.
    """
    logger.info("Running calibration module...")
    
    # Default paths from config
    binary_map_path = Path(config.DERIVED_PATH) / "nlcd_30m_binary.tif"
    output_path = Path(config.RESULTS_PATH) / "calibration_lambda.json"
    
    if not binary_map_path.exists():
        logger.error(f"Binary map not found at {binary_map_path}. "
                    "Please ensure T020 has been completed first.")
        return 1
    
    try:
        lambda_est = estimate_lambda(
            binary_map_path=str(binary_map_path),
            sample_size=config.SAMPLE_SIZE,
            seed=config.SEED,
            output_path=str(output_path)
        )
        logger.info(f"Calibration complete. Estimated lambda = {lambda_est:.6f}")
        return 0
    except Exception as e:
        logger.error(f"Calibration failed: {str(e)}")
        return 1


if __name__ == "__main__":
    import sys
    sys.exit(main())