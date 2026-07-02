import numpy as np
from scipy import stats
from scipy.optimize import minimize
from typing import Dict, Any, Optional, Tuple
import warnings
import json
import logging
from pathlib import Path

# Import from config if needed, though paths are usually handled in main
# Assuming config.py exists as per task list
import config

logger = logging.getLogger(__name__)

class ConvergenceError(Exception):
    """Raised when distribution fitting fails to converge."""
    pass

def fit_distribution(
    data: np.ndarray,
    dist_name: str,
    fit_kwargs: Optional[Dict[str, Any]] = None
) -> Tuple[object, Dict[str, float]]:
    """
    Fit a distribution to data using MLE.

    Args:
        data: 1D array of data points
        dist_name: Name of the scipy distribution (e.g., 'expon', 'gamma', 'norm', 'weibull_min')
        fit_kwargs: Additional arguments for the fit method (e.g., floc=0)

    Returns:
        Tuple of (distribution object, params dict)

    Raises:
        ConvergenceError: If fitting fails or returns invalid parameters
    """
    if fit_kwargs is None:
        fit_kwargs = {}

    try:
        dist = getattr(stats, dist_name)
        
        # Handle special cases for parameterization
        if dist_name == 'weibull_min':
            # scipy.stats.weibull_min uses c, loc, scale
            # We want standard Pareto-like or Weibull parameterization
            # Fit with loc fixed at 0 for delay data (delays >= 0)
            fit_kwargs.setdefault('floc', 0)
            params = dist.fit(data, **fit_kwargs)
        elif dist_name in ['expon', 'gamma', 'lognorm']:
            # Fix location at 0 for delay data
            fit_kwargs.setdefault('floc', 0)
            params = dist.fit(data, **fit_kwargs)
        else:
            params = dist.fit(data, **fit_kwargs)

        # Validate parameters
        if any(np.isnan(p) or np.isinf(p) for p in params if p != 0):
            raise ConvergenceError(f"Invalid parameters for {dist_name}: {params}")

        # Create frozen distribution with fitted parameters
        # For scipy, we need to pass params correctly
        # params usually (shape, loc, scale) or (loc, scale) depending on dist
        if dist_name == 'weibull_min':
            c, loc, scale = params
            frozen_dist = dist(c, loc=loc, scale=scale)
        elif dist_name == 'lognorm':
            s, loc, scale = params
            frozen_dist = dist(s, loc=loc, scale=scale)
        elif dist_name == 'gamma':
            a, loc, scale = params
            frozen_dist = dist(a, loc=loc, scale=scale)
        elif dist_name == 'expon':
            loc, scale = params
            frozen_dist = dist(loc=loc, scale=scale)
        else:
            frozen_dist = dist(*params)

        return frozen_dist, params

    except Exception as e:
        raise ConvergenceError(f"Failed to fit {dist_name}: {str(e)}") from e

def get_fitted_distribution(
    data: np.ndarray,
    dist_name: str
) -> Tuple[object, Dict[str, float]]:
    """Convenience wrapper for fit_distribution."""
    return fit_distribution(data, dist_name)

def fit_all_base_distributions(
    data: np.ndarray,
    exclude_pareto: bool = True
) -> Dict[str, Tuple[object, Dict[str, float]]]:
    """
    Fit all base distributions to the full cleaned data.

    Args:
        data: 1D array of delay data
        exclude_pareto: Whether to exclude Pareto from this fit (Pareto is fitted on tail)

    Returns:
        Dict mapping dist_name -> (frozen_dist, params)
    """
    distributions = ['expon', 'gamma', 'lognorm', 'weibull_min']
    if not exclude_pareto:
        distributions.append('pareto')

    results = {}
    for dist_name in distributions:
        try:
            frozen_dist, params = fit_distribution(data, dist_name)
            results[dist_name] = (frozen_dist, params)
            logger.info(f"Fitted {dist_name}: params={params}")
        except ConvergenceError as e:
            logger.warning(f"Skipping {dist_name} due to convergence error: {e}")
        except Exception as e:
            logger.error(f"Unexpected error fitting {dist_name}: {e}")

    return results

