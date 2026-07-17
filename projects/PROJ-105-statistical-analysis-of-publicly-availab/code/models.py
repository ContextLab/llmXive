import numpy as np
from scipy import stats
from scipy.optimize import minimize
from typing import Dict, Any, Optional, Tuple
import warnings
import json
import logging
from pathlib import Path

# Ensure logging is configured if not already
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ConvergenceError(Exception):
    """Raised when a distribution fit fails to converge."""
    pass

def fit_distribution(data: np.ndarray, dist_name: str, method: str = 'MLE') -> Tuple[Any, Dict[str, float]]:
    """
    Fit a distribution to data using MLE.
    
    Args:
        data: 1D numpy array of data
        dist_name: Name of the distribution ('expon', 'gamma', 'lognorm', 'weibull_min', 'pareto')
        method: Fitting method (currently only 'MLE' supported)
    
    Returns:
        Tuple of (scipy.stats distribution object, params dict)
    
    Raises:
        ConvergenceError: If fitting fails or produces invalid parameters
    """
    if len(data) == 0:
        raise ConvergenceError("Cannot fit distribution to empty data")
    
    if method != 'MLE':
        raise ValueError(f"Method {method} not supported. Use 'MLE'.")
    
    try:
        if dist_name == 'expon':
            # Exponential: scale parameter
            params = stats.expon.fit(data)
            dist_obj = stats.expon(*params)
        elif dist_name == 'gamma':
            # Gamma: shape, loc, scale
            params = stats.gamma.fit(data)
            dist_obj = stats.gamma(*params)
        elif dist_name == 'lognorm':
            # Log-normal: shape (s), loc, scale
            params = stats.lognorm.fit(data)
            dist_obj = stats.lognorm(*params)
        elif dist_name == 'weibull_min':
            # Weibull: shape (c), loc, scale
            params = stats.weibull_min.fit(data)
            dist_obj = stats.weibull_min(*params)
        elif dist_name == 'pareto':
            # Pareto: shape (b), loc, scale
            params = stats.pareto.fit(data)
            dist_obj = stats.pareto(*params)
        else:
            raise ValueError(f"Unknown distribution: {dist_name}")
        
        # Validate parameters
        if any(np.isnan(p) for p in params):
            raise ConvergenceError(f"NaN parameters detected for {dist_name}")
        if any(np.isinf(p) for p in params):
            raise ConvergenceError(f"Infinite parameters detected for {dist_name}")
        
        return dist_obj, {'name': dist_name, 'params': params}
    
    except Exception as e:
        raise ConvergenceError(f"Failed to fit {dist_name}: {str(e)}")

def get_fitted_distribution(dist_obj: Any, data: np.ndarray) -> Dict[str, Any]:
    """
    Calculate metrics for a fitted distribution against data.
    
    Args:
        dist_obj: Fitted scipy.stats distribution object
        data: Original data array
    
    Returns:
        Dict with AIC, BIC, KS statistic, KS p-value, AD statistic
    """
    n = len(data)
    if n == 0:
        return {}
    
    # AIC and BIC
    log_likelihood = np.sum(dist_obj.logpdf(data))
    k = len(dist_obj.args)  # Number of parameters
    aic = 2 * k - 2 * log_likelihood
    bic = k * np.log(n) - 2 * log_likelihood
    
    # Kolmogorov-Smirnov test
    ks_stat, ks_p = stats.kstest(data, dist_obj.cdf)
    
    # Anderson-Darling test (approximate for general distributions)
    # Note: scipy.stats.anderson is for specific distributions, using custom calculation
    sorted_data = np.sort(data)
    n = len(sorted_data)
    i = np.arange(1, n + 1)
    cdf_vals = dist_obj.cdf(sorted_data)
    ad_stat = -n - np.sum((2 * i - 1) / n * (np.log(cdf_vals) + np.log(1 - cdf_vals[::-1])))
    
    return {
        'aic': aic,
        'bic': bic,
        'ks_statistic': ks_stat,
        'ks_p_value': ks_p,
        'ad_statistic': ad_stat
    }

def fit_all_base_distributions(data: np.ndarray) -> Dict[str, Dict[str, Any]]:
    """
    Fit all base distributions to the full cleaned data.
    
    Args:
        data: 1D numpy array of delay data
    
    Returns:
        Dict mapping distribution names to fit results
    """
    distributions = ['expon', 'gamma', 'lognorm', 'weibull_min']
    results = {}
    
    for dist_name in distributions:
        try:
            dist_obj, params = fit_distribution(data, dist_name)
            metrics = get_fitted_distribution(dist_obj, data)
            results[dist_name] = {
                'params': params['params'],
                'metrics': metrics,
                'converged': True
            }
            logger.info(f"Fitted {dist_name}: params={params['params']}")
        except ConvergenceError as e:
            logger.warning(f"Failed to fit {dist_name}: {e}")
            results[dist_name] = {
                'params': None,
                'metrics': None,
                'converged': False,
                'error': str(e)
            }
    
    return results

