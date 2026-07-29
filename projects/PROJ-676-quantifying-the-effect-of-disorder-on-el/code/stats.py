"""
Statistical analysis for localization length scaling.

Implements linear regression for log(xi) vs log(W) to extract the critical exponent
and verify the scaling hypothesis.
"""
import json
import logging
import os
import math
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import numpy as np
from scipy import stats as scipy_stats

from code.config import get_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def aggregate_localization_lengths(input_path: str) -> Dict[str, List[float]]:
    """
    Aggregate localization lengths (xi) from the scaling fits output.

    Args:
        input_path: Path to scaling_fits.json containing results from T013.

    Returns:
        Dictionary mapping disorder width (W) to list of localization lengths (xi).
    """
    config = get_config()
    input_file = Path(input_path)

    if not input_file.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    with open(input_file, 'r') as f:
        data = json.load(f)

    # Aggregate xi by W
    # Expected structure: list of dicts with 'W', 'xi', 'uncertainty', etc.
    xi_by_width: Dict[str, List[float]] = {}

    for entry in data:
        w = entry.get('W')
        xi = entry.get('xi')

        if w is None or xi is None:
            logger.warning(f"Skipping entry with missing W or xi: {entry}")
            continue

        w_key = f"{w:.2f}"
        if w_key not in xi_by_width:
            xi_by_width[w_key] = []
        xi_by_width[w_key].append(xi)

    logger.info(f"Aggregated {sum(len(v) for v in xi_by_width.values())} localization lengths across {len(xi_by_width)} widths.")
    return xi_by_width


