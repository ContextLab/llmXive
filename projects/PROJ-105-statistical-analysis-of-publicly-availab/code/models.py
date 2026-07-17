import numpy as np
from scipy import stats
from scipy.optimize import minimize
from typing import Dict, Any, Optional, Tuple
import warnings
import json
import logging
from pathlib import Path
import pandas as pd

from config import get_bts_url, RANDOM_SEED
from utils import setup_logging, check_memory_limit
from preprocessing import load_large_csv

# Ensure logging is configured
logger = setup_logging()

class ConvergenceError(Exception):
    """Raised when distribution fitting fails to converge."""
    pass

def fit_distribution(data: np.ndarray, dist_name: str) -> Tuple[Dict[str, Any], bool]:
    """
    Fit a distribution to data using MLE.
    
    Args:
        data: 1D numpy array of data points.
        dist_name: Name of the distribution ('expon', 'gamma', 'lognorm', 'weibull_min', 'pareto').
        
    Returns:
        Tuple of (params_dict, success_bool).
        params_dict contains 'dist', 'frozen', 'params', 'args'.
    """
    if len(data) == 0:
        raise ValueError("Cannot fit distribution to empty data.")
        
    data = data[data > 0] # Ensure positive for most distributions
    if len(data) == 0:
        raise ValueError("No positive data remaining after filtering.")

    try:
        dist = getattr(stats, dist_name)
        # Fit using MLE
        params = dist.fit(data)
        
        # Create frozen distribution
        frozen = dist(*params)
        
        return {
            'dist': dist_name,
            'frozen': frozen,
            'params': params,
            'args': params
        }, True
    except Exception as e:
        logger.warning(f"Failed to fit {dist_name}: {e}")
        return {}, False

def get_fitted_distribution(fitted_dict: Dict[str, Any]) -> Any:
    """Return the frozen distribution object."""
    return fitted_dict.get('frozen')

def fit_all_base_distributions(data: np.ndarray) -> Dict[str, Dict[str, Any]]:
    """Fit all base distributions to the data."""
    distributions = ['expon', 'gamma', 'lognorm', 'weibull_min']
    results = {}
    
    for dist_name in distributions:
        try:
            result, success = fit_distribution(data, dist_name)
            if success:
                results[dist_name] = result
            else:
                logger.warning(f"Skipped {dist_name} due to fit failure.")
        except Exception as e:
            logger.error(f"Error fitting {dist_name}: {e}")
            
    return results

def fit_all_base_distributions_tail(data: np.ndarray, x_min: float) -> Dict[str, Dict[str, Any]]:
    """Fit base distributions to tail data (x >= x_min)."""
    tail_data = data[data >= x_min]
    if len(tail_data) == 0:
        raise ValueError("No data points above x_min for tail fitting.")
    return fit_all_base_distributions(tail_data)

def fit_pareto_tail(data: np.ndarray, x_min: float) -> Dict[str, Any]:
    """Fit Pareto distribution to tail data."""
    tail_data = data[data >= x_min]
    if len(tail_data) == 0:
        raise ValueError("No data points above x_min for Pareto fitting.")
    
    # Fix x_min for Pareto fitting (scipy pareto uses b, scale)
    # We want to fit the tail starting at x_min
    try:
        # Fit Pareto with fixed x_min (scale parameter)
        # scipy.stats.pareto(b, loc, scale)
        # We fix loc=0, scale=x_min, and estimate b
        # Actually, standard approach: fit full pareto to tail_data
        # pareto.fit returns (b, loc, scale)
        # We want to enforce that the distribution starts at x_min
        
        # Method: Fit to tail_data, but ensure loc is near x_min
        # Or simpler: fit to tail_data - x_min + min(tail_data) ? No.
        # Standard: fit pareto to tail_data directly.
        # The resulting scale will be close to min(tail_data) ~ x_min.
        
        params = stats.pareto.fit(tail_data, floc=x_min) # Fix location to x_min
        frozen = stats.pareto(*params)
        
        return {
            'dist': 'pareto',
            'frozen': frozen,
            'params': params,
            'args': params
        }
    except Exception as e:
        logger.error(f"Pareto fit failed: {e}")
        return {}

