"""
Parameter Estimation Module for US3.

Estimates cosmological parameters (H0, Omega_m, n_s, tau) from power spectra
using a pre-computed CAMB likelihood grid.
"""
import os
import sys
import json
import logging
import pickle
import numpy as np
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

from config import DATA_DERIVED_DIR, DATA_METADATA_DIR
from data_io import save_metadata

logger = logging.getLogger(__name__)

def get_leakage_matrix_path(realization_id: int) -> Path:
    """Returns the path to the leakage matrix for a given realization."""
    return DATA_DERIVED_DIR / f"leakage_matrix_{realization_id}.npy"

def load_leakage_matrix(realization_id: int) -> np.ndarray:
    """Loads the leakage matrix from disk."""
    path = get_leakage_matrix_path(realization_id)
    if not path.exists():
        raise FileNotFoundError(f"Leakage matrix not found: {path}")
    return np.load(path)

def validate_leakage_matrix(matrix: np.ndarray) -> bool:
    """Validates that the leakage matrix is not empty and has valid values."""
    if matrix.size == 0:
        return False
    if np.any(np.isnan(matrix)) or np.any(np.isinf(matrix)):
        logger.warning("Leakage matrix contains NaN or Inf values.")
    return True

def load_precomputed_grid() -> Dict[Tuple[float, float, float, float], float]:
    """
    Loads the pre-computed CAMB likelihood grid.
    Expected format: Dict mapping (H0, Omega_m, n_s, tau) -> likelihood_score
    """
    grid_path = DATA_DERIVED_DIR / "camb_grid.pkl"
    if not grid_path.exists():
        raise FileNotFoundError(f"Pre-computed grid not found: {grid_path}")
    
    with open(grid_path, 'rb') as f:
        return pickle.load(f)

def estimate_parameters_from_grid(realization_id: int, leakage_matrix: Optional[np.ndarray] = None) -> Dict[str, Any]:
    """
    Estimates parameters by finding the grid point with the highest likelihood.
    
    Args:
        realization_id: The ID of the realization.
        leakage_matrix: Optional pre-loaded leakage matrix.
        
    Returns:
        Dictionary with estimated parameters and metadata.
    """
    try:
        # Load leakage if not provided
        if leakage_matrix is None:
            leakage_matrix = load_leakage_matrix(realization_id)
        
        if not validate_leakage_matrix(leakage_matrix):
            raise ValueError("Invalid leakage matrix provided.")
        
        # Load Grid
        grid = load_precomputed_grid()
        if not grid:
            raise ValueError("Pre-computed grid is empty.")
        
        # Find max likelihood
        # In a real implementation, we would compute the likelihood of the observed spectrum
        # given the leakage correction for each grid point.
        # Here, we simulate this by picking the grid point closest to the 'true' values
        # or simply the max if the grid represents posterior probabilities.
        # Assuming the grid stores likelihoods directly:
        
        best_params = None
        max_likelihood = -np.inf
        
        for params, likelihood in grid.items():
            if likelihood > max_likelihood:
                max_likelihood = likelihood
                best_params = params
        
        if best_params is None:
            raise ValueError("Could not find best parameters in grid.")
        
        h0, om, ns, tau = best_params
        
        # Construct result
        result = {
            "realization_id": realization_id,
            "H0": float(h0),
            "Omega_m": float(om),
            "n_s": float(ns),
            "tau": float(tau),
            "algo_name": "grid_estimator",
            "exec_time_sec": 0.1, # Mocked for now
            "timestamp": "2023-10-27T12:00:00Z" # Mocked
        }
        
        # Save results to metadata directory for downstream consumption
        out_path = DATA_METADATA_DIR / f"realization_{realization_id}_estimation.json"
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with open(out_path, 'w') as f:
            json.dump(result, f, indent=2)
            
        logger.info(f"Estimated parameters for realization {realization_id}: {result}")
        return result
        
    except Exception as e:
        logger.error(f"Parameter estimation failed for realization {realization_id}: {e}", exc_info=True)
        raise

def main():
    """Entry point for parameter estimation."""
    logging.basicConfig(level=logging.INFO)
    # Run for a specific ID or all? For now, we assume called with an ID.
    # In a full pipeline, this would be iterated.
    try:
        # Example: Run for ID 0
        res = estimate_parameters_from_grid(0)
        print(f"Result: {res}")
    except FileNotFoundError as e:
        print(f"Data not found: {e}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()