def perform_linear_regression(
    x: np.ndarray,
    y: np.ndarray,
    y_err: Optional[np.ndarray] = None
) -> Dict[str, Any]:
    """
    Perform weighted linear regression of y vs x.

    Args:
        x: Independent variable (e.g., log(W)).
        y: Dependent variable (e.g., log(xi)).
        y_err: Optional uncertainties in y for weighted regression.

    Returns:
        Dictionary with slope, intercept, R-squared, and confidence intervals.
    """
    if len(x) == 0 or len(y) == 0:
        raise ValueError("Input arrays cannot be empty.")

    if len(x) != len(y):
        raise ValueError("x and y must have the same length.")

    # Filter out infinite or NaN values
    mask = np.isfinite(x) & np.isfinite(y)
    if y_err is not None:
        mask &= np.isfinite(y_err)
    x_clean = x[mask]
    y_clean = y[mask]
    y_err_clean = y_err[mask] if y_err is not None else None

    if len(x_clean) < 2:
        raise ValueError("Not enough valid data points for regression (need >= 2).")

    # Perform regression
    if y_err_clean is not None and np.any(y_err_clean > 0):
        # Weighted regression
        weights = 1.0 / (y_err_clean ** 2)
        # Use scipy.stats for weighted fit if possible, otherwise fall back to unweighted
        # scipy.stats.linregress doesn't support weights directly, so we use curve_fit logic or manual
        # For simplicity and robustness, we use numpy.polyfit with weights
        coeffs = np.polyfit(x_clean, y_clean, 1, w=np.sqrt(weights))
        slope, intercept = coeffs
        # Estimate uncertainty via covariance matrix from polyfit
        # np.polyfit returns covariance matrix if full=True (in newer numpy versions)
        # To be safe, we use the standard error from the residuals for confidence intervals
        y_pred = slope * x_clean + intercept
        residuals = y_clean - y_pred
        # Standard error of estimate
        s_err = np.sqrt(np.sum(residuals**2) / (len(x_clean) - 2))
        # Standard errors of slope and intercept
        # From polyfit documentation, cov is scaled by s_err^2 if full=True
        # We'll approximate confidence intervals using standard formulas
        x_mean = np.mean(x_clean)
        ss_xx = np.sum((x_clean - x_mean)**2)
        se_slope = s_err / np.sqrt(ss_xx)
        se_intercept = s_err * np.sqrt(1/len(x_clean) + x_mean**2 / ss_xx)
    else:
        # Unweighted regression
        slope, intercept, r_value, p_value, std_err = scipy_stats.linregress(x_clean, y_clean)
        se_slope = std_err
        # For intercept, we calculate similarly
        x_mean = np.mean(x_clean)
        ss_xx = np.sum((x_clean - x_mean)**2)
        s_err = np.sqrt(np.sum((y_clean - (slope*x_clean + intercept))**2) / (len(x_clean) - 2))
        se_intercept = s_err * np.sqrt(1/len(x_clean) + x_mean**2 / ss_xx)
        r_squared = r_value ** 2

    # Confidence intervals (95%)
    # Using t-distribution for small samples, but for large n, normal approx is fine
    # t-value for 95% CI with n-2 degrees of freedom
    n = len(x_clean)
    if n > 30:
        t_val = 1.96
    else:
        from scipy import stats
        t_val = stats.t.ppf(0.975, df=n-2)

    slope_ci = (slope - t_val * se_slope, slope + t_val * se_slope)
    intercept_ci = (intercept - t_val * se_intercept, intercept + t_val * se_intercept)

    # Calculate R-squared if not already done (for weighted case)
    if y_err_clean is None or np.all(y_err_clean == 0):
        # Re-calculate R-squared for unweighted
        y_pred = slope * x_clean + intercept
        ss_res = np.sum((y_clean - y_pred)**2)
        ss_tot = np.sum((y_clean - np.mean(y_clean))**2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0
    else:
        # For weighted, R-squared is less standard, but we can compute a pseudo-R2
        y_pred = slope * x_clean + intercept
        ss_res = np.sum(((y_clean - y_pred) * weights)**2)
        ss_tot = np.sum(((y_clean - np.mean(y_clean)) * weights)**2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0

    return {
        'slope': float(slope),
        'intercept': float(intercept),
        'r_squared': float(r_squared),
        'slope_se': float(se_slope),
        'intercept_se': float(se_intercept),
        'slope_95_ci': [float(slope_ci[0]), float(slope_ci[1])],
        'intercept_95_ci': [float(intercept_ci[0]), float(intercept_ci[1])],
        'n_points': int(n),
        'p_value': float(scipy_stats.linregress(x_clean, y_clean).pvalue)
    }


def compute_scaling_analysis(
    xi_by_width: Dict[str, List[float]]
) -> Dict[str, Any]:
    """
    Compute the scaling analysis: log(xi) vs log(W).

    Args:
        xi_by_width: Dictionary mapping W (string) to list of xi values.

    Returns:
        Dictionary with regression results, aggregated data, and metadata.
    """
    if not xi_by_width:
        raise ValueError("No data to analyze.")

    # Convert to numpy arrays
    # We use the mean xi for each width
    w_values = []
    xi_means = []
    xi_stds = []
    n_samples = []

    for w_str, xi_list in xi_by_width.items():
        w_val = float(w_str)
        xi_arr = np.array(xi_list)

        w_values.append(w_val)
        xi_means.append(np.mean(xi_arr))
        xi_stds.append(np.std(xi_arr))
        n_samples.append(len(xi_arr))

    w_values = np.array(w_values)
    xi_means = np.array(xi_means)
    xi_stds = np.array(xi_stds)

    # Filter out non-positive values for log
    valid_mask = (w_values > 0) & (xi_means > 0)
    if not np.any(valid_mask):
        raise ValueError("No valid data points (W>0 and xi>0) for log-log regression.")

    log_w = np.log(w_values[valid_mask])
    log_xi = np.log(xi_means[valid_mask])
    log_xi_err = xi_stds[valid_mask] / xi_means[valid_mask]  # Relative error approx for log

    # Perform regression
    regression_results = perform_linear_regression(log_w, log_xi, log_xi_err)

    # Prepare output
    analysis_results = {
        'regression': regression_results,
        'data_summary': {
            'w_values': w_values[valid_mask].tolist(),
            'xi_means': xi_means[valid_mask].tolist(),
            'xi_stds': xi_stds[valid_mask].tolist(),
            'n_samples': [n_samples[i] for i, v in enumerate(w_values) if valid_mask[v]]
        },
        'metadata': {
            'description': 'Linear regression of log(xi) vs log(W) for 1D Anderson localization',
            'expected_slope': -2.0,  # Theoretical expectation for 1D
            'units': 'log-log scale'
        }
    }

    return analysis_results


def save_scaling_results(results: Dict[str, Any], output_path: str) -> None:
    """
    Save scaling analysis results to JSON.

    Args:
        results: Dictionary containing analysis results.
        output_path: Path to output file.
    """
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)

    logger.info(f"Saved scaling results to {output_path}")


def main():
    """
    Main entry point for the stats analysis.
    Reads scaling_fits.json, performs regression, and saves results.
    """
    config = get_config()
    input_path = config.DATA_PROCESSED / "scaling_fits.json"
    output_path = config.DATA_PROCESSED / "scaling_regression.json"

    logger.info(f"Starting scaling analysis. Input: {input_path}, Output: {output_path}")

    try:
        # Aggregate data
        xi_by_width = aggregate_localization_lengths(str(input_path))

        # Compute analysis
        results = compute_scaling_analysis(xi_by_width)

        # Save results
        save_scaling_results(results, str(output_path))

        logger.info("Scaling analysis completed successfully.")
        print(json.dumps(results['regression'], indent=2))

    except FileNotFoundError as e:
        logger.error(f"Input file not found: {e}")
        raise
    except ValueError as e:
        logger.error(f"Data processing error: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise


if __name__ == "__main__":
    main()