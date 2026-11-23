"""
T025: Baseline validity test for User Story 2.

Runs trials on synthetic H=0.5 data (approximate white noise) to verify that
the one-sample t-test rejection rate at alpha=0.05 is within the 95%
Clopper-Pearson confidence interval of 0.05.

This acts as a gate to ensure our hypothesis testing pipeline is correctly
calibrated before proceeding to analyze dependent data (H > 0.5).
"""
import pytest
import numpy as np
import json
from pathlib import Path
from typing import List, Dict, Any
import logging

# Import project utilities
from src.synthesis.generators import generate_synthetic_series
from src.analysis.hypothesis_tests import run_one_sample_ttest
from src.utils.config import set_seed, get_path

# Configure logging for this test
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants for the baseline test
ALPHA = 0.05
TARGET_H = 0.5
TRIALS = 1000  # Sufficient for stable rejection rate estimation
SERIES_LENGTH = 1000  # N=1000 as per grid, sufficient for asymptotic properties
SEED = 42

def compute_clopper_pearson_interval(k: int, n: int, alpha: float = 0.05) -> tuple:
    """
    Compute the Clopper-Pearson (exact) binomial confidence interval.
    
    Args:
        k: Number of successes (rejections)
        n: Total number of trials
        alpha: Significance level (0.05 for 95% CI)
        
    Returns:
        tuple: (lower_bound, upper_bound)
    """
    from scipy.stats import beta
    
    if k == 0:
        lower = 0.0
    else:
        lower = beta.ppf(alpha / 2, k, n - k + 1)
        
    if k == n:
        upper = 1.0
    else:
        upper = beta.ppf(1 - alpha / 2, k + 1, n - k)
        
    return lower, upper

def run_baseline_trials() -> Dict[str, Any]:
    """
    Execute the baseline validity test.
    
    Generates TRIALS of synthetic H=0.5 series, runs a one-sample t-test
    (mean=0) on each, and calculates the rejection rate.
    
    Returns:
        Dict containing results, rejection rate, CI bounds, and status.
    """
    set_seed(SEED)
    rejections = 0
    p_values = []
    
    logger.info(f"Starting baseline validity test: {TRIALS} trials, H={TARGET_H}, N={SERIES_LENGTH}")
    
    for i in range(TRIALS):
        # Generate synthetic H=0.5 data (approximate white noise)
        # Note: generate_synthetic_series expects Hurst parameter
        data = generate_synthetic_series(
            hurst=TARGET_H,
            length=SERIES_LENGTH,
            seed=SEED + i  # Vary seed per trial
        )
        
        # Run one-sample t-test against mean=0
        # The function returns (statistic, p_value)
        try:
            stat, p_val = run_one_sample_ttest(data, mu=0)
            p_values.append(p_val)
            
            if p_val < ALPHA:
                rejections += 1
        except Exception as e:
            logger.warning(f"Trial {i} failed: {e}")
            # Count as non-rejection to be conservative, or fail loudly?
            # Given the "fail loudly" constraint, we should probably let this crash
            # if it happens frequently, but for a single outlier, we log and continue.
            # However, for a robust test, if the test itself fails, the pipeline is broken.
            # Let's raise if it happens more than 1% of the time.
            raise RuntimeError(f"Critical: Hypothesis test failed unexpectedly: {e}") from e

    rejection_rate = rejections / TRIALS
    lower_ci, upper_ci = compute_clopper_pearson_interval(rejections, TRIALS, ALPHA)
    
    logger.info(f"Rejections: {rejections}/{TRIALS} ({rejection_rate:.4f})")
    logger.info(f"95% Clopper-Pearson CI: [{lower_ci:.4f}, {upper_ci:.4f}]")
    
    # Check if the observed rate is within the expected CI for alpha=0.05
    # Ideally, the true rate should be close to 0.05.
    # We check if 0.05 falls within the CI of the observed rate? 
    # Or if the observed rate falls within the CI of 0.05?
    # The task says: "verify rejection rate is within 95% Clopper-Pearson CI of 0.05"
    # This usually means: Calculate the CI for the observed proportion. 
    # If the interval contains 0.05, we pass. 
    # Alternatively, calculate the CI for p=0.05 with n=TRIALS and see if observed k is in it.
    # Standard interpretation: The observed rate should be statistically consistent with 0.05.
    # So we check if 0.05 is inside [lower_ci, upper_ci].
    
    is_valid = lower_ci <= ALPHA <= upper_ci
    status = "PASS" if is_valid else "FAIL"
    
    return {
        "trials": TRIALS,
        "rejections": rejections,
        "rejection_rate": rejection_rate,
        "alpha": ALPHA,
        "ci_lower": lower_ci,
        "ci_upper": upper_ci,
        "status": status,
        "h_value": TARGET_H,
        "series_length": SERIES_LENGTH
    }

def test_baseline_validity():
    """
    Pytest entry point for the baseline validity test.
    
    Runs the trials and asserts that the rejection rate is within the
    expected confidence interval.
    """
    results = run_baseline_trials()
    
    # Save results to file for downstream tasks (T029 gate)
    output_path = get_path("results") / "baseline_status.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Results saved to {output_path}")
    
    # Assert the status is PASS
    assert results["status"] == "PASS", (
        f"Baseline validity test FAILED. "
        f"Observed rejection rate: {results['rejection_rate']:.4f}, "
        f"95% CI: [{results['ci_lower']:.4f}, {results['ci_upper']:.4f}]. "
        f"Expected rate 0.05 to be within CI."
    )

if __name__ == "__main__":
    test_baseline_validity()
    print("Baseline validity test completed successfully.")