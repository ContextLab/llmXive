"""
Task T029a: Compute variation in critical threshold θ_c relative to nominal sparsity level.

This module reads the sensitivity density sweep results, fits a critical threshold
for each sparsity density level, and computes the variation of θ_c relative to the
nominal (reference) sparsity level.

Output:
    data/processed/sensitivity_variation.csv
        Columns: density, theta_c, variation_pct, nominal_theta_c, nominal_density
"""
import csv
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
import numpy as np
from scipy.optimize import curve_fit

# Import project modules
from utils.config import get_project_paths, ensure_directories

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def sigmoid_function(x: np.ndarray, a: float, b: float, c: float) -> np.ndarray:
    """
    Sigmoid function for fitting probability of outlier emergence.
    
    Parameters:
        x: theta values
        a: slope parameter
        b: center (theta_c)
        c: offset
        
    Returns:
        Probability values
    """
    return 1.0 / (1.0 + np.exp(-a * (x - b))) + c

def load_sensitivity_results(csv_path: Path) -> List[Dict[str, Any]]:
    """
    Load the sensitivity density sweep results.
    
    Parameters:
        csv_path: Path to sensitivity_density_sweep.csv
        
    Returns:
        List of result dictionaries
    """
    results = []
    with open(csv_path, 'r', newline='') as f:
        reader = csv.DictReader(f)
        for row in reader:
            results.append({
                'density': float(row['density']),
                'theta': float(row['theta']),
                'outlier_count': int(row['outlier_count']),
                'total_runs': int(row['total_runs']),
                'probability': float(row['probability'])
            })
    return results

def aggregate_by_density(results: List[Dict[str, Any]]) -> Dict[float, Dict[str, np.ndarray]]:
    """
    Aggregate results by density level.
    
    Parameters:
        results: List of result dictionaries
        
    Returns:
        Dictionary mapping density to aggregated data
    """
    aggregated = {}
    for r in results:
        density = r['density']
        if density not in aggregated:
            aggregated[density] = {'theta': [], 'probability': []}
        aggregated[density]['theta'].append(r['theta'])
        aggregated[density]['probability'].append(r['probability'])
    
    # Convert to numpy arrays
    for density in aggregated:
        aggregated[density]['theta'] = np.array(aggregated[density]['theta'])
        aggregated[density]['probability'] = np.array(aggregated[density]['probability'])
    
    return aggregated

def fit_theta_c_for_density(
    theta: np.ndarray,
    probability: np.ndarray,
    density: float
) -> Optional[float]:
    """
    Fit sigmoid function to estimate critical threshold θ_c for a given density.
    
    Parameters:
        theta: Array of theta values
        probability: Array of outlier probabilities
        density: Current density level (for logging)
        
    Returns:
        Estimated θ_c (center parameter b), or None if fit fails
    """
    if len(theta) < 3:
        logger.warning(f"Not enough data points for density={density} to fit sigmoid")
        return None
    
    try:
        # Initial guesses: a=5, b=2.0, c=0.0
        p0 = [5.0, 2.0, 0.0]
        bounds = ([0, 1.0, -0.1], [20, 4.0, 0.1])
        
        popt, _ = curve_fit(
            sigmoid_function,
            theta,
            probability,
            p0=p0,
            bounds=bounds,
            maxfev=5000
        )
        
        theta_c = popt[1]  # Center parameter
        logger.info(f"Fit for density={density}: θ_c = {theta_c:.4f}")
        return theta_c
    except Exception as e:
        logger.error(f"Fit failed for density={density}: {e}")
        return None

def compute_sensitivity_variation(
    results: List[Dict[str, Any]],
    nominal_density: float = 0.2
) -> List[Dict[str, Any]]:
    """
    Compute variation in θ_c relative to nominal density.
    
    Parameters:
        results: Aggregated sensitivity results
        nominal_density: Reference density level (default 0.2)
        
    Returns:
        List of variation records
    """
    aggregated = aggregate_by_density(results)
    
    # Fit θ_c for each density
    theta_c_values = {}
    for density in sorted(aggregated.keys()):
        theta = aggregated[density]['theta']
        prob = aggregated[density]['probability']
        theta_c = fit_theta_c_for_density(theta, prob, density)
        if theta_c is not None:
            theta_c_values[density] = theta_c
    
    if not theta_c_values:
        logger.error("No successful fits for any density level")
        return []
    
    # Determine nominal θ_c
    if nominal_density in theta_c_values:
        nominal_theta_c = theta_c_values[nominal_density]
    else:
        # Use closest density if nominal not available
        closest_density = min(theta_c_values.keys(), key=lambda d: abs(d - nominal_density))
        nominal_theta_c = theta_c_values[closest_density]
        logger.warning(f"Nominal density {nominal_density} not found, using {closest_density} with θ_c={nominal_theta_c:.4f}")
    
    logger.info(f"Nominal θ_c (density={nominal_density}): {nominal_theta_c:.4f}")
    
    # Compute variations
    variations = []
    for density, theta_c in sorted(theta_c_values.items()):
        variation_pct = ((theta_c - nominal_theta_c) / nominal_theta_c) * 100.0
        variations.append({
            'density': density,
            'theta_c': theta_c,
            'variation_pct': variation_pct,
            'nominal_theta_c': nominal_theta_c,
            'nominal_density': nominal_density
        })
    
    return variations

def write_variation_csv(
    variations: List[Dict[str, Any]],
    output_path: Path
) -> None:
    """
    Write variation results to CSV.
    
    Parameters:
        variations: List of variation records
        output_path: Output file path
    """
    fieldnames = ['density', 'theta_c', 'variation_pct', 'nominal_theta_c', 'nominal_density']
    
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for record in variations:
            writer.writerow(record)
    
    logger.info(f"Wrote {len(variations)} variation records to {output_path}")

def main() -> int:
    """
    Main entry point for T029a.
    
    Returns:
        Exit code (0 for success, 1 for failure)
    """
    try:
        # Get project paths
        paths = get_project_paths()
        input_path = paths['data_processed'] / 'sensitivity_density_sweep.csv'
        output_path = paths['data_processed'] / 'sensitivity_variation.csv'
        
        # Ensure output directory exists
        ensure_directories([output_path.parent])
        
        # Validate input
        if not input_path.exists():
            logger.error(f"Input file not found: {input_path}")
            return 1
        
        # Load results
        logger.info(f"Loading sensitivity results from {input_path}")
        results = load_sensitivity_results(input_path)
        logger.info(f"Loaded {len(results)} records")
        
        if not results:
            logger.error("No results found in input file")
            return 1
        
        # Compute variations
        logger.info("Computing sensitivity variation")
        variations = compute_sensitivity_variation(results)
        
        if not variations:
            logger.error("No variations computed (fit failures)")
            return 1
        
        # Write output
        write_variation_csv(variations, output_path)
        
        # Summary
        max_variation = max(abs(v['variation_pct']) for v in variations)
        logger.info(f"Max |variation|: {max_variation:.2f}%")
        
        if max_variation > 5.0:
            logger.warning("Threshold shift exceeds 5% - sensitivity detected")
        else:
            logger.info("Threshold shift within 5% - results are robust")
        
        return 0
        
    except Exception as e:
        logger.exception(f"Error during sensitivity variation computation: {e}")
        return 1

if __name__ == '__main__':
    sys.exit(main())