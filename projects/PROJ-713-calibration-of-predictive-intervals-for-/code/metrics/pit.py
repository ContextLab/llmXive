"""
Probability Integral Transform (PIT) metrics for distributional calibration.

Implements PIT calculation, histogram generation, and the Ljung-Box test
for uniformity as specified in FR-004 and SC-002.

This module avoids the Kolmogorov-Smirnov test in favor of Ljung-Box to
account for potential autocorrelation in the PIT sequence.
"""

import numpy as np
import pandas as pd
from typing import List, Dict, Tuple, Optional, Union, Any
from scipy import stats
from utils.logger import get_logger
from utils.exceptions import DataValidationError

logger = get_logger(__name__)


def calculate_pit(
    forecasts: Union[np.ndarray, List[float]],
    actuals: Union[np.ndarray, List[float]],
    predictive_cdf: Optional[callable] = None,
    predictive_samples: Optional[np.ndarray] = None
) -> np.ndarray:
    """
    Calculate the Probability Integral Transform (PIT) values for a set of forecasts.

    The PIT value for an observation y and forecast distribution F is F(y).
    If F is continuous and correctly specified, PIT values should be uniformly
    distributed on [0, 1].

    Args:
        forecasts: Not directly used if CDF or samples are provided.
        actuals: The observed ground truth values (y).
        predictive_cdf: A callable CDF function F(y) for the forecast distribution.
                        If provided, this is used directly.
        predictive_samples: If CDF is not provided, an array of shape (n_samples,)
                            representing draws from the predictive distribution.
                            Used to estimate the empirical CDF.

    Returns:
        np.ndarray: PIT values in the range [0, 1].

    Raises:
        DataValidationError: If neither CDF nor samples are provided, or if inputs are invalid.
    """
    actuals = np.asarray(actuals, dtype=float)
    forecasts = np.asarray(forecasts, dtype=float)

    if actuals.size == 0:
        raise DataValidationError("Actuals array is empty.")
    if actuals.shape != forecasts.shape:
        # Forecasts shape check is flexible depending on how samples are passed,
        # but for direct CDF usage, they should match or be broadcastable.
        logger.warning(f"Shape mismatch check: actuals {actuals.shape}, forecasts {forecasts.shape}")

    pit_values = np.zeros_like(actuals)

    if predictive_cdf is not None:
        # Use the provided CDF directly
        try:
            # Assume CDF takes scalar or array and returns probability
            # We iterate if the CDF is not vectorized for safety, or vectorize if possible
            if callable(predictive_cdf):
                # Try vectorized call first
                try:
                    pit_values = predictive_cdf(actuals)
                except Exception:
                    # Fallback to scalar iteration
                    pit_values = np.array([predictive_cdf(y) for y in actuals])
        except Exception as e:
            raise DataValidationError(f"Error evaluating predictive CDF: {e}")

    elif predictive_samples is not None:
        # Estimate CDF using empirical distribution from samples
        # predictive_samples shape: (n_samples,)
        # We need to estimate P(Y <= y) for each y in actuals
        predictive_samples = np.asarray(predictive_samples, dtype=float)
        if predictive_samples.ndim != 1:
            raise DataValidationError("predictive_samples must be a 1D array.")

        n_samples = predictive_samples.size
        # Sort samples for efficient CDF estimation
        sorted_samples = np.sort(predictive_samples)

        # Calculate empirical CDF: count how many samples <= y
        # Using searchsorted is efficient for sorted arrays
        # side='right' gives count of elements <= value (since indices are 0-based)
        counts = np.searchsorted(sorted_samples, actuals, side='right')
        pit_values = counts / n_samples

    else:
        raise DataValidationError("Either predictive_cdf or predictive_samples must be provided.")

    # Clamp values to [0, 1] to handle floating point errors
    pit_values = np.clip(pit_values, 0.0, 1.0)

    # Handle exact 0 or 1 if necessary for log-likelihoods later,
    # but for uniformity testing, strict boundaries are often kept as is
    # or smoothed. Here we keep them as calculated.
    logger.debug(f"Calculated {len(pit_values)} PIT values. Range: [{pit_values.min():.4f}, {pit_values.max():.4f}]")

    return pit_values


def generate_pit_histogram(
    pit_values: np.ndarray,
    bins: int = 20
) -> Tuple[np.ndarray, np.ndarray, Dict[str, Any]]:
    """
    Generate histogram data for PIT values to assess uniformity visually.

    Args:
        pit_values: Array of PIT values.
        bins: Number of bins for the histogram.

    Returns:
        Tuple of (bin_edges, counts, stats_dict).
        stats_dict contains 'mean', 'variance', 'expected_mean', 'expected_variance'.
    """
    if pit_values.size == 0:
        raise DataValidationError("PIT values array is empty.")

    counts, bin_edges = np.histogram(pit_values, bins=bins, range=(0, 1))
    bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2

    # Expected uniform distribution statistics
    n = len(pit_values)
    expected_count = n / bins
    expected_mean = 0.5
    expected_variance = 1.0 / 12.0  # Variance of Uniform(0,1)

    pit_mean = np.mean(pit_values)
    pit_var = np.var(pit_values)

    stats_dict = {
        "mean": float(pit_mean),
        "variance": float(pit_var),
        "expected_mean": expected_mean,
        "expected_variance": expected_variance,
        "n_bins": bins,
        "counts": counts.tolist(),
        "bin_edges": bin_edges.tolist()
    }

    logger.debug(f"PIT Histogram generated: Mean={pit_mean:.4f}, Var={pit_var:.4f}")

    return bin_edges, counts, stats_dict


