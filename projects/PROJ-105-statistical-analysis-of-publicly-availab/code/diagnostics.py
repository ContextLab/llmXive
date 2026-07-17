import numpy as np
from scipy import stats
from scipy.optimize import minimize_scalar
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import os

from config import get_bts_url, TARGET_YEAR, RANDOM_SEED
from utils import check_memory_limit, log_peak_memory, setup_logging

# Configure logger for this module
logger = setup_logging()

def validate_stability_window(hill_values: np.ndarray, k_values: np.ndarray, max_fraction: float = 0.1) -> Tuple[bool, int]:
    """
    Validate the stability window for the Hill estimator.
    
    Args:
        hill_values: Array of Hill index estimates.
        k_values: Array of corresponding k values (number of top order statistics).
        max_fraction: Maximum allowed fraction of k/n.
        
    Returns:
        Tuple of (is_stable, optimal_k)
    """
    n = len(hill_values)
    if n == 0:
        return False, 0
        
    # Filter k values within the allowed range
    valid_indices = k_values <= (n * max_fraction)
    if not np.any(valid_indices):
        return False, 0
        
    valid_hill = hill_values[valid_indices]
    valid_k = k_values[valid_indices]
    
    if len(valid_hill) < 2:
        return False, 0
        
    # Check for stability (low variance in the tail)
    window_size = 10
    if len(valid_hill) < window_size:
        return False, 0
        
    # Calculate rolling variance
    rolling_var = np.var(valid_hill[:window_size])
    
    # Stability criterion: variance should be relatively low
    # This is a heuristic; adjust threshold as needed
    is_stable = rolling_var < 0.1 * np.mean(valid_hill)**2
    
    # Find optimal k (minimum variance window)
    min_var = np.inf
    optimal_k = valid_k[0]
    for i in range(len(valid_hill) - window_size + 1):
        var = np.var(valid_hill[i:i+window_size])
        if var < min_var:
            min_var = var
            optimal_k = valid_k[i + window_size // 2]
            
    return is_stable, int(optimal_k)

def hill_estimator(data: np.ndarray, k_values: Optional[np.ndarray] = None) -> Tuple[np.ndarray, np.ndarray, float]:
    """
    Compute the Hill estimator for a range of k values.
    
    Args:
        data: Sorted array of delay values (ascending).
        k_values: Array of k values to evaluate. If None, generates automatically.
        
    Returns:
        Tuple of (k_values, hill_estimates, optimal_hill)
    """
    n = len(data)
    if n < 10:
        raise ValueError("Dataset too small for Hill estimation")
        
    if k_values is None:
        # Generate k values from 10 to 10% of n
        max_k = int(n * 0.1)
        if max_k < 10:
            max_k = 10
        k_values = np.arange(10, max_k + 1)
        
    hill_estimates = []
    
    for k in k_values:
        if k >= n:
            break
            
        # Sort data in descending order for Hill estimator
        sorted_data = np.sort(data)[::-1]
        x_k = sorted_data[k-1]  # k-th largest value
        
        # Hill estimator: mean of log(X_i / X_k) for i=1..k
        log_ratios = np.log(sorted_data[:k] / x_k)
        hill_estimate = np.mean(log_ratios)
        hill_estimates.append(hill_estimate)
        
    hill_estimates = np.array(hill_estimates)
    
    # Find optimal k (minimum variance window)
    window_size = 10
    if len(hill_estimates) >= window_size:
        min_var = np.inf
        optimal_idx = 0
        for i in range(len(hill_estimates) - window_size + 1):
            var = np.var(hill_estimates[i:i+window_size])
            if var < min_var:
                min_var = var
                optimal_idx = i + window_size // 2
        optimal_hill = hill_estimates[optimal_idx]
    else:
        optimal_hill = hill_estimates[-1]
        
    return k_values, hill_estimates, optimal_hill

def compute_hill_statistics(data: np.ndarray, k_values: Optional[np.ndarray] = None) -> Dict[str, Any]:
    """
    Compute comprehensive Hill estimator statistics.
    
    Args:
        data: Array of delay values.
        k_values: Optional array of k values to evaluate.
        
    Returns:
        Dictionary with Hill statistics.
    """
    k_vals, hill_vals, optimal_hill = hill_estimator(data, k_values)
    is_stable, optimal_k = validate_stability_window(hill_vals, k_vals)
    
    return {
        "k_values": k_vals.tolist(),
        "hill_estimates": hill_vals.tolist(),
        "optimal_hill_index": float(optimal_hill),
        "optimal_k": int(optimal_k),
        "is_stable": is_stable,
        "sample_size": int(len(data))
    }

def save_stability_curve(k_values: np.ndarray, hill_values: np.ndarray, output_path: Path) -> None:
    """
    Save stability curve data to CSV.
    
    Args:
        k_values: Array of k values.
        hill_values: Array of Hill estimates.
        output_path: Path to save the CSV file.
    """
    import pandas as pd
    
    df = pd.DataFrame({
        "k": k_values,
        "hill_estimate": hill_values
    })
    df.to_csv(output_path, index=False)
    logger.info(f"Stability curve saved to {output_path}")

def save_tail_index_estimate(stats_dict: Dict[str, Any], output_path: Path) -> None:
    """
    Save tail index estimate to JSON.
    
    Args:
        stats_dict: Dictionary with Hill statistics.
        output_path: Path to save the JSON file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(stats_dict, f, indent=2)
    logger.info(f"Tail index estimate saved to {output_path}")

def bootstrap_goodness_of_fit(data: np.ndarray, fitted_params: Dict[str, Any], 
                             distribution_name: str, n_iter: int = 1000, 
                             x_min: Optional[float] = None) -> Dict[str, Any]:
    """
    Perform bootstrap goodness-of-fit test for a fitted distribution.
    
    Args:
        data: Observed data (tail subset if x_min is provided).
        fitted_params: Parameters of the fitted distribution.
        distribution_name: Name of the distribution (e.g., 'pareto', 'gamma').
        n_iter: Number of bootstrap iterations.
        x_min: Threshold for tail analysis.
        
    Returns:
        Dictionary with bootstrap GoF results.
    """
    check_memory_limit()
    log_peak_memory()
    
    if x_min is not None:
        tail_data = data[data >= x_min]
    else:
        tail_data = data
        
    n = len(tail_data)
    if n < 10:
        raise ValueError("Insufficient data for bootstrap GoF test")
        
    # Calculate test statistic on observed data
    if distribution_name == 'pareto':
        alpha = fitted_params.get('alpha', 1.0)
        # Kolmogorov-Smirnov statistic for Pareto
        sorted_data = np.sort(tail_data)
        empirical_cdf = np.arange(1, n+1) / n
        theoretical_cdf = 1 - (sorted_data / sorted_data[0])**(-alpha)
        ks_stat = np.max(np.abs(empirical_cdf - theoretical_cdf))
    else:
        # Fallback to general KS test
        from scipy import stats as scipy_stats
        # Get distribution object
        dist = getattr(scipy_stats, distribution_name)
        ks_stat = scipy_stats.kstest(tail_data, distribution_name, args=tuple(fitted_params.values())).statistic
        
    # Bootstrap loop
    bootstrap_stats = []
    for i in range(n_iter):
        # Generate bootstrap sample
        if distribution_name == 'pareto':
            alpha = fitted_params.get('alpha', 1.0)
            # Generate Pareto samples
            bootstrap_sample = sorted_data[0] * (1 - np.random.uniform(0, 1, n))**(-1/alpha)
        else:
            dist = getattr(scipy_stats, distribution_name)
            bootstrap_sample = dist.rvs(*tuple(fitted_params.values()), size=n)
            
        # Calculate KS statistic for bootstrap sample
        sorted_boot = np.sort(bootstrap_sample)
        empirical_boot = np.arange(1, n+1) / n
        
        if distribution_name == 'pareto':
            theoretical_boot = 1 - (sorted_boot / sorted_boot[0])**(-alpha)
            boot_ks = np.max(np.abs(empirical_boot - theoretical_boot))
        else:
            boot_ks = scipy_stats.kstest(bootstrap_sample, distribution_name, 
                                       args=tuple(fitted_params.values())).statistic
                
        bootstrap_stats.append(boot_ks)
        
    bootstrap_stats = np.array(bootstrap_stats)
    p_value = np.mean(bootstrap_stats >= ks_stat)
    
    return {
        "observed_ks_statistic": float(ks_stat),
        "bootstrap_p_value": float(p_value),
        "n_iterations": n_iter,
        "distribution": distribution_name,
        "sample_size": n,
        "x_min": float(x_min) if x_min is not None else None,
        "reject_null": p_value < 0.1
    }

def log_normal_discrimination(data: np.ndarray, x_min: float, n_simulations: int = 1000) -> Dict[str, Any]:
    """
    Perform Log-Normal discrimination via curvature statistic comparison.
    
    This test compares the curvature of the empirical log-log survival plot
    to that expected under a Log-Normal null hypothesis.
    
    Args:
        data: Array of delay values (should include tail).
        x_min: Threshold for tail analysis.
        n_simulations: Number of simulations for null distribution.
        
    Returns:
        Dictionary with Log-Normal discrimination results.
    """
    check_memory_limit()
    log_peak_memory()
    
    # Filter tail data
    tail_data = data[data >= x_min]
    n = len(tail_data)
    
    if n < 20:
        raise ValueError("Insufficient tail data for Log-Normal discrimination")
        
    # Sort data
    sorted_data = np.sort(tail_data)[::-1]  # Descending order
    
    # Compute empirical log-log survival plot
    ranks = np.arange(1, n+1)
    log_x = np.log(sorted_data)
    log_survival = np.log(ranks / n)
    
    # Calculate curvature statistic (second derivative approximation)
    # Using central differences for interior points
    if len(log_x) < 5:
        curvature_obs = 0.0
    else:
        # Second derivative of log-survival vs log-x
        # Approximate using finite differences
        curvature_obs = np.zeros(len(log_x) - 2)
        for i in range(len(log_x) - 2):
            # Curvature at point i+1
            h = log_x[i+2] - log_x[i]
            if h == 0:
                curvature_obs[i] = 0
            else:
                # Second derivative approximation
                d2y = (log_survival[i+2] - 2*log_survival[i+1] + log_survival[i])
                curvature_obs[i] = d2y / (h**2)
        
        # Use mean absolute curvature as test statistic
        curvature_obs = np.mean(np.abs(curvature_obs))
        
    # Generate null distribution under Log-Normal hypothesis
    # Fit Log-Normal to tail data
    from scipy import stats as scipy_stats
    ln_params = scipy_stats.lognorm.fit(tail_data)
    
    curvature_null = []
    for _ in range(n_simulations):
        # Generate Log-Normal sample
        sim_data = scipy_stats.lognorm.rvs(*ln_params, size=n)
        sim_sorted = np.sort(sim_data)[::-1]
        
        sim_ranks = np.arange(1, n+1)
        sim_log_x = np.log(sim_sorted)
        sim_log_survival = np.log(sim_ranks / n)
        
        # Calculate curvature for simulated data
        if len(sim_log_x) < 5:
            curvature_sim = 0.0
        else:
            curvature_sim = np.zeros(len(sim_log_x) - 2)
            for i in range(len(sim_log_x) - 2):
                h = sim_log_x[i+2] - sim_log_x[i]
                if h == 0:
                    curvature_sim[i] = 0
                else:
                    d2y = (sim_log_survival[i+2] - 2*sim_log_survival[i+1] + sim_log_survival[i])
                    curvature_sim[i] = d2y / (h**2)
            
            curvature_sim = np.mean(np.abs(curvature_sim))
            
        curvature_null.append(curvature_sim)
        
    curvature_null = np.array(curvature_null)
    
    # Calculate p-value
    p_value = np.mean(curvature_null >= curvature_obs)
    
    # Interpretation: 
    # Low p-value suggests data is NOT Log-Normal (reject Log-Normal)
    # High p-value suggests data could be Log-Normal
    is_log_normal = p_value > 0.1
    
    return {
        "observed_curvature": float(curvature_obs),
        "mean_null_curvature": float(np.mean(curvature_null)),
        "null_std_curvature": float(np.std(curvature_null)),
        "p_value": float(p_value),
        "n_simulations": n_simulations,
        "sample_size": n,
        "x_min": float(x_min),
        "is_log_normal": is_log_normal,
        "interpretation": "Reject Log-Normal" if not is_log_normal else "Cannot reject Log-Normal"
    }

def main():
    """
    Main function to run Log-Normal discrimination analysis.
    """
    # Setup logging
    log_file = Path("data/logs/pipeline.log")
    log_file.parent.mkdir(parents=True, exist_ok=True)
    logger = setup_logging(log_file=log_file)
    
    logger.info("Starting Log-Normal discrimination analysis (T035)")
    
    try:
        # Load cleaned data
        data_path = Path("data/processed/cleaned_delays.csv")
        if not data_path.exists():
            raise FileNotFoundError(f"Cleaned data not found at {data_path}")
            
        import pandas as pd
        df = pd.read_csv(data_path)
        
        # Get delay data (total_delay column)
        if 'total_delay' not in df.columns:
            raise ValueError("total_delay column not found in cleaned data")
            
        delay_data = df['total_delay'].values
        
        # Filter positive delays only (for tail analysis)
        positive_delays = delay_data[delay_data > 0]
        
        if len(positive_delays) < 100:
            raise ValueError("Insufficient positive delay data for analysis")
            
        # Load x_min estimate
        x_min_path = Path("data/results/x_min_estimate.json")
        if not x_min_path.exists():
            raise FileNotFoundError(f"x_min estimate not found at {x_min_path}")
            
        with open(x_min_path, 'r') as f:
            x_min_data = json.load(f)
            
        x_min = x_min_data['x_min']
        logger.info(f"Using x_min = {x_min}")
        
        # Perform Log-Normal discrimination
        result = log_normal_discrimination(positive_delays, x_min, n_simulations=1000)
        
        # Save results
        output_path = Path("data/results/log_normal_test.json")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            json.dump(result, f, indent=2)
            
        logger.info(f"Log-Normal discrimination results saved to {output_path}")
        logger.info(f"Result: {result['interpretation']} (p-value: {result['p_value']:.4f})")
        
        # Log summary
        print(f"Log-Normal Discrimination Analysis Complete")
        print(f"  x_min: {x_min}")
        print(f"  Sample size: {result['sample_size']}")
        print(f"  Observed curvature: {result['observed_curvature']:.6f}")
        print(f"  P-value: {result['p_value']:.4f}")
        print(f"  Conclusion: {result['interpretation']}")
        
        return result
        
    except Exception as e:
        logger.error(f"Error in Log-Normal discrimination analysis: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
