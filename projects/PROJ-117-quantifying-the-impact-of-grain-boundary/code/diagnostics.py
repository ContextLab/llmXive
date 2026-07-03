"""
Diagnostics module for grain boundary data analysis.
Implements T016: Collinearity diagnostics using Mutual Information.
"""
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

import numpy as np
from scipy.stats import entropy

logger = logging.getLogger(__name__)

def compute_mutual_information(x: np.ndarray, y: np.ndarray, n_bins: int = 10) -> float:
    """
    Compute the Mutual Information (MI) between two continuous variables using histogram-based estimation.
    
    Args:
        x: First variable array
        y: Second variable array
        n_bins: Number of bins for histogram discretization
    
    Returns:
        Mutual Information value in bits (or nats depending on log base)
    """
    if len(x) != len(y):
        raise ValueError("Input arrays must have the same length")
    
    if len(x) == 0:
        return 0.0
    
    # Check for constant arrays
    if np.std(x) == 0 or np.std(y) == 0:
        return 0.0
    
    # Discretize the continuous variables
    x_hist, x_edges = np.histogram(x, bins=n_bins)
    y_hist, y_edges = np.histogram(y, bins=n_bins)
    
    # Joint histogram
    joint_hist, _, _ = np.histogram2d(x, y, bins=[x_edges, y_edges])
    
    # Normalize to probabilities
    p_x = x_hist / len(x)
    p_y = y_hist / len(y)
    p_xy = joint_hist / (len(x) * len(y))
    
    # Avoid log(0)
    p_x = p_x[p_x > 0]
    p_y = p_y[p_y > 0]
    p_xy = p_xy[p_xy > 0]
    
    # Calculate MI: I(X;Y) = sum(p(x,y) * log(p(x,y) / (p(x)*p(y))))
    # Using base 2 for bits
    mi = 0.0
    for i in range(len(p_xy)):
        # Find corresponding p_x and p_y for the bin
        # This is a simplified approach; a more robust one would iterate over 2D grid
        pass
    
    # Correct calculation over 2D grid
    mi = 0.0
    for i in range(n_bins):
        for j in range(n_bins):
            if joint_hist[i, j] > 0:
                p_xy_val = joint_hist[i, j] / (len(x) * len(y))
                p_x_val = x_hist[i] / len(x) if x_hist[i] > 0 else 0
                p_y_val = y_hist[j] / len(y) if y_hist[j] > 0 else 0
                
                if p_x_val > 0 and p_y_val > 0:
                    mi += p_xy_val * np.log2(p_xy_val / (p_x_val * p_y_val))
    
    return mi

def calculate_sigma_from_misorientation(misorientation_angle: float) -> int:
    """
    Estimate Sigma value from misorientation angle using CSL approximation.
    This is a simplified lookup/approximation for common angles.
    In a real scenario, this would use a more robust CSL algorithm.
    
    Args:
        misorientation_angle: Angle in degrees
    
    Returns:
        Approximate Sigma value
    """
    # Common CSL angles for cubic systems (approximate)
    # This is a simplified mapping for demonstration
    # Real implementation would use pymatgen or a proper CSL library
    csl_mapping = {
        36.87: 5,
        53.13: 5,
        28.07: 13,
        32.21: 13,
        41.41: 17,
        46.40: 17,
        50.48: 25,
        55.05: 25,
        60.00: 3,
        70.53: 3,
        90.00: 5,
    }
    
    # Find closest match
    best_sigma = 999
    min_diff = float('inf')
    
    for angle, sigma in csl_mapping.items():
        diff = abs(misorientation_angle - angle)
        if diff < min_diff:
            min_diff = diff
            best_sigma = sigma
    
    # If no close match, use a heuristic or return a default
    if min_diff > 5.0:
        # Fallback: rough approximation based on angle
        # Sigma ~ 1 / (1 - cos(theta)) is not accurate but used for fallback
        theta_rad = np.radians(misorientation_angle)
        denom = 1 - np.cos(theta_rad)
        if denom > 0:
            best_sigma = int(round(1.0 / denom))
        else:
            best_sigma = 1
    
    return best_sigma

def run_collinearity_diagnostic(
    misorientation: np.ndarray,
    sigma: np.ndarray,
    output_path: str
) -> Dict[str, Any]:
    """
    Compute Mutual Information between misorientation angle and Sigma value.
    Log warnings and save diagnostic report.
    
    Args:
        misorientation: Array of misorientation angles
        sigma: Array of Sigma values
        output_path: Path to save the JSON report
    
    Returns:
        Dictionary containing the diagnostic results
    """
    logger.info("Running collinearity diagnostic between misorientation and Sigma value.")
    
    # Compute MI
    mi_value = compute_mutual_information(misorientation, sigma, n_bins=20)
    
    result = {
        "mutual_information": float(mi_value),
        "misorientation": {
            "min": float(np.min(misorientation)),
            "max": float(np.max(misorientation)),
            "mean": float(np.mean(misorientation)),
            "count": len(misorientation)
        },
        "sigma": {
            "min": int(np.min(sigma)),
            "max": int(np.max(sigma)),
            "mean": float(np.mean(sigma)),
            "count": len(sigma)
        }
    }
    
    # Check threshold and add warning
    if mi_value > 0.8:
        warning_msg = "MI > 0.8 indicates strong dependency; relationship is descriptive, not causal."
        result["warning"] = warning_msg
        logger.warning(warning_msg)
    else:
        logger.info(f"MI ({mi_value:.4f}) is below threshold (0.8). No strong dependency detected.")
    
    # Ensure output directory exists
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    # Save report
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)
    
    logger.info(f"Diagnostic report saved to {output_path}")
    
    return result

def main():
    """
    Main entry point for running the diagnostic on sample data.
    This function is intended to be called by a script or pipeline.
    """
    # Example usage with dummy data
    # In a real pipeline, data would be loaded from data/processed/
    np.random.seed(42)
    misorientation = np.random.uniform(0, 180, 1000)
    # Create a correlated Sigma for demonstration (some correlation)
    sigma = np.array([calculate_sigma_from_misorientation(m) for m in misorientation])
    
    output_path = "artifacts/reports/collinearity_diagnostic.json"
    
    run_collinearity_diagnostic(misorientation, sigma, output_path)
    
    print(f"Diagnostic complete. Report saved to {output_path}")

if __name__ == "__main__":
    main()