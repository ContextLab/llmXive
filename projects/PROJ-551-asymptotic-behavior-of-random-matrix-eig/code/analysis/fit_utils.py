"""
Fit utilities for threshold analysis.

This module provides functions to extract fitted parameters from the threshold
identification model and validate the fit quality against strict numerical
tolerance thresholds (1e-10) as required by the project specification.

It implements the statistical inference logic for the critical threshold theta_c
using Logistic Regression, ensuring residuals meet the 1e-10 tolerance.
"""
import json
import logging
import os
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any

import numpy as np
from scipy.optimize import curve_fit
from scipy import stats

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Strict tolerance for numerical validation
STRICT_TOLERANCE = 1e-10

def sigmoid_function(x: np.ndarray, theta_c: float, steepness: float) -> np.ndarray:
    """
    Logistic sigmoid function modeling the probability of outlier emergence.
    
    P(outlier) = 1 / (1 + exp(-steepness * (theta - theta_c)))
    
    Args:
        x: Array of theta values
        theta_c: Critical threshold parameter
        steepness: Steepness of the transition (k)
        
    Returns:
        Probability values for each theta
    """
    return 1.0 / (1.0 + np.exp(-steepness * (x - theta_c)))

def load_mc_results(filepath: str) -> np.ndarray:
    """
    Load Monte Carlo results from CSV file.
    
    Args:
        filepath: Path to mc_results.csv
        
    Returns:
        Array of (theta, outlier_flag) pairs
    """
    data = []
    with open(filepath, 'r') as f:
        lines = f.readlines()
        # Skip header
        for line in lines[1:]:
            parts = line.strip().split(',')
            if len(parts) >= 4:
                try:
                    theta = float(parts[1])
                    outlier = int(parts[3])
                    data.append((theta, outlier))
                except ValueError:
                    continue
    return np.array(data)

