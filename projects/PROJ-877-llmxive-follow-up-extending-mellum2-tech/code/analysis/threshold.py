import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
from scipy import stats
from scipy.optimize import curve_fit
import random
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_correlation_stats() -> Dict[str, Any]:
    """Load correlation statistics from the results file."""
    path = Path("data/results/us1_correlation_stats.json")
    if not path.exists():
        raise FileNotFoundError(f"Correlation stats file not found: {path}")
    with open(path, 'r') as f:
        return json.load(f)

def load_threshold_candidates() -> Optional[Dict[str, Any]]:
    """Load existing threshold candidates if they exist."""
    path = Path("data/results/us2_threshold_candidates.json")
    if not path.exists():
        return None
    with open(path, 'r') as f:
        return json.load(f)

def write_threshold_candidates(data: Dict[str, Any]) -> None:
    """Write threshold candidates to the results file."""
    path = Path("data/results/us2_threshold_candidates.json")
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)

def load_feasibility_report() -> Dict[str, Any]:
    """Load the feasibility report to get perturbation parameters."""
    path = Path("data/results/feasibility_report.json")
    if not path.exists():
        raise FileNotFoundError(f"Feasibility report not found: {path}")
    with open(path, 'r') as f:
        return json.load(f)

def piecewise_linear(x: np.ndarray, x0: float, a1: float, a2: float, b: float) -> np.ndarray:
    """
    Piecewise linear function for threshold detection.
    x0: threshold point
    a1: slope before threshold
    a2: slope after threshold
    b: intercept
    """
    return np.where(x < x0, a1 * x + b, a2 * x + (b + (a1 - a2) * x0))

def detect_change_points(x: np.ndarray, y: np.ndarray) -> Tuple[float, float, float, float]:
    """
    Detect change points in the data using piecewise linear regression.
    Returns (threshold, slope1, slope2, intercept).
    """
    if len(x) < 10:
        raise ValueError("Not enough data points for change point detection")

    # Grid search for initial threshold
    x_sorted = np.sort(x)
    min_x, max_x = x_sorted[10], x_sorted[-10]
    
    best_threshold = None
    best_score = np.inf
    best_params = None

    # Try multiple starting points for threshold
    for threshold in np.linspace(min_x, max_x, 20):
        try:
            # Define the piecewise function with fixed threshold
            def fixed_threshold_func(x, a1, a2, b):
                return np.where(x < threshold, a1 * x + b, a2 * x + (b + (a1 - a2) * threshold))
            
            # Fit the model
            popt, _ = curve_fit(fixed_threshold_func, x, y, p0=[1.0, 0.5, np.mean(y)])
            
            # Calculate residuals
            residuals = y - fixed_threshold_func(x, *popt)
            score = np.sum(residuals**2)
            
            if score < best_score:
                best_score = score
                best_threshold = threshold
                best_params = (threshold, popt[0], popt[1], popt[2])
        except Exception as e:
            logger.warning(f"Failed to fit model with threshold {threshold}: {e}")
            continue

    if best_params is None:
        raise RuntimeError("Could not fit piecewise linear model")

    return best_params

