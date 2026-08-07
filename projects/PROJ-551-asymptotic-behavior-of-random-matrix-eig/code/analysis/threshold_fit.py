"""
Curve fitting module to estimate critical theta_c from binary outlier probability data.

Implements logistic regression-like fitting to determine the phase transition threshold
where outlier eigenvalues emerge with probability > 0.5.
"""
import os
import json
import logging
import numpy as np
from scipy.optimize import curve_fit
from pathlib import Path
from typing import Tuple, Optional, Dict, Any

from utils.config import get_project_paths, ensure_directories

logger = logging.getLogger(__name__)

def sigmoid_function(theta: np.ndarray, theta_c: float, slope: float) -> np.ndarray:
    """
    Sigmoid function modeling the probability of outlier emergence.
    
    P(outlier) = 1 / (1 + exp(-slope * (theta - theta_c)))
    
    Args:
        theta: Array of perturbation norm values
        theta_c: Critical threshold parameter (where probability = 0.5)
        slope: Steepness of the transition
        
    Returns:
        Predicted probabilities for each theta value
    """
    return 1.0 / (1.0 + np.exp(-slope * (theta - theta_c)))

def load_sweep_results(input_path: str) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Load aggregated sweep results from CSV.
    
    Args:
        input_path: Path to the threshold_sweep_results.csv file
        
    Returns:
        Tuple of (theta_values, N_values, outlier_probabilities)
        
    Raises:
        FileNotFoundError: If the input file does not exist
        ValueError: If the file format is invalid or missing required columns
    """
    import csv
    
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Sweep results file not found: {input_path}")
    
    theta_list = []
    prob_list = []
    n_list = []
    
    with open(input_path, 'r', newline='') as f:
        reader = csv.DictReader(f)
        required_cols = {'theta', 'N', 'outlier_probability'}
        if not required_cols.issubset(set(reader.fieldnames or [])):
            raise ValueError(f"Missing required columns. Found: {reader.fieldnames}, Required: {required_cols}")
        
        for row in reader:
            try:
                theta = float(row['theta'])
                N = int(row['N'])
                prob = float(row['outlier_probability'])
                
                theta_list.append(theta)
                n_list.append(N)
                prob_list.append(prob)
            except (ValueError, KeyError) as e:
                logger.warning(f"Skipping invalid row: {row}, error: {e}")
                continue
    
    if not theta_list:
        raise ValueError("No valid data rows found in sweep results")
        
    return np.array(theta_list), np.array(n_list), np.array(prob_list)

def fit_critical_threshold(
    theta: np.ndarray, 
    probabilities: np.ndarray,
    initial_guess: Optional[Tuple[float, float]] = None
) -> Tuple[float, float, Dict[str, Any]]:
    """
    Fit the sigmoid model to empirical outlier probability data to estimate theta_c.
    
    Args:
        theta: Array of perturbation norm values
        probabilities: Array of observed outlier probabilities (0.0 to 1.0)
        initial_guess: Optional tuple (theta_c_init, slope_init) for curve_fit
        
    Returns:
        Tuple of (theta_c, slope, fit_info_dict)
        
    Raises:
        RuntimeError: If curve fitting fails to converge
    """
    if len(theta) < 2:
        raise ValueError("Need at least 2 data points for curve fitting")
    
    if initial_guess is None:
        # Heuristic initial guess: theta_c near where prob ~ 0.5
        mid_idx = np.argmin(np.abs(probabilities - 0.5))
        theta_c_init = float(theta[mid_idx])
        # Estimate slope from the steepest part of the curve
        if len(theta) > 2:
            sorted_idx = np.argsort(theta)
            sorted_theta = theta[sorted_idx]
            sorted_prob = probabilities[sorted_idx]
            # Approximate derivative
            deltas = np.diff(sorted_prob) / np.diff(sorted_theta)
            max_slope_idx = np.argmax(np.abs(deltas))
            slope_init = float(deltas[max_slope_idx])
            if abs(slope_init) < 1e-6:
                slope_init = 1.0
        else:
            slope_init = 1.0
        initial_guess = (theta_c_init, slope_init)
    
    logger.info(f"Initial guess for fitting: theta_c={initial_guess[0]:.4f}, slope={initial_guess[1]:.4f}")
    
    try:
        popt, pcov = curve_fit(
            sigmoid_function,
            theta,
            probabilities,
            p0=initial_guess,
            bounds=([0.0, -np.inf], [np.inf, np.inf]),
            maxfev=5000
        )
        
        theta_c, slope = popt
        
        # Calculate standard errors if covariance is available
        if pcov is not None:
            perr = np.sqrt(np.diag(pcov))
            theta_c_err = float(perr[0])
            slope_err = float(perr[1])
        else:
            theta_c_err = None
            slope_err = None
        
        # Calculate R-squared
        y_pred = sigmoid_function(theta, theta_c, slope)
        ss_res = np.sum((probabilities - y_pred) ** 2)
        ss_tot = np.sum((probabilities - np.mean(probabilities)) ** 2)
        r_squared = 1.0 - (ss_res / ss_tot) if ss_tot > 0 else 0.0
        
        fit_info = {
            'theta_c': float(theta_c),
            'slope': float(slope),
            'theta_c_std_error': float(theta_c_err) if theta_c_err is not None else None,
            'slope_std_error': float(slope_err) if slope_err is not None else None,
            'r_squared': float(r_squared),
            'converged': True,
            'n_data_points': len(theta),
            'initial_guess': list(initial_guess)
        }
        
        logger.info(f"Fitting converged: theta_c={theta_c:.6f}, slope={slope:.6f}, R²={r_squared:.4f}")
        return theta_c, slope, fit_info
        
    except Exception as e:
        logger.error(f"Curve fitting failed: {e}")
        raise RuntimeError(f"Failed to fit critical threshold: {e}")

def run_curve_fitting(
    input_csv_path: str,
    output_json_path: str,
    matrix_size: Optional[int] = None
) -> Dict[str, Any]:
    """
    Main entry point to run curve fitting on sweep results.
    
    Args:
        input_csv_path: Path to threshold_sweep_results.csv
        output_json_path: Path to write threshold_fit_params.json
        matrix_size: Optional filter to fit only data for a specific N
        
    Returns:
        Dictionary containing fitting results and metadata
    """
    logger.info(f"Loading sweep results from: {input_csv_path}")
    theta_all, n_all, prob_all = load_sweep_results(input_csv_path)
    
    if matrix_size is not None:
        mask = (n_all == matrix_size)
        if not np.any(mask):
            raise ValueError(f"No data found for matrix size N={matrix_size}")
        theta = theta_all[mask]
        probabilities = prob_all[mask]
        logger.info(f"Filtered to N={matrix_size}: {len(theta)} data points")
    else:
        # Aggregate by theta across all N (simple mean)
        unique_thetas = np.unique(theta_all)
        theta = unique_thetas
        probabilities = np.array([np.mean(prob_all[theta_all == t]) for t in unique_thetas])
        logger.info(f"Aggregated across all N: {len(theta)} unique theta values")
    
    logger.info(f"Fitting sigmoid model to {len(theta)} data points")
    theta_c, slope, fit_info = fit_critical_threshold(theta, probabilities)
    
    # Prepare output
    result = {
        'fit_parameters': fit_info,
        'data_summary': {
            'input_file': input_csv_path,
            'matrix_size_filter': matrix_size,
            'unique_thetas': [float(t) for t in theta],
            'probabilities': [float(p) for p in probabilities]
        },
        'metadata': {
            'model': 'sigmoid',
            'formula': 'P(outlier) = 1 / (1 + exp(-slope * (theta - theta_c)))',
            'theoretical_bbp_threshold': 1.0,
            'timestamp': datetime.now().isoformat()
        }
    }
    
    # Ensure output directory exists
    output_dir = os.path.dirname(output_json_path)
    if output_dir:
        ensure_directories([output_dir])
    
    # Write results
    with open(output_json_path, 'w') as f:
        json.dump(result, f, indent=2)
    
    logger.info(f"Wrote fitting results to: {output_json_path}")
    return result

def main():
    """Command-line entry point for threshold curve fitting."""
    import argparse
    from datetime import datetime
    
    parser = argparse.ArgumentParser(
        description='Estimate critical theta_c from outlier probability data'
    )
    parser.add_argument(
        '--input', '-i',
        type=str,
        default='data/processed/threshold_sweep_results.csv',
        help='Path to threshold_sweep_results.csv'
    )
    parser.add_argument(
        '--output', '-o',
        type=str,
        default='data/processed/threshold_fit_params.json',
        help='Path to write threshold_fit_params.json'
    )
    parser.add_argument(
        '--matrix-size', '-n',
        type=int,
        default=None,
        help='Filter to specific matrix size N (optional)'
    )
    parser.add_argument(
        '--log-level',
        type=str,
        default='INFO',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        help='Logging level'
    )
    
    args = parser.parse_args()
    
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    try:
        result = run_curve_fitting(args.input, args.output, args.matrix_size)
        print(f"Successfully fitted critical threshold: theta_c = {result['fit_parameters']['theta_c']:.6f}")
        return 0
    except Exception as e:
        logging.error(f"Failed to run curve fitting: {e}")
        return 1

if __name__ == '__main__':
    exit(main())