def fit_all_base_distributions_tail(
    data: np.ndarray,
    x_min: float,
    exclude_pareto: bool = True
) -> Dict[str, Tuple[object, Dict[str, float]]]:
    """
    Fit base distributions to the tail subset (data >= x_min).

    Args:
        data: Full 1D array of delay data
        x_min: Threshold for tail analysis
        exclude_pareto: Whether to exclude Pareto from this fit

    Returns:
        Dict mapping dist_name -> (frozen_dist, params)
    """
    tail_data = data[data >= x_min]
    if len(tail_data) < 10:
        logger.warning(f"Tail data too small (n={len(tail_data)}) for fitting")
        return {}

    logger.info(f"Fitting distributions to tail data (n={len(tail_data)}, x_min={x_min})")
    return fit_all_base_distributions(tail_data, exclude_pareto=exclude_pareto)

def fit_pareto_tail(
    data: np.ndarray,
    x_min: float
) -> Tuple[object, Dict[str, float]]:
    """
    Fit Pareto distribution to tail subset (data >= x_min).

    Args:
        data: Full 1D array of delay data
        x_min: Threshold for tail analysis

    Returns:
        Tuple of (frozen_dist, params)
    """
    tail_data = data[data >= x_min]
    if len(tail_data) < 10:
        raise ConvergenceError(f"Tail data too small (n={len(tail_data)}) for Pareto fitting")

    logger.info(f"Fitting Pareto to tail data (n={len(tail_data)}, x_min={x_min})")
    
    # For Pareto, we shift data by x_min and fit standard Pareto
    # scipy.stats.pareto uses b (shape), loc, scale
    # We want Pareto with scale=x_min, so we fit on (data - x_min) with floc=0
    shifted_data = tail_data - x_min
    
    try:
        frozen_dist, params = fit_distribution(shifted_data, 'pareto', {'floc': 0})
        # Adjust params: the fitted scale should be close to 1 if we did it right
        # But we want to report the actual Pareto parameters for the original data
        # Pareto PDF: f(x) = b * x_min^b / x^(b+1) for x >= x_min
        # In scipy: pareto(b, loc=x_min, scale=1) gives same shape
        # So we return the frozen distribution with loc=x_min
        b, loc, scale = params
        # Reconstruct with correct loc
        final_dist = stats.pareto(b, loc=x_min, scale=1.0)
        return final_dist, {'b': b, 'x_min': x_min}
    except Exception as e:
        raise ConvergenceError(f"Failed to fit Pareto: {e}") from e

def estimate_x_min_ks(
    data: np.ndarray,
    grid_min: Optional[float] = None,
    grid_max: Optional[float] = None,
    grid_points: int = 50
) -> float:
    """
    Estimate x_min via KS minimization over a grid.

    Args:
        data: 1D array of delay data
        grid_min: Minimum value for grid search (default: 5th percentile)
        grid_max: Maximum value for grid search (default: 95th percentile)
        grid_points: Number of points in grid

    Returns:
        Estimated x_min value
    """
    if grid_min is None:
        grid_min = np.percentile(data, 5)
    if grid_max is None:
        grid_max = np.percentile(data, 95)

    # Ensure grid_min > 0 for delay data
    grid_min = max(grid_min, 1.0)

    grid = np.linspace(grid_min, grid_max, grid_points)
    best_x_min = grid[0]
    best_ks_stat = float('inf')

    logger.info(f"Estimating x_min via KS minimization on grid [{grid_min}, {grid_max}]")

    for x_min in grid:
        tail_data = data[data >= x_min]
        if len(tail_data) < 10:
            continue

        try:
            # Fit Pareto to tail
            shifted_data = tail_data - x_min
            fitted_dist, _ = fit_distribution(shifted_data, 'pareto', {'floc': 0})
            
            # Calculate KS statistic
            ks_stat, _ = stats.kstest(shifted_data, fitted_dist.cdf)
            
            if ks_stat < best_ks_stat:
                best_ks_stat = ks_stat
                best_x_min = x_min
        except Exception as e:
            logger.debug(f"KS estimation failed at x_min={x_min}: {e}")
            continue

    logger.info(f"Estimated x_min: {best_x_min:.2f} (KS stat: {best_ks_stat:.4f})")
    return best_x_min

def save_x_min_estimate(x_min: float, output_path: str = "data/results/x_min_estimate.json") -> None:
    """Save x_min estimate to JSON file."""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    result = {
        "x_min": float(x_min),
        "description": "Estimated threshold for Pareto tail fitting via KS minimization"
    }
    
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)
    
    logger.info(f"Saved x_min estimate to {output_path}")

def calculate_aic(
    data: np.ndarray,
    frozen_dist: object,
    num_params: int
) -> float:
    """Calculate AIC for a fitted distribution."""
    log_likelihood = np.sum(frozen_dist.logpdf(data))
    return 2 * num_params - 2 * log_likelihood

