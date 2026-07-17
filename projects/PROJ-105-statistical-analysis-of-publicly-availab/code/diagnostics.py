import numpy as np
from scipy import stats
from scipy.optimize import minimize_scalar
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import warnings

logger = logging.getLogger(__name__)

def hill_estimator(data: np.ndarray, k: int) -> float:
    """
    Compute the Hill estimator for the tail index (xi) given the top k order statistics.
    
    Parameters
    ----------
    data : np.ndarray
        Sorted array of positive values (descending order expected for top k).
    k : int
        Number of top order statistics to use.
        
    Returns
    -------
    float
        Estimated tail index xi.
    """
    if k <= 0 or k >= len(data):
        raise ValueError("k must be in range (0, len(data))")
    
    # Sort descending to get largest values first
    sorted_data = np.sort(data)[::-1]
    top_k = sorted_data[:k]
    
    # Hill estimator: average of log ratios
    # xi_hat = (1/k) * sum_{i=1}^k log(X_{n-i+1} / X_{n-k})
    threshold = top_k[-1]
    if threshold <= 0:
        raise ValueError("Threshold value must be positive for Hill estimator")
        
    log_ratios = np.log(top_k / threshold)
    return np.mean(log_ratios)

def compute_hill_statistics(data: np.ndarray, max_k_ratio: float = 0.1) -> Dict[str, Any]:
    """
    Compute Hill estimator statistics over a range of k values.
    
    Parameters
    ----------
    data : np.ndarray
        Array of delay values.
    max_k_ratio : float
        Maximum ratio of k/n to consider (default 0.1).
        
    Returns
    -------
    dict
        Dictionary containing k_values, hill_estimates, and variance estimates.
    """
    n = len(data)
    max_k = int(n * max_k_ratio)
    k_values = np.arange(10, max_k, 5)  # Start from 10 to avoid instability
    
    hill_estimates = []
    variances = []
    
    for k in k_values:
        try:
            xi = hill_estimator(data, k)
            hill_estimates.append(xi)
            # Approximate variance of Hill estimator
            variances.append(xi**2 / k)
        except ValueError as e:
            logger.warning(f"Skipping k={k}: {e}")
            hill_estimates.append(np.nan)
            variances.append(np.nan)
    
    return {
        'k_values': k_values.tolist(),
        'hill_estimates': hill_estimates,
        'variances': variances,
        'n': n,
        'max_k': max_k
    }

def validate_stability_window(
    hill_stats: Dict[str, Any], 
    window_size: int = 10, 
    threshold: float = 0.05
) -> Tuple[bool, int, float]:
    """
    Validate the stability window for the Hill estimator.
    
    Parameters
    ----------
    hill_stats : dict
        Statistics from compute_hill_statistics.
    window_size : int
        Size of the sliding window for variance check.
    threshold : float
        Variance threshold for stability.
        
    Returns
    -------
    tuple
        (is_stable, optimal_k, min_variance)
    """
    k_values = np.array(hill_stats['k_values'])
    estimates = np.array(hill_stats['hill_estimates'])
    variances = np.array(hill_stats['variances'])
    
    if len(estimates) < window_size:
        return False, -1, np.inf
        
    # Sliding window variance check
    stable_indices = []
    for i in range(len(estimates) - window_size + 1):
        window_estimates = estimates[i:i+window_size]
        window_variance = np.var(window_estimates)
        if window_variance < threshold:
            stable_indices.append(k_values[i])
    
    if not stable_indices:
        return False, -1, np.inf
        
    # Find k with minimum variance in stable region
    min_var_idx = np.argmin(variances)
    optimal_k = k_values[min_var_idx]
    min_variance = variances[min_var_idx]
    
    return True, optimal_k, min_variance

def save_stability_curve(stats_dict: Dict[str, Any], output_path: Path) -> None:
    """Save the stability curve data to CSV."""
    import pandas as pd
    df = pd.DataFrame({
        'k': stats_dict['k_values'],
        'hill_estimate': stats_dict['hill_estimates'],
        'variance': stats_dict['variances']
    })
    df.to_csv(output_path, index=False)
    logger.info(f"Saved stability curve to {output_path}")

def save_tail_index_estimate(estimate: float, k: int, output_path: Path) -> None:
    """Save the final tail index estimate to JSON."""
    result = {
        'tail_index': float(estimate),
        'optimal_k': int(k),
        'method': 'Hill_estimator'
    }
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)
    logger.info(f"Saved tail index estimate to {output_path}")