def calculate_threshold_candidates(correlation_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate threshold candidates from correlation data.
    """
    results = []
    
    for lang in ['python', 'java']:
        if lang not in correlation_data:
            continue
        
        data = correlation_data[lang]
        if 'complexity' not in data or 'normalized_loss' not in data:
            continue
        
        x = np.array(data['complexity'])
        y = np.array(data['normalized_loss'])
        
        if len(x) < 10 or np.std(x) < 1e-6 or np.std(y) < 1e-6:
            logger.warning(f"Insufficient variance in {lang} data, skipping threshold detection")
            continue

        try:
            threshold, slope1, slope2, intercept = detect_change_points(x, y)
            results.append({
                'language': lang,
                'threshold': float(threshold),
                'slope_before': float(slope1),
                'slope_after': float(slope2),
                'intercept': float(intercept),
                'r_squared': float(1 - np.var(y - piecewise_linear(x, threshold, slope1, slope2, intercept)) / np.var(y))
            })
        except Exception as e:
            logger.error(f"Failed to detect threshold for {lang}: {e}")
            continue

    return {
        'thresholds': results,
        'status': 'completed' if results else 'failed'
    }

def calculate_aic_bic(y: np.ndarray, y_pred: np.ndarray, n_params: int) -> Tuple[float, float]:
    """
    Calculate AIC and BIC for model comparison.
    """
    n = len(y)
    rss = np.sum((y - y_pred)**2)
    sigma2 = rss / n
    
    aic = n * np.log(sigma2) + 2 * n_params
    bic = n * np.log(sigma2) + np.log(n) * n_params
    
    return float(aic), float(bic)

def fit_linear_model(x: np.ndarray, y: np.ndarray) -> Tuple[float, float, float]:
    """Fit a simple linear model y = ax + b."""
    slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
    return slope, intercept, r_value**2

def fit_piecewise_model(x: np.ndarray, y: np.ndarray, threshold: float) -> Tuple[float, float, float, float]:
    """Fit a piecewise linear model with a fixed threshold."""
    def fixed_threshold_func(x, a1, a2, b):
        return np.where(x < threshold, a1 * x + b, a2 * x + (b + (a1 - a2) * threshold))
    
    popt, _ = curve_fit(fixed_threshold_func, x, y, p0=[1.0, 0.5, np.mean(y)])
    return popt[0], popt[1], popt[2], threshold

def compare_models(x: np.ndarray, y: np.ndarray) -> Dict[str, Any]:
    """Compare linear vs piecewise models using AIC/BIC."""
    # Fit linear model
    slope, intercept, r2_linear = fit_linear_model(x, y)
    y_pred_linear = slope * x + intercept
    aic_linear, bic_linear = calculate_aic_bic(y, y_pred_linear, 2)
    
    # Fit piecewise model
    try:
        threshold, slope1, slope2, intercept_pw = detect_change_points(x, y)
        y_pred_pw = piecewise_linear(x, threshold, slope1, slope2, intercept_pw)
        aic_pw, bic_pw = calculate_aic_bic(y, y_pred_pw, 4)
        
        return {
            'linear': {'aic': aic_linear, 'bic': bic_linear, 'r_squared': r2_linear},
            'piecewise': {
                'aic': aic_pw, 
                'bic': bic_pw,
                'r_squared': 1 - np.var(y - y_pred_pw) / np.var(y),
                'threshold': threshold,
                'slope_before': slope1,
                'slope_after': slope2,
                'intercept': intercept_pw
            },
            'preference': 'piecewise' if aic_pw < aic_linear else 'linear'
        }
    except Exception as e:
        logger.warning(f"Could not fit piecewise model: {e}")
        return {
            'linear': {'aic': aic_linear, 'bic': bic_linear, 'r_squared': r2_linear},
            'piecewise': None,
            'preference': 'linear'
        }

def run_model_comparison(correlation_data: Dict[str, Any]) -> Dict[str, Any]:
    """Run model comparison for all languages."""
    comparisons = {}
    
    for lang in ['python', 'java']:
        if lang not in correlation_data:
            continue
        
        data = correlation_data[lang]
        if 'complexity' not in data or 'normalized_loss' not in data:
            continue
        
        x = np.array(data['complexity'])
        y = np.array(data['normalized_loss'])
        
        if len(x) < 10 or np.std(x) < 1e-6 or np.std(y) < 1e-6:
            continue

        comparisons[lang] = compare_models(x, y)
    
    return comparisons

def run_sensitivity_analysis(
    correlation_data: Dict[str, Any],
    perturbation_magnitude: List[float],
    bootstrap_count: int
) -> Dict[str, Any]:
    """
    Perform sensitivity analysis on threshold detection.
    
    1. Perturbation Sweep: Vary perturbation magnitude and re-run threshold detection.
    2. Bootstrap Perturbation: Resample data and recompute thresholds.
    """
    sensitivity_results = {
        'threshold_shifts_by_magnitude': {},
        'dataset_perturbation_shifts': {}
    }
    
    for lang in ['python', 'java']:
        if lang not in correlation_data:
            continue
        
        data = correlation_data[lang]
        if 'complexity' not in data or 'normalized_loss' not in data:
            continue
        
        x = np.array(data['complexity'])
        y = np.array(data['normalized_loss'])
        
        if len(x) < 10 or np.std(x) < 1e-6 or np.std(y) < 1e-6:
            continue

        # Get baseline threshold
        try:
            baseline_threshold, _, _, _ = detect_change_points(x, y)
        except Exception as e:
            logger.error(f"Could not compute baseline threshold for {lang}: {e}")
            continue

        # Perturbation Sweep
        magnitude_shifts = []
        for mag in perturbation_magnitude:
            # Add noise to data
            x_perturbed = x + np.random.normal(0, mag, size=x.shape)
            y_perturbed = y + np.random.normal(0, mag, size=y.shape)
            
            try:
                new_threshold, _, _, _ = detect_change_points(x_perturbed, y_perturbed)
                delta = abs(new_threshold - baseline_threshold)
                magnitude_shifts.append({
                    'magnitude': mag,
                    'delta': float(delta),
                    'new_threshold': float(new_threshold)
                })
            except Exception as e:
                logger.warning(f"Failed perturbation with magnitude {mag}: {e}")
                magnitude_shifts.append({
                    'magnitude': mag,
                    'delta': None,
                    'new_threshold': None,
                    'error': str(e)
                })
        
        sensitivity_results['threshold_shifts_by_magnitude'][lang] = magnitude_shifts

        # Bootstrap Perturbation
        bootstrap_shifts = []
        for i in range(bootstrap_count):
            # Resample with replacement
            indices = np.random.choice(len(x), size=len(x), replace=True)
            x_boot = x[indices]
            y_boot = y[indices]
            
            try:
                boot_threshold, _, _, _ = detect_change_points(x_boot, y_boot)
                delta = abs(boot_threshold - baseline_threshold)
                bootstrap_shifts.append({
                    'iteration': i,
                    'delta': float(delta),
                    'threshold': float(boot_threshold)
                })
            except Exception as e:
                logger.warning(f"Bootstrap iteration {i} failed: {e}")
                continue

        # Calculate statistics on bootstrap shifts
        if bootstrap_shifts:
          deltas = [b['delta'] for b in bootstrap_shifts if b['delta'] is not None]
          if deltas:
              sensitivity_results['dataset_perturbation_shifts'][lang] = {
                  'mean_delta': float(np.mean(deltas)),
                  'std_delta': float(np.std(deltas)),
                  'min_delta': float(np.min(deltas)),
                  'max_delta': float(np.max(deltas)),
                  'percentile_5': float(np.percentile(deltas, 5)),
                  'percentile_95': float(np.percentile(deltas, 95)),
                  'successful_iterations': len(deltas),
                  'total_iterations': bootstrap_count
              }
          else:
              sensitivity_results['dataset_perturbation_shifts'][lang] = {
                  'error': 'No valid bootstrap samples',
                  'successful_iterations': 0,
                  'total_iterations': bootstrap_count
              }
        else:
            sensitivity_results['dataset_perturbation_shifts'][lang] = {
                'error': 'All bootstrap iterations failed',
                'successful_iterations': 0,
                'total_iterations': bootstrap_count
            }

    return sensitivity_results

def main():
    """Main function to run sensitivity analysis."""
    logger.info("Starting sensitivity analysis for threshold detection")
    
    # Load required data
    try:
        correlation_data = load_correlation_stats()
        feasibility_report = load_feasibility_report()
    except FileNotFoundError as e:
        logger.error(f"Required data file not found: {e}")
        sys.exit(1)
    
    # Get perturbation parameters from feasibility report
    perturbation_magnitude = feasibility_report.get('perturbation_magnitude', [0.1, 0.5, 1.0])
    bootstrap_count = feasibility_report.get('bootstrap_count', 1000)
    
    # Ensure perturbation_magnitude is a list
    if not isinstance(perturbation_magnitude, list):
        perturbation_magnitude = [float(perturbation_magnitude)]
    
    logger.info(f"Perturbation magnitudes: {perturbation_magnitude}")
    logger.info(f"Bootstrap count: {bootstrap_count}")
    
    # Run sensitivity analysis
    try:
        sensitivity_results = run_sensitivity_analysis(
            correlation_data, 
            perturbation_magnitude, 
            bootstrap_count
        )
    except Exception as e:
        logger.error(f"Sensitivity analysis failed: {e}")
        sys.exit(1)
    
    # Load existing threshold candidates or create new
    threshold_candidates = load_threshold_candidates()
    if threshold_candidates is None:
        threshold_candidates = {'thresholds': [], 'status': 'pending'}
    
    # Add sensitivity results
    threshold_candidates['sensitivity_analysis'] = sensitivity_results
    threshold_candidates['status'] = 'completed'
    
    # Write updated results
    write_threshold_candidates(threshold_candidates)
    
    logger.info("Sensitivity analysis completed successfully")
    logger.info(f"Results written to data/results/us2_threshold_candidates.json")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())