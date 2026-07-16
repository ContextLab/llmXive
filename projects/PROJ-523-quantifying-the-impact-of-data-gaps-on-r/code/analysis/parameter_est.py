"""
Parameter estimation from power spectra using pre-computed CAMB grids.
Optimized for memory by using float32 for grid lookups and intermediate arrays.
"""
import os
import sys
import logging
import numpy as np
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from config import DATA_DERIVED_DIR, DATA_RESULTS_DIR, get_dtype, FORCE_FLOAT32

logger = logging.getLogger(__name__)

def get_leakage_matrix_path(realization_id: str) -> Path:
    return DATA_DERIVED_DIR / f"leakage_matrix_{realization_id}.npy"

def load_leakage_matrix(realization_id: str) -> np.ndarray:
    path = get_leakage_matrix_path(realization_id)
    if not path.exists():
        raise FileNotFoundError(f"Leakage matrix not found at {path}")
    
    matrix = np.load(path)
    if FORCE_FLOAT32 and matrix.dtype != np.float32:
        matrix = matrix.astype(np.float32)
    return matrix

def validate_leakage_matrix(matrix: np.ndarray) -> bool:
    if matrix.ndim != 2:
        logger.error("Leakage matrix must be 2D")
        return False
    if np.any(np.isnan(matrix)):
        logger.error("Leakage matrix contains NaN values")
        return False
    return True

def estimate_parameters_from_grid(cl_obs: np.ndarray, grid_path: Path, leakage_matrix: Optional[np.ndarray] = None) -> Dict[str, float]:
    """
    Estimates cosmological parameters by querying a pre-computed CAMB grid.
    Applies leakage correction if a matrix is provided.
    Uses float32 for grid data to save memory.
    """
    import pickle
    
    logger.info("Loading pre-computed CAMB grid...")
    with open(grid_path, 'rb') as f:
        grid_data = pickle.load(f)
    
    # Ensure grid data is float32 if configured
    if FORCE_FLOAT32:
        if 'theoretical_cl' in grid_data:
            grid_data['theoretical_cl'] = grid_data['theoretical_cl'].astype(np.float32)
    
    # Apply leakage correction if available
    if leakage_matrix is not None:
        logger.info("Applying leakage correction...")
        # Simple correction: cl_corrected = inv(leakage) @ cl_obs
        # For memory safety, we might do this element-wise or block-wise
        # Assuming leakage_matrix is diagonal or simplified for this task
        if leakage_matrix.ndim == 1:
            cl_corrected = cl_obs / leakage_matrix
        else:
            # Full matrix multiplication (might be heavy, but necessary for accuracy)
            # Ensure cl_obs is float32
            if cl_obs.dtype != np.float32:
                cl_obs = cl_obs.astype(np.float32)
            cl_corrected = np.linalg.solve(leakage_matrix, cl_obs)
    else:
        cl_corrected = cl_obs

    # Find best fit in grid
    # Chi-squared calculation
    best_chi2 = np.inf
    best_params = {}
    
    # Iterate over grid (assuming grid_data has 'params' and 'cl')
    # This is a simplified example
    for i, params in enumerate(grid_data['params']):
        theo_cl = grid_data['theoretical_cl'][i]
        
        # Ensure types match
        if theo_cl.dtype != cl_corrected.dtype:
            theo_cl = theo_cl.astype(cl_corrected.dtype)
        
        # Chi-squared
        diff = cl_corrected - theo_cl
        chi2 = np.sum(diff ** 2)
        
        if chi2 < best_chi2:
            best_chi2 = chi2
            best_params = {k: v for k, v in zip(grid_data['param_names'], params)}
    
    logger.info(f"Best fit parameters found: {best_params} with chi2={best_chi2}")
    return best_params

def main():
    """
    Main entry point for parameter estimation.
    """
    logging.basicConfig(level=logging.INFO)
    logger.info("Parameter estimation module loaded.")

if __name__ == "__main__":
    main()