def bootstrap_goodness_of_fit(
    data: np.ndarray, 
    fitted_params: Dict[str, Any],
    distribution_name: str,
    n_iter: int = 1000,
    random_state: Optional[int] = None
) -> float:
    """
    Perform bootstrap goodness-of-fit test.
    
    Parameters
    ----------
    data : np.ndarray
        Observed data.
    fitted_params : dict
        Fitted distribution parameters.
    distribution_name : str
        Name of the distribution ('pareto', 'gamma', etc.).
    n_iter : int
        Number of bootstrap iterations.
    random_state : int, optional
        Random seed for reproducibility.
        
    Returns
    -------
    float
        Bootstrap p-value.
    """
    if random_state is not None:
        np.random.seed(random_state)
        
    # Calculate KS statistic on original data
    if distribution_name == 'pareto':
        # Pareto distribution: scipy.stats.pareto(b=alpha, scale=x_min)
        alpha = fitted_params['alpha']
        x_min = fitted_params.get('x_min', np.min(data))
        cdf = stats.pareto.cdf(data, alpha, scale=x_min)
    elif distribution_name == 'gamma':
        alpha, loc, scale = fitted_params['a'], fitted_params.get('loc', 0), fitted_params.get('scale', 1)
        cdf = stats.gamma.cdf(data, alpha, loc=loc, scale=scale)
    elif distribution_name == 'lognorm':
        s = fitted_params['s']
        loc = fitted_params.get('loc', 0)
        scale = fitted_params.get('scale', 1)
        cdf = stats.lognorm.cdf(data, s, loc=loc, scale=scale)
    elif distribution_name == 'weibull':
        c = fitted_params['c']
        loc = fitted_params.get('loc', 0)
        scale = fitted_params.get('scale', 1)
        cdf = stats.weibull_min.cdf(data, c, loc=loc, scale=scale)
    elif distribution_name == 'expon':
        loc = fitted_params.get('loc', 0)
        scale = fitted_params.get('scale', 1)
        cdf = stats.expon.cdf(data, loc=loc, scale=scale)
    else:
        raise ValueError(f"Unknown distribution: {distribution_name}")
        
    ks_obs = np.max(np.abs(cdf - np.arange(1, len(cdf)+1)/len(cdf)))
    
    # Bootstrap iterations
    boot_ks = []
    for i in range(n_iter):
        # Generate synthetic data from fitted distribution
        if distribution_name == 'pareto':
            synth_data = stats.pareto.rvs(alpha, scale=x_min, size=len(data), random_state=random_state+i)
        elif distribution_name == 'gamma':
            synth_data = stats.gamma.rvs(alpha, loc=loc, scale=scale, size=len(data), random_state=random_state+i)
        elif distribution_name == 'lognorm':
            synth_data = stats.lognorm.rvs(s, loc=loc, scale=scale, size=len(data), random_state=random_state+i)
        elif distribution_name == 'weibull':
            synth_data = stats.weibull_min.rvs(c, loc=loc, scale=scale, size=len(data), random_state=random_state+i)
        elif distribution_name == 'expon':
            synth_data = stats.expon.rvs(loc=loc, scale=scale, size=len(data), random_state=random_state+i)
        else:
            raise ValueError(f"Unknown distribution: {distribution_name}")
            
        # Calculate KS statistic for synthetic data
        synth_cdf = np.sort(synth_data)
        synth_cdf_vals = stats.ppf(np.arange(1, len(synth_data)+1)/(len(synth_data)+1), 
                                  **fitted_params) if distribution_name != 'pareto' else None
        
        # Simplified KS calculation for bootstrap
        synth_cdf_emp = np.arange(1, len(synth_data)+1) / len(synth_data)
        if distribution_name == 'pareto':
            synth_cdf_theory = stats.pareto.cdf(synth_cdf_emp, alpha, scale=x_min)
        else:
            continue  # Skip if not implemented
            
        ks_boot = np.max(np.abs(synth_cdf_emp - synth_cdf_theory))
        boot_ks.append(ks_boot)
        
    # Calculate p-value
    p_value = np.mean(np.array(boot_ks) >= ks_obs)
    return p_value

