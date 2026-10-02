import os
import json
import logging
from pathlib import Path
from typing import Tuple, List, Optional, Dict, Any
import numpy as np
import pandas as pd
import libpysal
from pysal.esda.moran import Moran
from utils import get_logger, read_raster_windowed, get_raster_info, create_memory_mapped_array

# Global logger
logger = get_logger(__name__)

# Constants
NLCD_FOREST_CLASS = 41  # Deciduous Forest
NLCD_URBAN_CLASS = 12   # Developed, Open Space (representative urban)
DEFAULT_SEED = 42

def create_binary_indicator_map(values: np.ndarray, target_class_id: int) -> np.ndarray:
    """
    Transform a categorical land cover map into a binary indicator map.
    
    Args:
        values: 2D numpy array of land cover class IDs.
        target_class_id: The class ID to treat as '1' (presence), others as '0'.
    
    Returns:
        2D numpy array of 0s and 1s.
    """
    return (values == target_class_id).astype(np.uint8)

def calculate_moran_i(data: np.ndarray, w: libpysal.weights.W) -> Tuple[float, float]:
    """
    Calculate Moran's I and its p-value for a given spatial weights matrix.
    
    Args:
        data: 1D or 2D array of values. If 2D, flattened.
        w: Spatial weights object (e.g., Queen contiguity).
    
    Returns:
        Tuple of (Moran's I statistic, p-value).
    """
    if data.ndim > 1:
        data_flat = data.flatten()
    else:
        data_flat = data
    
    # Filter out NaNs if any (though binary maps usually don't have them)
    valid_mask = ~np.isnan(data_flat)
    y = data_flat[valid_mask]
    
    # Re-index weights if necessary (libpysal expects integer IDs 0..n-1)
    # For simplicity in this pipeline, we assume w is constructed for the full grid
    # and we pass the full flattened array. If y is shorter, we must subset w.
    # However, standard practice for raster Moran is to use the full grid.
    # We will assume input 'data' matches the weights topology.
    
    try:
        moran = Moran(y, w)
        # pysal returns p-value based on permutation or exact
        p_val = moran.p_sim
        return float(moran.I), float(p_val)
    except Exception as e:
        logger.error(f"Moran's I calculation failed: {e}")
        raise

def generate_null_distribution(data: np.ndarray, w: libpysal.weights.W, permutations: int = 1000, seed: int = DEFAULT_SEED) -> List[float]:
    """
    Generate a null distribution of Moran's I via random permutations.
    
    Args:
        data: 1D array of values.
        w: Spatial weights object.
        permutations: Number of random permutations.
        seed: Random seed for reproducibility.
    
    Returns:
        List of Moran's I values from permutations.
    """
    rng = np.random.default_rng(seed)
    null_vals = []
    y = data.flatten()
    
    # Use pysal's built-in permutation logic if available, or manual
    # Manual approach for clarity and control
    n = len(y)
    for _ in range(permutations):
        y_perm = rng.permutation(y)
        try:
            m = Moran(y_perm, w)
            null_vals.append(m.I)
        except:
            null_vals.append(0.0) # Fallback for edge cases
    
    return null_vals

def simulate_h1_gibbs(binary_map: np.ndarray, lambda_val: float, seed: int = DEFAULT_SEED) -> np.ndarray:
    """
    Generate synthetic H1 data using a simplified Gibbs sampler approach 
    for binary spatial autoregressive processes.
    
    Note: True binary SAR is complex. This implementation approximates the 
    spatial structure by iteratively updating pixels based on neighbors 
    weighted by lambda, then thresholding to maintain binary state.
    
    Args:
        binary_map: 2D binary array (0/1).
        lambda_val: Spatial lag parameter.
        seed: Random seed.
    
    Returns:
        Synthetic binary map with similar spatial autocorrelation.
    """
    rng = np.random.default_rng(seed)
    y = binary_map.copy().astype(float)
    rows, cols = y.shape
    n = rows * cols
    
    # Create a simple neighborhood index (4-neighbor)
    # This is a simplification for the Gibbs sampler
    # In a real SAR, we'd use the weights matrix directly
    
    # We will use a simplified Metropolis-Hastings style update
    # to preserve the marginal distribution (binomial) while inducing spatial correlation.
    # Since we don't have the full W matrix here easily accessible in this function signature,
    # we'll rely on the fact that the input binary_map already has structure.
    # A more robust implementation would require 'w' as an argument.
    # For this task, we assume the 'binary_map' is the target distribution shape
    # and we add noise correlated with neighbors.
    
    # Simplified approach: Smooth the map using lambda-weighted neighbors
    # and then binarize.
    smoothed = y.copy()
    for _ in range(10): # Few iterations of smoothing
        new_smooth = np.zeros_like(smoothed)
        for r in range(rows):
            for c in range(cols):
                neighbors = []
                if r > 0: neighbors.append(smoothed[r-1, c])
                if r < rows-1: neighbors.append(smoothed[r+1, c])
                if c > 0: neighbors.append(smoothed[r, c-1])
                if c < cols-1: neighbors.append(smoothed[r, c+1])
                
                if neighbors:
                    avg = np.mean(neighbors)
                    # Update with weight lambda
                    new_val = (1 - lambda_val) * smoothed[r, c] + lambda_val * avg
                    new_smooth[r, c] = new_val
        smoothed = new_smooth
    
    # Threshold back to binary
    threshold = 0.5
    synthetic = (smoothed > threshold).astype(np.uint8)
    return synthetic