def fit_all_base_distributions_tail(data: np.ndarray, x_min: float) -> Dict[str, Dict[str, Any]]:
    """
    Fit all base distributions to the tail subset (data >= x_min).
    
    Args:
        data: 1D numpy array of delay data
        x_min: Threshold for tail subset
    
    Returns:
        Dict mapping distribution names to fit results
    """
    tail_data = data[data >= x_min]
    if len(tail_data) == 0:
        logger.warning("No data points >= x_min. Cannot fit tail distributions.")
        return {}
    
    return fit_all_base_distributions(tail_data)

def fit_pareto_tail(data: np.ndarray, x_min: float) -> Optional[Dict[str, Any]]:
    """
    Fit Pareto distribution to the tail subset (data >= x_min).
    
    Args:
        data: 1D numpy array of delay data
        x_min: Threshold for tail subset
    
    Returns:
        Dict with fit results or None if failed
    """
    tail_data = data[data >= x_min]
    if len(tail_data) == 0:
        logger.warning("No data points >= x_min. Cannot fit Pareto.")
        return None
    
    try:
        dist_obj, params = fit_distribution(tail_data, 'pareto')
        metrics = get_fitted_distribution(dist_obj, tail_data)
        return {
            'params': params['params'],
            'metrics': metrics,
            'converged': True
        }
    except ConvergenceError as e:
        logger.warning(f"Failed to fit Pareto: {e}")
        return {
            'params': None,
            'metrics': None,
            'converged': False,
            'error': str(e)
        }

def calculate_aic(log_likelihood: float, n_params: int) -> float:
    """Calculate AIC from log-likelihood and number of parameters."""
    return 2 * n_params - 2 * log_likelihood

def calculate_bic(log_likelihood: float, n_params: int, n_samples: int) -> float:
    """Calculate BIC from log-likelihood, number of parameters, and sample size."""
    return n_params * np.log(n_samples) - 2 * log_likelihood

def calculate_ks_statistic(data: np.ndarray, cdf_func) -> Tuple[float, float]:
    """
    Calculate Kolmogorov-Smirnov statistic.
    
    Args:
        data: 1D numpy array
        cdf_func: Function that computes CDF values
    
    Returns:
        Tuple of (KS statistic, p-value)
    """
    return stats.kstest(data, cdf_func)

def calculate_ad_statistic(data: np.ndarray, cdf_func) -> float:
    """
    Calculate Anderson-Darling statistic.
    
    Args:
        data: 1D numpy array
        cdf_func: Function that computes CDF values
    
    Returns:
        AD statistic
    """
    sorted_data = np.sort(data)
    n = len(sorted_data)
    i = np.arange(1, n + 1)
    cdf_vals = cdf_func(sorted_data)
    # Avoid log(0)
    cdf_vals = np.clip(cdf_vals, 1e-10, 1 - 1e-10)
    ad_stat = -n - np.sum((2 * i - 1) / n * (np.log(cdf_vals) + np.log(1 - cdf_vals[::-1])))
    return ad_stat