def calculate_bic(
    data: np.ndarray,
    frozen_dist: object,
    num_params: int
) -> float:
    """Calculate BIC for a fitted distribution."""
    log_likelihood = np.sum(frozen_dist.logpdf(data))
    return num_params * np.log(len(data)) - 2 * log_likelihood

def calculate_ks_statistic(
    data: np.ndarray,
    frozen_dist: object
) -> Tuple[float, float]:
    """Calculate KS statistic and p-value."""
    return stats.kstest(data, frozen_dist.cdf)

def calculate_ad_statistic(
    data: np.ndarray,
    frozen_dist: object
) -> float:
    """Calculate Anderson-Darling statistic."""
    # Note: scipy.stats.anderson is for specific distributions only
    # For general case, we use ks_statistic or implement AD manually
    # Here we use ks_statistic as a proxy since AD requires distribution-specific critical values
    ks_stat, _ = stats.kstest(data, frozen_dist.cdf)
    return ks_stat * np.sqrt(len(data))  # Approximate scaling

def calculate_tail_metrics(
    data: np.ndarray,
    fitted_results: Dict[str, Tuple[object, Dict[str, float]]],
    x_min: float
) -> Dict[str, Dict[str, float]]:
    """
    Calculate AIC, BIC, KS, AD for all fitted models on tail data.

    Args:
        data: Full data array
        fitted_results: Dict of dist_name -> (frozen_dist, params)
        x_min: Threshold for tail analysis

    Returns:
        Dict mapping dist_name -> metrics dict
    """
    tail_data = data[data >= x_min]
    metrics = {}

    for dist_name, (frozen_dist, params) in fitted_results.items():
        # Count parameters
        num_params = len(params) - 2  # Exclude loc and scale if they were fixed
        if dist_name == 'pareto':
            num_params = 1  # Only shape parameter b
        elif dist_name == 'lognorm':
            num_params = 1  # Only shape parameter s (loc and scale fixed)
        else:
            num_params = max(1, num_params)

        try:
            aic = calculate_aic(tail_data, frozen_dist, num_params)
            bic = calculate_bic(tail_data, frozen_dist, num_params)
            ks_stat, ks_p = calculate_ks_statistic(tail_data, frozen_dist)
            ad_stat = calculate_ad_statistic(tail_data, frozen_dist)

            metrics[dist_name] = {
                'aic': float(aic),
                'bic': float(bic),
                'ks_statistic': float(ks_stat),
                'ks_p_value': float(ks_p),
                'ad_statistic': float(ad_stat),
                'num_params': num_params
            }
        except Exception as e:
            logger.error(f"Error calculating metrics for {dist_name}: {e}")
            continue

    return metrics

def save_model_comparison(
    metrics: Dict[str, Dict[str, float]],
    x_min: float,
    output_path: str = "data/results/model_comparison.json"
) -> None:
    """Save model comparison metrics to JSON file."""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    result = {
        "x_min": float(x_min),
        "models": metrics,
        "ranking_by_aic": sorted(metrics.keys(), key=lambda k: metrics[k]['aic'])
    }

    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)

    logger.info(f"Saved model comparison to {output_path}")

def perform_vuong_test(
    data: np.ndarray,
    model1: object,
    model2: object,
    x_min: float
) -> Dict[str, float]:
    """
    Perform Vuong test to compare two non-nested models.

    Args:
        data: Full data array
        model1: First fitted distribution
        model2: Second fitted distribution
        x_min: Threshold for tail analysis

    Returns:
        Dict with vuong_z and p_value
    """
    tail_data = data[data >= x_min]
    
    # Calculate log-likelihoods
    ll1 = np.sum(model1.logpdf(tail_data))
    ll2 = np.sum(model2.logpdf(tail_data))
    
    # Calculate pointwise log-likelihood differences
    log_likelihoods_1 = model1.logpdf(tail_data)
    log_likelihoods_2 = model2.logpdf(tail_data)
    diff = log_likelihoods_1 - log_likelihoods_2
    
    # Vuong statistic
    n = len(tail_data)
    mean_diff = np.mean(diff)
    std_diff = np.std(diff, ddof=1)
    
    if std_diff == 0:
        vuong_z = 0.0
    else:
        vuong_z = mean_diff * np.sqrt(n) / std_diff
    
    # Two-tailed p-value
    p_value = 2 * (1 - stats.norm.cdf(abs(vuong_z)))
    
    return {
        "vuong_z": float(vuong_z),
        "p_value": float(p_value),
        "interpretation": "model1_better" if vuong_z > 1.96 else ("model2_better" if vuong_z < -1.96 else "no_difference")
    }

