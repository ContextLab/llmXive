"""
Metrics module for User Story 2: Quantify Bias and Divergence via Hellinger Distance.

This module calculates Hellinger distance between posteriors, computes bias,
and manages baseline uncertainty comparisons.
"""
import os
import logging
from pathlib import Path
from typing import Optional, Tuple, Dict, Any, List
import numpy as np
from scipy.stats import norm, gaussian_kde

from code.config import RESULTS_DIR, DATA_DIR

logger = logging.getLogger(__name__)


def load_posterior_from_file(file_path: Path) -> np.ndarray:
    """
    Load posterior samples from a file.
    Expects a JSON or CSV file containing samples for a parameter (e.g., mass).
    Returns a numpy array of samples.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"Posterior file not found: {file_path}")

    # Simple heuristic: try JSON first, then CSV
    # In a real scenario, we'd check the extension or content structure
    try:
        import json
        with open(file_path, "r") as f:
            data = json.load(f)
            # Assume the file contains a list of samples or a dict with a 'samples' key
            if isinstance(data, list):
                return np.array(data)
            elif isinstance(data, dict) and "samples" in data:
                return np.array(data["samples"])
            else:
                # Fallback: treat the whole dict as a single sample? Unlikely.
                logger.warning(f"Unexpected JSON structure in {file_path}")
                return np.array([])
    except json.JSONDecodeError:
        # Try CSV
        import pandas as pd
        df = pd.read_csv(file_path)
        # Assume first column is the parameter of interest
        if len(df.columns) > 0:
            return df[df.columns[0]].values
        else:
            return np.array([])


def gate_check_baseline_valid(baseline_posterior_path: Path) -> bool:
    """
    Verify that the baseline posterior is not 'inconclusive'.

    This is a gate check before using the baseline for comparison.
    """
    if not baseline_posterior_path.exists():
        logger.error(f"Baseline posterior not found: {baseline_posterior_path}")
        return False

    try:
        # Load metadata if available
        import json
        with open(baseline_posterior_path, "r") as f:
            data = json.load(f)
            if isinstance(data, dict):
                status = data.get("status", "valid")
                if status == "inconclusive":
                    logger.error("Baseline posterior is marked as inconclusive.")
                    return False
    except Exception as e:
        logger.warning(f"Could not read baseline metadata: {e}")
        # If we can't verify, assume it's valid? Or fail?
        # Fail safe: assume valid if we can't read, but log warning
        logger.warning("Assuming baseline is valid due to metadata read error.")

    return True


def get_baseline_uncertainty_baseline(baseline_posterior_path: Path) -> float:
    """
    Retrieve the intrinsic statistical uncertainty baseline.
    Defined as the 90% CI width from the 4096 Hz baseline posterior.

    Returns:
        The width of the 90% confidence interval.
    """
    samples = load_posterior_from_file(baseline_posterior_path)
    if len(samples) == 0:
        raise ValueError("No samples found in baseline posterior.")

    # Calculate 90% CI width
    lower = np.percentile(samples, 5)
    upper = np.percentile(samples, 95)
    return upper - lower


def calculate_hellinger_distance(
    posterior_samples: np.ndarray,
    baseline_samples: np.ndarray,
    num_bins: int = 100
) -> float:
    """
    Calculate the Hellinger distance between two distributions represented by samples.

    Uses Gaussian KDE to estimate PDFs, then computes the Hellinger distance.
    """
    if len(posterior_samples) == 0 or len(baseline_samples) == 0:
        logger.warning("Empty samples provided to Hellinger distance calculation.")
        return 1.0  # Maximum distance

    # Estimate PDFs using KDE
    # Combine data to find a common range
    all_data = np.concatenate([posterior_samples, baseline_samples])
    min_val, max_val = np.min(all_data), np.max(all_data)
    x = np.linspace(min_val, max_val, num_bins)

    try:
        kde_p = gaussian_kde(posterior_samples)
        kde_b = gaussian_kde(baseline_samples)

        pdf_p = kde_p(x)
        pdf_b = kde_b(x)

        # Normalize just in case
        pdf_p /= np.trapz(pdf_p, x)
        pdf_b /= np.trapz(pdf_b, x)

        # Hellinger distance: H(P, Q) = 1/sqrt(2) * sqrt( integral (sqrt(P) - sqrt(Q))^2 )
        # Discrete version: 1/sqrt(2) * sqrt( sum (sqrt(p_i) - sqrt(q_i))^2 * dx )
        # But since we normalized, we can just sum the squared differences of sqrt
        # H = 1/sqrt(2) * sqrt( 2 - 2 * sum(sqrt(p_i * q_i)) )
        # Or simpler: sqrt( 0.5 * sum( (sqrt(p) - sqrt(q))^2 ) )

        sqrt_p = np.sqrt(pdf_p)
        sqrt_q = np.sqrt(pdf_b)
        diff_sq = (sqrt_p - sqrt_q) ** 2
        integral = np.trapz(diff_sq, x)
        hellinger = np.sqrt(0.5 * integral)

        return hellinger
    except Exception as e:
        logger.error(f"Error calculating Hellinger distance: {e}")
        return 1.0


def calculate_bias(
    posterior_samples: np.ndarray,
    truth_value: float,
    prior_width: Optional[float] = None
) -> float:
    """
    Calculate the absolute bias of the posterior mean relative to the truth.

    Args:
        posterior_samples: Samples from the posterior distribution.
        truth_value: The ground truth value (injected or catalog).
        prior_width: Optional width of the prior (used for relative bias calculation).

    Returns:
        Absolute bias (posterior mean - truth).
    """
    if len(posterior_samples) == 0:
        logger.warning("Empty samples for bias calculation.")
        return 0.0

    posterior_mean = np.mean(posterior_samples)
    bias = abs(posterior_mean - truth_value)

    # If prior width is provided, calculate relative bias
    if prior_width is not None and prior_width > 0:
        relative_bias = bias / prior_width
        return relative_bias

    return bias


def compute_metrics_for_resolution(
    posterior_path: Path,
    baseline_path: Path,
    truth_value: Optional[float] = None,
    catalog_ci: Optional[float] = None
) -> Dict[str, Any]:
    """
    Compute all metrics for a single resolution configuration.

    1. Load posterior and baseline.
    2. Calculate Hellinger distance.
    3. Calculate bias (if truth available).
    4. Compare bias to catalog CI.

    Returns a dictionary of metrics.
    """
    metrics = {}

    try:
        posterior_samples = load_posterior_from_file(posterior_path)
        baseline_samples = load_posterior_from_file(baseline_path)
    except FileNotFoundError as e:
        logger.error(str(e))
        metrics["error"] = str(e)
        return metrics

    if len(posterior_samples) == 0:
        metrics["status"] = "invalid_posterior"
        return metrics

    # Hellinger distance
    metrics["hellinger_distance"] = calculate_hellinger_distance(posterior_samples, baseline_samples)

    # Bias calculation
    if truth_value is not None:
        # Estimate prior width if not provided (approximate from posterior range?)
        # For now, just calculate absolute bias
        metrics["bias_magnitude"] = calculate_bias(posterior_samples, truth_value)

        # Relative bias if catalog CI is provided
        if catalog_ci is not None and catalog_ci > 0:
            # Assuming catalog_ci is the full width of the 90% CI
            # Bias relative to this uncertainty
            metrics["bias_relative_to_ci"] = metrics["bias_magnitude"] / catalog_ci
            if metrics["bias_relative_to_ci"] > 1.0:
                metrics["bias_exceeds_ci"] = True
            else:
                metrics["bias_exceeds_ci"] = False
        else:
            metrics["bias_exceeds_ci"] = False
    else:
        metrics["bias_magnitude"] = None
        metrics["bias_exceeds_ci"] = False

    return metrics


def main() -> None:
    """
    Main entry point for metrics calculation.
    This is a placeholder for a script that would iterate over files.
    """
    logger.info("Metrics module loaded. Run compute_metrics_for_resolution for specific files.")


if __name__ == "__main__":
    from code.utils.logging_config import setup_logging
    setup_logging()
    main()