def calculate_tail_metrics(data: np.ndarray, x_min: float, dist_results: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """
    Calculate metrics for distributions on the tail subset.
    
    Args:
        data: Full data array
        x_min: Threshold
        dist_results: Results from fit_all_base_distributions_tail
    
    Returns:
        Same dict with metrics calculated
    """
    return dist_results

def save_model_comparison(results: Dict[str, Dict[str, Any]], output_path: str):
    """Save model comparison results to JSON."""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Model comparison saved to {output_path}")

def perform_vuong_test(data: np.ndarray, dist1: Any, dist2: Any) -> Dict[str, float]:
    """
    Perform Vuong test to compare two non-nested distributions.
    
    Args:
        data: 1D numpy array
        dist1, dist2: Fitted scipy.stats distribution objects
    
    Returns:
        Dict with vuong_z, vuong_p, and conclusion
    """
    # Calculate log-likelihood ratio for each point
    ll1 = dist1.logpdf(data)
    ll2 = dist2.logpdf(data)
    lr = ll1 - ll2
    
    # Vuong statistic
    mean_lr = np.mean(lr)
    std_lr = np.std(lr, ddof=1)
    n = len(data)
    
    if std_lr == 0:
        vuong_z = np.inf if mean_lr > 0 else -np.inf
    else:
        vuong_z = mean_lr * np.sqrt(n) / std_lr
    
    # Two-tailed p-value
    vuong_p = 2 * (1 - stats.norm.cdf(abs(vuong_z)))
    
    # Interpretation
    if abs(vuong_z) < 1.96:
        conclusion = "Inconclusive (no significant difference)"
    elif vuong_z > 1.96:
        conclusion = "Distribution 1 is significantly better"
    else:
        conclusion = "Distribution 2 is significantly better"
    
    return {
        'vuong_z': float(vuong_z),
        'vuong_p': float(vuong_p),
        'conclusion': conclusion
    }

def save_vuong_test_results(results: Dict[str, float], output_path: str):
    """Save Vuong test results to JSON."""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Vuong test results saved to {output_path}")

def compare_component_distributions(total_delay: np.ndarray, arr_delay: np.ndarray, dep_delay: np.ndarray, output_path: str) -> Dict[str, Any]:
    """
    Compare sum distribution (total_delay) vs components (ArrDelay, DepDelay) via KS test and histograms.
    
    Args:
        total_delay: Array of total delays (ArrDelay + DepDelay)
        arr_delay: Array of arrival delays
        dep_delay: Array of departure delays
        output_path: Path to save results JSON
    
    Returns:
        Dict with comparison results
    """
    results = {
        'ks_tests': {},
        'summary_statistics': {}
    }
    
    # Filter out non-positive values for distribution fitting (if needed)
    valid_mask = (total_delay > 0) & (arr_delay >= 0) & (dep_delay >= 0)
    total_valid = total_delay[valid_mask]
    arr_valid = arr_delay[valid_mask]
    dep_valid = dep_delay[valid_mask]
    
    logger.info(f"Total records: {len(total_delay)}, Valid for comparison: {len(total_valid)}")
    
    if len(total_valid) == 0:
        logger.error("No valid data points for component comparison.")
        results['error'] = "No valid data points"
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
        return results
    
    # KS test: Total vs Arrival
    try:
        ks_total_arr, p_total_arr = stats.kstest(total_valid, arr_valid)
        results['ks_tests']['total_vs_arrival'] = {
            'ks_statistic': float(ks_total_arr),
            'p_value': float(p_total_arr),
            'interpretation': "Significant difference" if p_total_arr < 0.05 else "No significant difference"
        }
    except Exception as e:
        logger.warning(f"KS test total vs arrival failed: {e}")
        results['ks_tests']['total_vs_arrival'] = {'error': str(e)}
    
    # KS test: Total vs Departure
    try:
        ks_total_dep, p_total_dep = stats.kstest(total_valid, dep_valid)
        results['ks_tests']['total_vs_departure'] = {
            'ks_statistic': float(ks_total_dep),
            'p_value': float(p_total_dep),
            'interpretation': "Significant difference" if p_total_dep < 0.05 else "No significant difference"
        }
    except Exception as e:
        logger.warning(f"KS test total vs departure failed: {e}")
        results['ks_tests']['total_vs_departure'] = {'error': str(e)}
    
    # KS test: Arrival vs Departure
    try:
        ks_arr_dep, p_arr_dep = stats.kstest(arr_valid, dep_valid)
        results['ks_tests']['arrival_vs_departure'] = {
            'ks_statistic': float(ks_arr_dep),
            'p_value': float(p_arr_dep),
            'interpretation': "Significant difference" if p_arr_dep < 0.05 else "No significant difference"
        }
    except Exception as e:
        logger.warning(f"KS test arrival vs departure failed: {e}")
        results['ks_tests']['arrival_vs_departure'] = {'error': str(e)}
    
    # Summary statistics
    results['summary_statistics'] = {
        'total_delay': {
            'mean': float(np.mean(total_valid)),
            'median': float(np.median(total_valid)),
            'std': float(np.std(total_valid)),
            'min': float(np.min(total_valid)),
            'max': float(np.max(total_valid)),
            'count': int(len(total_valid))
        },
        'arrival_delay': {
            'mean': float(np.mean(arr_valid)),
            'median': float(np.median(arr_valid)),
            'std': float(np.std(arr_valid)),
            'min': float(np.min(arr_valid)),
            'max': float(np.max(arr_valid)),
            'count': int(len(arr_valid))
        },
        'departure_delay': {
            'mean': float(np.mean(dep_valid)),
            'median': float(np.median(dep_valid)),
            'std': float(np.std(dep_valid)),
            'min': float(np.min(dep_valid)),
            'max': float(np.max(dep_valid)),
            'count': int(len(dep_valid))
        }
    }
    
    # Save results
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Component comparison results saved to {output_path}")
    return results

def main():
    """Main entry point for component comparison."""
    import argparse
    parser = argparse.ArgumentParser(description='Compare component distributions')
    parser.add_argument('--input', type=str, required=True, help='Path to cleaned delays CSV')
    parser.add_argument('--output', type=str, required=True, help='Path to output JSON')
    args = parser.parse_args()
    
    # Load data
    import pandas as pd
    df = pd.read_csv(args.input)
    
    # Ensure columns exist
    required_cols = ['total_delay', 'ArrDelay', 'DepDelay']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
    
    total_delay = df['total_delay'].values
    arr_delay = df['ArrDelay'].values
    dep_delay = df['DepDelay'].values
    
    # Run comparison
    compare_component_distributions(total_delay, arr_delay, dep_delay, args.output)
    
    logger.info("Component comparison completed.")

if __name__ == '__main__':
    main()
