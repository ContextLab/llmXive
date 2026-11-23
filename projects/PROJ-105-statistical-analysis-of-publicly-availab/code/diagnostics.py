import numpy as np
from scipy import stats
from scipy.optimize import minimize_scalar, minimize
from scipy import optimize
import json
import logging
import pandas as pd
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
from utils import PipelineError

logger = logging.getLogger(__name__)

def estimate_hill_index(data: np.ndarray, k: int) -> float:
    """
    Estimate the tail index (alpha) using the Hill estimator.
    
    Args:
        data: Sorted array of delay values (ascending).
        k: Number of top order statistics to use.
        
    Returns:
        Hill estimate of the tail index alpha.
    """
    if k <= 0 or k >= len(data):
        raise ValueError(f"k must be between 0 and len(data) ({len(data)}), got {k}")
    
    # Sort data descending to get largest values first
    sorted_data = np.sort(data)[::-1]
    
    # Hill estimator: alpha_hat = (1/k) * sum_{i=1}^k log(X_(i)/X_(k+1))
    # where X_(i) are the order statistics (largest first)
    log_ratios = np.log(sorted_data[:k] / sorted_data[k])
    alpha_hat = 1.0 / np.mean(log_ratios)
    
    return alpha_hat

def compute_hill_stability_curve(data: np.ndarray, k_min: int = 10, k_max: Optional[int] = None, window_size: int = 10) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Compute the Hill estimator stability curve.
    
    Args:
        data: Array of delay values.
        k_min: Minimum k to start the curve.
        k_max: Maximum k (default: floor(0.1 * n)).
        window_size: Size of sliding window for variance calculation.
        
    Returns:
        Tuple of (k_values, alpha_estimates, variances).
    """
    n = len(data)
    if k_max is None:
        k_max = int(0.1 * n)
    
    # Ensure k_max doesn't exceed bounds
    k_max = min(k_max, n - 1)
    k_max = max(k_max, k_min + window_size)  # Ensure we have enough points for variance
    
    if k_min >= k_max:
        raise ValueError(f"k_min ({k_min}) must be less than k_max ({k_max})")
    
    k_values = np.arange(k_min, k_max + 1)
    alpha_estimates = np.zeros(len(k_values))
    
    for i, k in enumerate(k_values):
        alpha_estimates[i] = estimate_hill_index(data, k)
    
    # Compute variance over sliding window
    variances = np.zeros(len(k_values))
    for i in range(len(k_values)):
        start_idx = max(0, i - window_size + 1)
        window = alpha_estimates[start_idx:i + 1]
        if len(window) > 1:
            variances[i] = np.var(window)
        else:
            variances[i] = 0.0
    
    return k_values, alpha_estimates, variances

def find_optimal_k_stability(k_values: np.ndarray, variances: np.ndarray, alpha_estimates: np.ndarray, n: int) -> Tuple[int, float, float]:
    """
    Find the k that minimizes variance in the stability curve.
    
    Args:
        k_values: Array of k values.
        variances: Array of variance values.
        alpha_estimates: Array of alpha estimates.
        n: Total number of data points.
        
    Returns:
        Tuple of (optimal_k, optimal_alpha, min_variance).
    """
    # Constraint: k/n <= 0.1
    valid_mask = k_values / n <= 0.1
    if not np.any(valid_mask):
        raise ValueError("No valid k values satisfy k/n <= 0.1")
    
    valid_indices = np.where(valid_mask)[0]
    valid_variances = variances[valid_indices]
    valid_k = k_values[valid_indices]
    valid_alpha = alpha_estimates[valid_indices]
    
    min_idx = np.argmin(valid_variances)
    optimal_k = valid_k[min_idx]
    optimal_alpha = valid_alpha[min_idx]
    min_variance = valid_variances[min_idx]
    
    # Verify constraint
    assert optimal_k / n <= 0.1, f"Constraint violation: {optimal_k}/{n} = {optimal_k/n} > 0.1"
    
    return int(optimal_k), optimal_alpha, min_variance

def calculate_hill_confidence_interval(alpha: float, k: int, confidence: float = 0.95) -> Tuple[float, float]:
    """
    Calculate confidence interval for the Hill estimator.
    
    Args:
        alpha: Estimated tail index.
        k: Number of order statistics used.
        confidence: Confidence level (e.g., 0.95).
        
    Returns:
        Tuple of (lower_bound, upper_bound).
    """
    # Asymptotic variance of Hill estimator is alpha^2 / k
    # Standard error
    se = alpha / np.sqrt(k)
    
    # Z-score for confidence level
    z = stats.norm.ppf((1 + confidence) / 2)
    
    lower = alpha - z * se
    upper = alpha + z * se
    
    return lower, upper

def run_hill_stability_analysis(x_min: float, data_path: str, output_dir: str, window_size: int = 10) -> Dict[str, Any]:
    """
    Run the full Hill estimator stability analysis.
    
    Args:
        x_min: Tail threshold from x_min_estimate.json.
        data_path: Path to the zero-excluded dataset.
        output_dir: Directory to save results.
        window_size: Sliding window size for variance calculation.
        
    Returns:
        Dictionary with analysis results.
    """
    # Load data
    logger.info(f"Loading data from {data_path}")
    df = pd.read_csv(data_path)
    
    # Filter for tail data
    tail_data = df[df['total_delay'] >= x_min]['total_delay'].values
    n = len(tail_data)
    
    if n == 0:
        raise PipelineError(f"No data points >= x_min ({x_min}) found in {data_path}")
    
    logger.info(f"Found {n} tail data points (x >= {x_min})")
    
    # Compute stability curve
    k_min = 10
    k_max = None  # Will be set to floor(0.1 * n)
    
    k_values, alpha_estimates, variances = compute_hill_stability_curve(
        tail_data, k_min=k_min, k_max=k_max, window_size=window_size
    )
    
    # Find optimal k
    optimal_k, optimal_alpha, min_variance = find_optimal_k_stability(
        k_values, variances, alpha_estimates, n
    )
    
    # Calculate confidence interval
    ci_lower, ci_upper = calculate_hill_confidence_interval(optimal_alpha, optimal_k)
    
    # Save stability curve
    output_dir_path = Path(output_dir)
    output_dir_path.mkdir(parents=True, exist_ok=True)
    
    stability_curve_path = output_dir_path / "stability_curve.csv"
    stability_df = pd.DataFrame({
        'k': k_values,
        'alpha_estimate': alpha_estimates,
        'variance': variances
    })
    stability_df.to_csv(stability_curve_path, index=False)
    logger.info(f"Saved stability curve to {stability_curve_path}")
    
    # Save tail index estimate
    result = {
        'optimal_k': int(optimal_k),
        'estimated_alpha': float(optimal_alpha),
        'confidence_interval': {
            'lower': float(ci_lower),
            'upper': float(ci_upper),
            'confidence_level': 0.95
        },
        'min_variance': float(min_variance),
        'n_tail_records': int(n),
        'x_min': float(x_min),
        'window_size': window_size,
        'k_max_used': int(k_values[-1])
    }
    
    tail_index_path = output_dir_path / "tail_index_estimate.json"
    with open(tail_index_path, 'w') as f:
        json.dump(result, f, indent=2)
    logger.info(f"Saved tail index estimate to {tail_index_path}")
    
    return result

def save_hill_results(results: Dict[str, Any], output_path: str):
    """Save Hill estimator results to JSON."""
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)

def calculate_r2_on_tail(data: np.ndarray, model_name: str, params: Dict[str, float], x_min: float) -> Tuple[float, Dict[str, Any]]:
    """
    Calculate R² for a fitted model on the tail data using log-log survival.
    
    Args:
        data: Array of delay values.
        model_name: Name of the distribution model.
        params: Fitted parameters.
        x_min: Tail threshold.
        
    Returns:
        Tuple of (r_squared, plot_data).
    """
    # Filter tail data
    tail_data = data[data >= x_min]
    if len(tail_data) == 0:
        return 0.0, {}
    
    # Sort descending
    tail_data = np.sort(tail_data)[::-1]
    n = len(tail_data)
    
    # Empirical survival function (rank-based)
    # S(x) = (n - rank + 1) / n for sorted data
    ranks = np.arange(1, n + 1)
    empirical_survival = (n - ranks + 1) / n
    
    # Log-log transformation
    log_x = np.log(tail_data)
    log_s = np.log(empirical_survival)
    
    # Remove infinite values
    valid_mask = np.isfinite(log_x) & np.isfinite(log_s)
    log_x = log_x[valid_mask]
    log_s = log_s[valid_mask]
    
    if len(log_x) < 2:
        return 0.0, {}
    
    # OLS regression
    slope, intercept, r_value, p_value, std_err = stats.linregress(log_x, log_s)
    r_squared = r_value ** 2
    
    plot_data = {
        'log_x': log_x.tolist(),
        'log_s': log_s.tolist(),
        'slope': float(slope),
        'intercept': float(intercept),
        'r_squared': float(r_squared)
    }
    
    return r_squared, plot_data

def perform_tail_ks_test(data: np.ndarray, model_name: str, params: Dict[str, float], x_min: float) -> Dict[str, Any]:
    """
    Perform Kolmogorov-Smirnov goodness-of-fit test on the tail.
    
    Args:
        data: Array of delay values.
        model_name: Name of the distribution model.
        params: Fitted parameters.
        x_min: Tail threshold.
        
    Returns:
        Dictionary with KS test results.
    """
    # Filter tail data
    tail_data = data[data >= x_min]
    if len(tail_data) == 0:
        raise PipelineError(f"No tail data found for x >= {x_min}")
    
    # Normalize tail data for testing (shift to start at 0)
    # For Pareto, we test (X - x_min) / x_min or just X with scale=x_min
    # scipy.stats.pareto uses scale parameter which is x_m (minimum value)
    
    try:
        if model_name.lower() == 'pareto':
            # Pareto distribution: scipy.stats.pareto(b, scale=x_min)
            b = params.get('b', params.get('alpha', 1.0))
            scale = x_min
            cdf_func = lambda x: stats.pareto.cdf(x, b, scale=scale)
        elif model_name.lower() == 'exponential':
            # Exponential: scale = 1/lambda
            loc = params.get('loc', 0)
            scale = params.get('scale', 1.0)
            cdf_func = lambda x: stats.expon.cdf(x, loc=loc, scale=scale)
        elif model_name.lower() == 'gamma':
            loc = params.get('loc', 0)
            scale = params.get('scale', 1.0)
            a = params.get('a', 1.0)
            cdf_func = lambda x: stats.gamma.cdf(x, a, loc=loc, scale=scale)
        elif model_name.lower() == 'lognormal':
            loc = params.get('loc', 0)
            scale = params.get('scale', 1.0)
            s = params.get('s', 1.0)
            cdf_func = lambda x: stats.lognorm.cdf(x, s, loc=loc, scale=scale)
        elif model_name.lower() == 'weibull':
            c = params.get('c', 1.0)
            loc = params.get('loc', 0)
            scale = params.get('scale', 1.0)
            cdf_func = lambda x: stats.weibull_min.cdf(x, c, loc=loc, scale=scale)
        else:
            raise ValueError(f"Unknown model: {model_name}")
        
        # Perform KS test
        ks_stat, p_value = stats.kstest(tail_data, cdf_func)
        
        result = {
            'model_name': model_name,
            'ks_statistic': float(ks_stat),
            'p_value': float(p_value),
            'tail_threshold': float(x_min),
            'n_tail_records': int(len(tail_data))
        }
        
        return result
        
    except Exception as e:
        logger.error(f"KS test failed for {model_name}: {e}")
        return {
            'model_name': model_name,
            'ks_statistic': float('nan'),
            'p_value': float('nan'),
            'tail_threshold': float(x_min),
            'n_tail_records': int(len(tail_data)),
            'error': str(e)
        }

def check_model_rejection(r_squared: float, hill_stable: bool, r2_threshold: float = 0.95, hill_variance_threshold: float = 0.1) -> Dict[str, Any]:
    """
    Check if a model should be rejected based on R² and Hill stability.
    
    Args:
        r_squared: R² value from log-log fit.
        hill_stable: Whether Hill index is stable.
        r2_threshold: Minimum acceptable R².
        hill_variance_threshold: Maximum acceptable variance for stability.
        
    Returns:
        Dictionary with rejection status and reason.
    """
    if r_squared < r2_threshold:
        return {
            'status': 'rejected',
            'reason': f"R² ({r_squared:.4f}) < threshold ({r2_threshold})"
        }
    
    if not hill_stable:
        return {
            'status': 'rejected',
            'reason': f"Hill index unstable (variance > {hill_variance_threshold})"
        }
    
    return {
        'status': 'accepted',
        'reason': 'Model passes both R² and Hill stability checks'
    }

def update_model_comparison(model_comparison_path: str, rejection_results: Dict[str, Any]):
    """Update model_comparison.json with rejection status."""
    try:
        with open(model_comparison_path, 'r') as f:
            data = json.load(f)
        
        # Add status to each model
        if 'models' in data:
            for model in data['models']:
                model_name = model.get('model_name')
                if model_name in rejection_results:
                    model['status'] = rejection_results[model_name]['status']
                    model['rejection_reason'] = rejection_results[model_name].get('reason', '')
        
        with open(model_comparison_path, 'w') as f:
            json.dump(data, f, indent=2)
            
    except Exception as e:
        logger.error(f"Failed to update model comparison: {e}")

def main():
    """Main entry point for Hill estimator stability analysis."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run Hill estimator stability analysis')
    parser.add_argument('--x-min', type=float, required=True, help='x_min threshold')
    parser.add_argument('--data', type=str, required=True, help='Path to zero-excluded CSV')
    parser.add_argument('--output-dir', type=str, default='data/results', help='Output directory')
    parser.add_argument('--window-size', type=int, default=10, help='Sliding window size')
    
    args = parser.parse_args()
    
    # Load x_min if provided as file path
    x_min = args.x_min
    if not isinstance(x_min, float):
        try:
            with open(x_min, 'r') as f:
                x_min_data = json.load(f)
                x_min = x_min_data.get('estimated_x_min', x_min_data.get('x_min', 0.0))
        except:
            pass
    
    logger.info(f"Starting Hill stability analysis with x_min={x_min}")
    
    result = run_hill_stability_analysis(
        x_min=x_min,
        data_path=args.data,
        output_dir=args.output_dir,
        window_size=args.window_size
    )
    
    logger.info(f"Analysis complete. Optimal k={result['optimal_k']}, Alpha={result['estimated_alpha']:.4f}")
    return result

if __name__ == '__main__':
    main()