def estimate_x_min_ks(data: np.ndarray) -> float:
    """
    Estimate x_min via Kolmogorov-Smirnov minimization.
    Searches for the x_min that minimizes the KS distance between the empirical
    tail distribution and the fitted Pareto distribution.
    """
    data = np.sort(data)
    data = data[data > 0]
    
    # Search range: 5th percentile to 95th percentile
    min_val = np.percentile(data, 5)
    max_val = np.percentile(data, 95)
    
    # Grid search
    grid = np.linspace(min_val, max_val, 50)
    best_x_min = min_val
    min_ks = float('inf')
    
    for x_min in grid:
        tail_data = data[data >= x_min]
        if len(tail_data) < 10:
            continue
            
        try:
            # Fit Pareto to tail
            params = stats.pareto.fit(tail_data, floc=x_min)
            cdf_vals = stats.pareto.cdf(tail_data, *params)
            empirical_cdf = np.arange(1, len(tail_data) + 1) / len(tail_data)
            ks_stat = np.max(np.abs(empirical_cdf - cdf_vals))
            
            if ks_stat < min_ks:
                min_ks = ks_stat
                best_x_min = x_min
        except:
            continue
            
    logger.info(f"Estimated x_min via KS minimization: {best_x_min:.2f}")
    return best_x_min

def save_x_min_estimate(x_min: float, output_path: str):
    """Save x_min estimate to JSON."""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump({'x_min': float(x_min)}, f, indent=2)

def calculate_aic(data: np.ndarray, frozen_dist: Any) -> float:
    """Calculate Akaike Information Criterion."""
    k = len(frozen_dist.args)
    n = len(data)
    log_likelihood = np.sum(frozen_dist.logpdf(data))
    return 2 * k - 2 * log_likelihood

def calculate_bic(data: np.ndarray, frozen_dist: Any) -> float:
    """Calculate Bayesian Information Criterion."""
    k = len(frozen_dist.args)
    n = len(data)
    log_likelihood = np.sum(frozen_dist.logpdf(data))
    return k * np.log(n) - 2 * log_likelihood

def calculate_ks_statistic(data: np.ndarray, frozen_dist: Any) -> float:
    """Calculate Kolmogorov-Smirnov statistic."""
    cdf_vals = frozen_dist.cdf(data)
    empirical_cdf = np.arange(1, len(data) + 1) / len(data)
    return np.max(np.abs(empirical_cdf - cdf_vals))

def calculate_ad_statistic(data: np.ndarray, frozen_dist: Any) -> float:
    """Calculate Anderson-Darling statistic."""
    # Anderson-Darling is not directly available for all distributions in scipy
    # Approximation using CDF values
    n = len(data)
    cdf_vals = frozen_dist.cdf(data)
    # Sort data
    sorted_data = np.sort(data)
    sorted_cdf = frozen_dist.cdf(sorted_data)
    
    # AD statistic formula
    # A^2 = -n - (1/n) * sum( (2i-1) * [ln(F(x_i)) + ln(1-F(x_{n-i+1}))] )
    i = np.arange(1, n + 1)
    term1 = np.log(sorted_cdf + 1e-10) # Avoid log(0)
    term2 = np.log(1 - sorted_cdf[::-1] + 1e-10)
    ad_stat = -n - (1/n) * np.sum((2*i - 1) * (term1 + term2))
    return ad_stat

def calculate_tail_metrics(data: np.ndarray, fitted_models: Dict[str, Dict[str, Any]]) -> Dict[str, Dict[str, float]]:
    """Calculate AIC, BIC, KS, AD for all models."""
    metrics = {}
    for name, model_data in fitted_models.items():
        frozen = model_data['frozen']
        metrics[name] = {
            'aic': calculate_aic(data, frozen),
            'bic': calculate_bic(data, frozen),
            'ks': calculate_ks_statistic(data, frozen),
            'ad': calculate_ad_statistic(data, frozen)
        }
    return metrics

def save_model_comparison(metrics: Dict[str, Dict[str, float]], output_path: str):
    """Save model comparison metrics to JSON."""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(metrics, f, indent=2)

def perform_vuong_test(model1_data: Dict[str, Any], model2_data: Dict[str, Any], data: np.ndarray) -> Dict[str, float]:
    """
    Perform Vuong test to compare two non-nested models.
    Returns p-value and test statistic.
    """
    frozen1 = model1_data['frozen']
    frozen2 = model2_data['frozen']
    
    # Log-likelihood ratios
    ll1 = frozen1.logpdf(data)
    ll2 = frozen2.logpdf(data)
    lr = ll1 - ll2
    
    # Vuong statistic
    mean_lr = np.mean(lr)
    std_lr = np.std(lr, ddof=1)
    n = len(data)
    
    if std_lr == 0:
        return {'statistic': 0.0, 'p_value': 1.0}
        
    vuong_stat = mean_lr * np.sqrt(n) / std_lr
    p_value = 2 * (1 - stats.norm.cdf(abs(vuong_stat)))
    
    return {
        'statistic': float(vuong_stat),
        'p_value': float(p_value)
    }