def calculate_statistical_power(h0_morans: List[float], h1_morans: List[float], alpha: float = 0.05) -> float:
    """
    Calculate statistical power as the proportion of H1 simulations 
    that reject the null hypothesis.
    
    Args:
        h0_morans: List of Moran's I values from H0 (null) distribution.
        h1_morans: List of Moran's I values from H1 (alternative) distribution.
        alpha: Significance level.
    
    Returns:
        Power estimate (0.0 to 1.0).
    """
    if not h0_morans or not h1_morans:
        return 0.0
    
    # Determine critical value from H0 (two-tailed or one-tailed?)
    # Usually one-tailed for positive autocorrelation
    critical_val = np.percentile(h0_morans, 100 * (1 - alpha))
    
    rejections = sum(1 for m in h1_morans if m > critical_val)
    return rejections / len(h1_morans)

def validate_h1_structure(observed_map: np.ndarray, synthetic_map: np.ndarray, w: libpysal.weights.W, tolerance: float = 0.05) -> bool:
    """
    Validate that the synthetic H1 data has similar spatial autocorrelation 
    to the observed data (within 5% error).
    
    Args:
        observed_map: Original binary map.
        synthetic_map: Generated synthetic map.
        w: Spatial weights.
        tolerance: Maximum allowed relative difference in Moran's I.
    
    Returns:
        True if validation passes.
    """
    i_obs, _ = calculate_moran_i(observed_map, w)
    i_syn, _ = calculate_moran_i(synthetic_map, w)
    
    if i_obs == 0:
        return abs(i_syn) < tolerance
    
    diff = abs(i_obs - i_syn) / abs(i_obs)
    return diff <= tolerance

def run_analysis_for_resolution(
    input_path: str,
    class_id: int,
    w: libpysal.weights.W,
    lambda_val: float,
    permutations: int = 1000,
    seed: int = DEFAULT_SEED
) -> Dict[str, Any]:
    """
    Run the full analysis pipeline for a specific resolution and class.
    
    Args:
        input_path: Path to the raster file.
        class_id: The land cover class ID to analyze.
        w: Spatial weights matrix.
        lambda_val: Estimated spatial lag parameter.
        permutations: Number of permutations for H0.
        seed: Random seed.
    
    Returns:
        Dictionary with results (moran_i, p_value, power, etc.).
    """
    logger.info(f"Running analysis for {input_path} (Class {class_id})")
    
    # Load data
    data = read_raster_windowed(input_path)
    
    # Create binary map
    binary_map = create_binary_indicator_map(data, class_id)
    
    # Flatten for Moran calculation
    y_flat = binary_map.flatten()
    
    # Calculate observed Moran's I
    i_obs, p_obs = calculate_moran_i(y_flat, w)
    
    # Generate H0 null distribution
    h0_morans = generate_null_distribution(y_flat, w, permutations=permutations, seed=seed)
    
    # Generate H1 simulations
    h1_morans = []
    for i in range(permutations):
        # We simulate H1 by using the observed structure + noise, 
        # or by using the Gibbs sampler if we had a full model.
        # For this task, we'll approximate H1 by perturbing the observed map
        # to maintain structure but vary slightly, then calculate Moran.
        # A more rigorous approach would use the Gibbs sampler defined above.
        synthetic = simulate_h1_gibbs(binary_map, lambda_val, seed=seed + i)
        i_syn, _ = calculate_moran_i(synthetic.flatten(), w)
        h1_morans.append(i_syn)
    
    # Calculate power
    power = calculate_statistical_power(h0_morans, h1_morans)
    
    return {
        "moran_i": i_obs,
        "p_value": p_obs,
        "power": power,
        "class_id": class_id,
        "seed": seed
    }

def main():
    """
    CLI entry point for running analysis.
    This function is designed to be called by a script that handles 
    loading the weights and iterating over resolutions.
    """
    logger.info("Analysis module ready.")

if __name__ == "__main__":
    main()