def ljung_box_test(pit_values: np.ndarray, lags: Optional[int] = None) -> Dict[str, float]:
    """
    Perform the Ljung-Box test on PIT values to test for uniformity (independence).

    Under the null hypothesis, PIT values should be i.i.d. Uniform(0,1).
    The Ljung-Box test checks for autocorrelation in the PIT sequence.
    Significant autocorrelation suggests the forecast distribution is misspecified
    or poorly calibrated over time.

    Note: We use Ljung-Box instead of KS-test as per FR-004 to account for
    time-series dependencies.

    Args:
        pit_values: Array of PIT values.
        lags: Number of lags to test. If None, defaults to int(10 * log10(n)).

    Returns:
        Dict with 'statistic' and 'p_value'.
    """
    if pit_values.size == 0:
        raise DataValidationError("PIT values array is empty.")

    # Convert to float64 for scipy
    pit_values = np.asarray(pit_values, dtype=np.float64)

    # Determine lags if not provided
    n = len(pit_values)
    if lags is None:
        lags = max(1, int(10 * np.log10(n)))

    # The Ljung-Box test in statsmodels/scipy usually tests for zero autocorrelation.
    # For uniformity, we ideally want to test if the sequence is i.i.d. Uniform(0,1).
    # A common approach is to test the PIT values directly for autocorrelation.
    # If PITs are uniform and independent, autocorrelations should be near zero.

    # Using scipy.stats.ljungbox (available in newer versions) or statsmodels
    # Since the environment has statsmodels (via requirements), we prefer that for robustness.
    try:
        from statsmodels.stats.diagnostic import acorr_ljungbox
        
        # acorr_ljungbox returns a DataFrame
        result = acorr_ljungbox(pit_values, lags=[lags], return_df=True)
        
        # The statistic and p-value for the specified lag
        # The result index is the lag number
        lb_stat = result.loc[lags, 'lb_stat']
        lb_pvalue = result.loc[lags, 'lb_pvalue']
        
    except ImportError:
        # Fallback to manual calculation if statsmodels is not fully available
        # Ljung-Box Statistic: Q = n(n+2) * sum(rho_k^2 / (n-k))
        mean_pit = np.mean(pit_values)
        # Center the series
        x = pit_values - mean_pit
        
        rho_squares = []
        for k in range(1, lags + 1):
            if k >= n:
                break
            # Autocorrelation at lag k
            numerator = np.sum(x[k:] * x[:-k])
            denominator = np.sum(x * x)
            if denominator == 0:
                rho_k = 0.0
            else:
                rho_k = numerator / denominator
            rho_squares.append(rho_k ** 2 / (n - k))
        
        if not rho_squares:
            lb_stat = 0.0
            lb_pvalue = 1.0
        else:
            lb_stat = n * (n + 2) * sum(rho_squares)
            # Approximate p-value using Chi-squared distribution with lags degrees of freedom
            lb_pvalue = 1.0 - stats.chi2.cdf(lb_stat, df=lags)

    logger.debug(f"Ljung-Box Test (lag={lags}): Statistic={lb_stat:.4f}, P-value={lb_pvalue:.4f}")

    return {
        "statistic": float(lb_stat),
        "p_value": float(lb_pvalue),
        "lags": lags,
        "n_observations": n
    }


def compute_pit_metrics(
    actuals: np.ndarray,
    predictive_samples: np.ndarray,
    bins: int = 20
) -> Dict[str, Any]:
    """
    Compute a comprehensive set of PIT metrics for a single forecast series.

    Args:
        actuals: Ground truth values.
        predictive_samples: Samples from the predictive distribution (1D array).
        bins: Number of bins for histogram.

    Returns:
        Dictionary containing:
            - pit_values: Array of calculated PITs.
            - histogram: Dict with bin data and stats.
            - ljung_box: Dict with test results.
            - summary: Dict with key metrics (mean, var, p-value).
    """
    # 1. Calculate PIT values
    pit_values = calculate_pit(
        forecasts=None, 
        actuals=actuals, 
        predictive_samples=predictive_samples
    )

    # 2. Generate Histogram
    hist_edges, hist_counts, hist_stats = generate_pit_histogram(pit_values, bins=bins)

    # 3. Ljung-Box Test
    lb_results = ljung_box_test(pit_values)

    # 4. Assemble Summary
    summary = {
        "mean_pit": hist_stats["mean"],
        "var_pit": hist_stats["variance"],
        "expected_mean": hist_stats["expected_mean"],
        "expected_var": hist_stats["expected_variance"],
        "ljung_box_statistic": lb_results["statistic"],
        "ljung_box_p_value": lb_results["p_value"],
        "is_uniform_indistinguishable": lb_results["p_value"] > 0.05
    }

    return {
        "pit_values": pit_values,
        "histogram": {
            "edges": hist_edges,
            "counts": hist_counts,
            "stats": hist_stats
        },
        "ljung_box": lb_results,
        "summary": summary
    }