def save_vuong_test_results(results: Dict[str, float], output_path: str):
    """Save Vuong test results to JSON."""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)

def compare_component_distributions(data_path: str, output_path: str):
    """
    Compare sum distribution (total_delay) vs components (ArrDelay, DepDelay).
    Performs KS test and generates histograms.
    Saves results to JSON.
    
    Args:
        data_path: Path to the cleaned CSV file containing delay data.
        output_path: Path to save the component_comparison.json file.
    """
    logger.info(f"Loading data from {data_path} for component comparison")
    
    # Load data
    df = load_large_csv(data_path)
    
    # Ensure required columns exist
    required_cols = ['total_delay', 'ArrDelay', 'DepDelay']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in data: {missing}")
    
    # Filter out NaN and negative values for valid comparison
    # Use only rows where all three are valid and positive (or zero for total)
    mask = df['total_delay'].notna() & df['ArrDelay'].notna() & df['DepDelay'].notna()
    valid_df = df[mask]
    
    total_delays = valid_df['total_delay'].values
    arr_delays = valid_df['ArrDelay'].values
    dep_delays = valid_df['DepDelay'].values
    
    # Filter positive values for distribution fitting (delays are typically >= 0)
    # But for KS test, we can include zeros if they exist
    # Remove extreme outliers (> 1440 min) if not already done
    total_delays = total_delays[total_delays <= 1440]
    arr_delays = arr_delays[arr_delays <= 1440]
    dep_delays = dep_delays[dep_delays <= 1440]
    
    logger.info(f"Comparing distributions: Total={len(total_delays)}, Arr={len(arr_delays)}, Dep={len(dep_delays)}")
    
    # Perform KS tests
    # Total vs Arr
    ks_total_arr, p_total_arr = stats.ks_2samp(total_delays, arr_delays)
    # Total vs Dep
    ks_total_dep, p_total_dep = stats.ks_2samp(total_delays, dep_delays)
    # Arr vs Dep
    ks_arr_dep, p_arr_dep = stats.ks_2samp(arr_delays, dep_delays)
    
    # Generate histogram data
    # Use same bins for fair comparison
    all_data = np.concatenate([total_delays, arr_delays, dep_delays])
    bins = np.histogram_bin_edges(all_data, bins=50, range=(0, 600)) # Focus on first 10 hours
    
    hist_total, _ = np.histogram(total_delays, bins=bins)
    hist_arr, _ = np.histogram(arr_delays, bins=bins)
    hist_dep, _ = np.histogram(dep_delays, bins=bins)
    
    # Normalize for comparison
    hist_total_norm = hist_total / len(total_delays)
    hist_arr_norm = hist_arr / len(arr_delays)
    hist_dep_norm = hist_dep / len(dep_delays)
    
    # Prepare results
    results = {
        'ks_tests': {
            'total_vs_arr': {
                'statistic': float(ks_total_arr),
                'p_value': float(p_total_arr),
                'interpretation': 'different' if p_total_arr < 0.05 else 'similar'
            },
            'total_vs_dep': {
                'statistic': float(ks_total_dep),
                'p_value': float(p_total_dep),
                'interpretation': 'different' if p_total_dep < 0.05 else 'similar'
            },
            'arr_vs_dep': {
                'statistic': float(ks_arr_dep),
                'p_value': float(p_arr_dep),
                'interpretation': 'different' if p_arr_dep < 0.05 else 'similar'
            }
        },
        'histograms': {
            'bins': bins.tolist(),
            'total_delay': hist_total_norm.tolist(),
            'arrival_delay': hist_arr_norm.tolist(),
            'departure_delay': hist_dep_norm.tolist()
        },
        'sample_sizes': {
            'total': int(len(total_delays)),
            'arrival': int(len(arr_delays)),
            'departure': int(len(dep_delays))
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
    # Default paths
    data_path = 'data/processed/cleaned_delays.csv'
    output_path = 'data/results/component_comparison.json'
    
    # Check if data exists
    if not Path(data_path).exists():
        logger.error(f"Data file not found: {data_path}")
        logger.error("Please run Stage 1 (data preprocessing) first.")
        return
        
    try:
        compare_component_distributions(data_path, output_path)
        logger.info("Component comparison completed successfully.")
    except Exception as e:
        logger.error(f"Component comparison failed: {e}")
        raise

if __name__ == '__main__':
    main()