def save_vuong_test_results(
    results: Dict[str, float],
    model1_name: str,
    model2_name: str,
    output_path: str = "data/results/vuong_test_results.json"
) -> None:
    """Save Vuong test results to JSON file."""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    result = {
        "model1": model1_name,
        "model2": model2_name,
        **results
    }

    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)

    logger.info(f"Saved Vuong test results to {output_path}")

def compare_component_distributions(
    total_delay: np.ndarray,
    arr_delay: np.ndarray,
    dep_delay: np.ndarray,
    output_path: str = "data/results/component_comparison.json"
) -> Dict[str, Any]:
    """
    Compare sum distribution (total_delay) vs components (ArrDelay, DepDelay)
    via KS test and descriptive statistics.

    Args:
        total_delay: Array of total delays (ArrDelay + DepDelay)
        arr_delay: Array of arrival delays
        dep_delay: Array of departure delays
        output_path: Path to save results

    Returns:
        Dict containing comparison results
    """
    logger.info("Comparing component distributions (total vs arrival vs departure delays)")
    
    # Filter out negative values for analysis (as per preprocessing rules)
    valid_mask = (total_delay >= 0) & (arr_delay >= 0) & (dep_delay >= 0)
    total_valid = total_delay[valid_mask]
    arr_valid = arr_delay[valid_mask]
    dep_valid = dep_delay[valid_mask]

    if len(total_valid) < 10:
        raise ValueError("Insufficient valid data for component comparison")

    results = {
        "sample_sizes": {
            "total_delay": int(len(total_valid)),
            "arr_delay": int(len(arr_valid)),
            "dep_delay": int(len(dep_valid))
        },
        "descriptive_statistics": {}
    }

    for name, data in [("total_delay", total_valid), ("arr_delay", arr_valid), ("dep_delay", dep_valid)]:
        results["descriptive_statistics"][name] = {
            "mean": float(np.mean(data)),
            "median": float(np.median(data)),
            "std": float(np.std(data)),
            "min": float(np.min(data)),
            "max": float(np.max(data)),
            "percentile_90": float(np.percentile(data, 90)),
            "percentile_95": float(np.percentile(data, 95)),
            "percentile_99": float(np.percentile(data, 99))
        }

    # KS tests
    ks_results = {}
    
    # Total vs Arrival
    ks_arr, p_arr = stats.ks_2samp(total_valid, arr_valid)
    ks_results["total_vs_arrival"] = {
        "ks_statistic": float(ks_arr),
        "p_value": float(p_arr),
        "significant_at_0.05": bool(p_arr < 0.05)
    }

    # Total vs Departure
    ks_dep, p_dep = stats.ks_2samp(total_valid, dep_valid)
    ks_results["total_vs_departure"] = {
        "ks_statistic": float(ks_dep),
        "p_value": float(p_dep),
        "significant_at_0.05": bool(p_dep < 0.05)
    }

    # Arrival vs Departure
    ks_arr_dep, p_arr_dep = stats.ks_2samp(arr_valid, dep_valid)
    ks_results["arrival_vs_departure"] = {
        "ks_statistic": float(ks_arr_dep),
        "p_value": float(p_arr_dep),
        "significant_at_0.05": bool(p_arr_dep < 0.05)
    }

    results["ks_tests"] = ks_results

    # Correlation analysis
    corr_total_arr = np.corrcoef(total_valid, arr_valid)[0, 1]
    corr_total_dep = np.corrcoef(total_valid, dep_valid)[0, 1]
    corr_arr_dep = np.corrcoef(arr_valid, dep_valid)[0, 1]

    results["correlations"] = {
        "total_delay_vs_arrival": float(corr_total_arr),
        "total_delay_vs_departure": float(corr_total_dep),
        "arrival_vs_departure": float(corr_arr_dep)
    }

    # Save to file
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)

    logger.info(f"Saved component comparison results to {output_path}")
    
    return results

def main():
    """Main entry point for model fitting and analysis."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('data/logs/pipeline.log')
        ]
    )

    logger.info("Starting model fitting and analysis...")

    # This function is typically called from main.py stage 2
    # For standalone execution, we would need to load data first
    # which is handled by preprocessing.py stage 1

    logger.info("Model fitting module loaded successfully.")

if __name__ == "__main__":
    main()