def aggregate_by_theta(data: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Aggregate results by theta value.
    
    Args:
        data: Array of (theta, outlier_flag) pairs
        
    Returns:
        Tuple of (unique_thetas, mean_prob, counts)
    """
    thetas = data[:, 0]
    outliers = data[:, 1]
    
    unique_thetas = np.unique(thetas)
    mean_probs = []
    counts = []
    
    for theta in unique_thetas:
        mask = thetas == theta
        prob = np.mean(outliers[mask])
        count = np.sum(mask)
        mean_probs.append(prob)
        counts.append(count)
        
    return unique_thetas, np.array(mean_probs), np.array(counts)

def fit_critical_threshold(
    thetas: np.ndarray, 
    probs: np.ndarray, 
    initial_guess: Optional[Tuple[float, float]] = None
) -> Dict[str, Any]:
    """
    Fit the critical threshold model using curve fitting.
    
    Uses scipy.optimize.curve_fit with strict bounds and tolerance settings.
    
    Args:
        thetas: Array of theta values
        probs: Array of outlier probabilities
        initial_guess: Optional (theta_c, steepness) initial guess
        
    Returns:
        Dictionary containing fitted parameters and fit statistics
    """
    if initial_guess is None:
        # Default guess: theta_c at 0.5 probability, steepness=5
        median_theta = np.median(thetas)
        initial_guess = (median_theta, 5.0)
    
    try:
        popt, pcov = curve_fit(
            sigmoid_function,
            thetas,
            probs,
            p0=initial_guess,
            bounds=([0, 0.1], [10, 100]),  # Reasonable bounds
            maxfev=10000,
            ftol=STRICT_TOLERANCE,
            xtol=STRICT_TOLERANCE,
            gtol=STRICT_TOLERANCE
        )
        
        theta_c, steepness = popt
        perr = np.sqrt(np.diag(pcov))
        
        # Calculate residuals
        predicted_probs = sigmoid_function(thetas, theta_c, steepness)
        residuals = probs - predicted_probs
        max_residual = np.max(np.abs(residuals))
        mean_residual = np.mean(np.abs(residuals))
        
        # Validate fit quality against tolerance
        fit_valid = max_residual < STRICT_TOLERANCE
        
        # Calculate R-squared
        ss_res = np.sum(residuals**2)
        ss_tot = np.sum((probs - np.mean(probs))**2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0
        
        return {
            'theta_c': float(theta_c),
            'steepness': float(steepness),
            'theta_c_std': float(perr[0]),
            'steepness_std': float(perr[1]),
            'max_residual': float(max_residual),
            'mean_residual': float(mean_residual),
            'r_squared': float(r_squared),
            'fit_valid': fit_valid,
            'tolerance': STRICT_TOLERANCE,
            'convergence_message': 'success' if fit_valid else 'warning: residual exceeds tolerance'
        }
        
    except Exception as e:
        logger.error(f"Curve fitting failed: {str(e)}")
        return {
            'theta_c': None,
            'steepness': None,
            'error': str(e),
            'fit_valid': False,
            'tolerance': STRICT_TOLERANCE
        }

def analyze_threshold_identification(
    input_path: str, 
    output_path: str
) -> Dict[str, Any]:
    """
    Main analysis function to extract fitted parameters and validate fit quality.
    
    This function:
    1. Loads validated sweep results
    2. Aggregates by theta
    3. Fits the critical threshold model
    4. Validates residuals against 1e-10 tolerance
    5. Writes results to JSON
    
    Args:
        input_path: Path to validated_sweep_results.csv
        output_path: Path to threshold_fit_params.json
        
    Returns:
        Dictionary containing analysis results
    """
    logger.info(f"Loading data from {input_path}")
    
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    # Load and aggregate data
    data = load_mc_results(input_path)
    thetas, probs, counts = aggregate_by_theta(data)
    
    if len(thetas) < 3:
        raise ValueError("Insufficient data points for fitting (need at least 3 theta values)")
    
    logger.info(f"Fitting threshold model to {len(thetas)} theta values")
    
    # Fit model
    fit_results = fit_critical_threshold(thetas, probs)
    
    # Prepare output
    output_data = {
        'input_file': input_path,
        'data_points': len(thetas),
        'fit_parameters': {
            'theta_c': fit_results.get('theta_c'),
            'steepness': fit_results.get('steepness'),
            'theta_c_std': fit_results.get('theta_c_std'),
            'steepness_std': fit_results.get('steepness_std')
        },
        'fit_quality': {
            'max_residual': fit_results.get('max_residual'),
            'mean_residual': fit_results.get('mean_residual'),
            'r_squared': fit_results.get('r_squared'),
            'tolerance': STRICT_TOLERANCE,
            'fit_valid': fit_results.get('fit_valid'),
            'convergence_message': fit_results.get('convergence_message')
        },
        'aggregated_data': {
            'thetas': thetas.tolist(),
            'probabilities': probs.tolist(),
            'counts': counts.tolist()
        },
        'validation': {
            'residual_threshold_met': fit_results.get('fit_valid', False),
            'max_residual_value': fit_results.get('max_residual', float('inf')),
            'required_tolerance': STRICT_TOLERANCE,
            'status': 'PASS' if fit_results.get('fit_valid', False) else 'FAIL'
        },
        'timestamp': str(np.datetime64('now'))
    }
    
    # Write output
    logger.info(f"Writing results to {output_path}")
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    return output_data

def main():
    """
    Command-line entry point for fit parameter extraction and validation.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Extract and validate fitted threshold parameters')
    parser.add_argument('--input', type=str, default='data/processed/validated_sweep_results.csv',
                      help='Path to validated sweep results CSV')
    parser.add_argument('--output', type=str, default='data/processed/threshold_fit_params.json',
                      help='Path to output JSON file')
    
    args = parser.parse_args()
    
    try:
        results = analyze_threshold_identification(args.input, args.output)
        
        if results['validation']['status'] == 'PASS':
            logger.info(f"✓ Fit validation PASSED: max_residual={results['fit_quality']['max_residual']:.2e} < {STRICT_TOLERANCE:.2e}")
            logger.info(f"  Critical threshold θ_c = {results['fit_parameters']['theta_c']:.6f} ± {results['fit_parameters']['theta_c_std']:.6f}")
        else:
            logger.warning(f"✗ Fit validation FAILED: max_residual={results['fit_quality']['max_residual']:.2e} > {STRICT_TOLERANCE:.2e}")
            logger.warning(f"  {results['fit_quality']['convergence_message']}")
            
    except Exception as e:
        logger.error(f"Analysis failed: {str(e)}")
        raise

if __name__ == '__main__':
    main()