def log_normal_discrimination(
    data: np.ndarray, 
    x_min: float,
    n_sim: int = 1000,
    random_state: Optional[int] = None
) -> Dict[str, Any]:
    """
    Perform Log-Normal discrimination via curvature statistic comparison.
    
    This method compares the curvature of the empirical log-log survival plot
    against simulated Log-Normal data to determine if the tail is better
    described by a Power Law (Pareto) or Log-Normal distribution.
    
    Parameters
    ----------
    data : np.ndarray
        Array of delay values (should be >= x_min).
    x_min : float
        Threshold for tail analysis.
    n_sim : int
        Number of simulations for the null distribution.
    random_state : int, optional
        Random seed.
        
    Returns
    -------
    dict
        Results including curvature statistic, p-value, and conclusion.
    """
    if random_state is not None:
        np.random.seed(random_state)
        
    # Filter data above x_min
    tail_data = data[data >= x_min]
    if len(tail_data) < 10:
        logger.warning("Not enough data points above x_min for Log-Normal discrimination")
        return {
            'curvature_statistic': np.nan,
            'p_value': np.nan,
            'conclusion': 'insufficient_data',
            'message': 'Not enough data points above x_min'
        }
        
    # Sort descending
    sorted_data = np.sort(tail_data)[::-1]
    n = len(sorted_data)
    
    # Calculate curvature statistic
    # For a power law, log-log plot should be linear (curvature ~ 0)
    # For log-normal, there should be curvature
    ranks = np.arange(1, n+1)
    log_ranks = np.log(ranks)
    log_values = np.log(sorted_data)
    
    # Fit quadratic to log-log plot to measure curvature
    # y = a*x^2 + b*x + c, curvature is related to 'a'
    coeffs = np.polyfit(log_ranks, log_values, 2)
    curvature_obs = coeffs[0]  # Quadratic coefficient
    
    # Simulate Log-Normal null distribution
    # Generate Log-Normal data with similar characteristics
    log_data = np.log(tail_data)
    mu, sigma = np.mean(log_data), np.std(log_data)
    
    curvature_null = []
    for i in range(n_sim):
        # Generate synthetic Log-Normal data
        synth_data = np.random.lognormal(mean=mu, sigma=sigma, size=n)
        synth_sorted = np.sort(synth_data)[::-1]
        synth_log_vals = np.log(synth_sorted)
        
        # Fit quadratic
        synth_coeffs = np.polyfit(log_ranks, synth_log_vals, 2)
        curvature_null.append(synth_coeffs[0])
        
    curvature_null = np.array(curvature_null)
    
    # Calculate p-value: probability of observing curvature as extreme as observed
    # under the Log-Normal null hypothesis
    # If curvature is significantly different from Log-Normal, we reject Log-Normal
    p_value = np.mean(np.abs(curvature_null) >= np.abs(curvature_obs))
    
    # Determine conclusion
    if p_value < 0.05:
        conclusion = 'reject_log_normal'
        message = 'Data significantly deviates from Log-Normal distribution'
    else:
        conclusion = 'cannot_reject_log_normal'
        message = 'Data is consistent with Log-Normal distribution'
        
    return {
        'curvature_statistic': float(curvature_obs),
        'p_value': float(p_value),
        'conclusion': conclusion,
        'message': message,
        'n_simulations': n_sim,
        'n_observations': n,
        'x_min': x_min
    }

def tail_ks_test(
    data: np.ndarray,
    fitted_params: Dict[str, Any],
    distribution_name: str,
    n_boot: int = 1000,
    random_state: Optional[int] = None
) -> Dict[str, Any]:
    """
    Perform tail Kolmogorov-Smirnov test with bootstrapped p-value correction.
    
    Parameters
    ----------
    data : np.ndarray
        Tail data (above x_min).
    fitted_params : dict
        Fitted distribution parameters.
    distribution_name : str
        Name of the distribution.
    n_boot : int
        Number of bootstrap iterations.
    random_state : int, optional
        Random seed.
        
    Returns
    -------
    dict
        KS statistic, p-value, and test result.
    """
    if random_state is not None:
        np.random.seed(random_state)
        
    # Calculate KS statistic
    if distribution_name == 'pareto':
        alpha = fitted_params['alpha']
        x_min = fitted_params.get('x_min', np.min(data))
        cdf_vals = stats.pareto.cdf(data, alpha, scale=x_min)
    else:
        raise NotImplementedError(f"KS test not implemented for {distribution_name}")
        
    # Empirical CDF
    n = len(data)
    emp_cdf = np.arange(1, n+1) / n
    ks_stat = np.max(np.abs(cdf_vals - emp_cdf))
    
    # Bootstrap p-value calculation
    boot_stats = []
    for i in range(n_boot):
        # Generate synthetic data
        synth_data = stats.pareto.rvs(alpha, scale=x_min, size=n, random_state=random_state+i)
        synth_cdf = stats.pareto.cdf(synth_data, alpha, scale=x_min)
        synth_emp = np.sort(synth_data)
        synth_emp_cdf = np.arange(1, n+1) / n
        # Recalculate KS for synthetic
        synth_cdf_vals = stats.pareto.cdf(synth_emp, alpha, scale=x_min)
        ks_boot = np.max(np.abs(synth_cdf_vals - synth_emp_cdf))
        boot_stats.append(ks_boot)
        
    p_value = np.mean(np.array(boot_stats) >= ks_stat)
    
    return {
        'ks_statistic': float(ks_stat),
        'p_value': float(p_value),
        'n_bootstrap': n_boot,
        'distribution': distribution_name
    }

def main():
    """
    Main function to run diagnostics including Log-Normal discrimination.
    This is a placeholder for the full pipeline integration.
    """
    logger.info("Running diagnostics module")
    
    # Example usage (would be replaced with actual data loading in pipeline)
    # data = load_data()
    # x_min = estimate_x_min(data)
    # result = log_normal_discrimination(data, x_min)
    # save_log_normal_test(result, 'data/results/log_normal_test.json')
    
    logger.info("Diagnostics module completed")

if __name__ == "__main__":
    main()
