"""
Hypothesis testing module for evaluating statistical robustness.

This module implements one-sample t-tests and F-tests for synthetic series.

CRITICAL EXCLUSION NOTE:
========================
The two-sample t-test is EXPLICITLY EXCLUDED from this implementation per
Spec FR-004.

Reason for Exclusion:
---------------------
The two-sample t-test assumes that observations within each sample are
independent and identically distributed (i.i.d.). However, the data processed
by this pipeline (specifically detrended residuals) often exhibit long-range
dependence (LRD) or fractional Gaussian noise (fGn) characteristics.

When long-range dependence is present:
1. The effective sample size (N_eff) is significantly lower than the nominal
   sample size (N).
2. The standard error estimates used in the t-test statistic are biased
   downwards (underestimated).
3. This leads to inflated Type I error rates (false positives), causing the
   test to reject the null hypothesis far more often than the nominal alpha
   level (e.g., 0.05).

Consequently, applying a two-sample t-test to detrended residuals with LRD
would yield invalid statistical inferences. This implementation strictly
adheres to one-sample tests (testing against a known mean of 0) and F-tests
for variance, which are the focus of this robustness study.

Attempting to import or use a two-sample t-test function from this module
will result in an AttributeError or a NotImplementedError.
"""

import logging
import numpy as np
import pandas as pd
from scipy import stats
from typing import Dict, Any, List, Optional, Tuple, Union

from src.utils.logging import log_info, log_warning, log_error, log_critical

# Setup logger
logger = logging.getLogger(__name__)

# Log the exclusion rationale at module load time for immediate visibility
log_info(
    "Hypothesis Testing Module Loaded",
    extra={
        "component": "hypothesis_tests",
        "action": "exclusion_notice",
        "message": "Two-sample t-test is EXCLUDED per Spec FR-004 due to invalidity on detrended residuals with long-range dependence."
    }
)

class HypothesisTestError(Exception):
    """Custom exception for hypothesis testing errors."""
    pass


def run_one_sample_ttest(
    data: Union[np.ndarray, pd.Series],
    mu: float = 0.0,
    alpha: float = 0.05
) -> Dict[str, Any]:
    """
    Perform a one-sample t-test on the provided data.

    Tests the null hypothesis that the mean of the data is equal to `mu`.

    Args:
        data: The data series to test.
        mu: The hypothesized mean (default 0.0).
        alpha: The significance level.

    Returns:
        A dictionary containing the test statistic, p-value, and rejection decision.

    Raises:
        HypothesisTestError: If data is invalid or test cannot be performed.
    """
    if not isinstance(data, (np.ndarray, pd.Series)):
        raise HypothesisTestError("Data must be a numpy array or pandas Series.")

    if len(data) < 2:
        raise HypothesisTestError("Data must have at least 2 points for t-test.")

    # Perform t-test
    try:
        t_stat, p_value = stats.ttest_1samp(data, popmean=mu)
    except Exception as e:
        raise HypothesisTestError(f"t-test failed: {str(e)}")

    rejected = p_value < alpha

    return {
        "test_type": "one_sample_ttest",
        "statistic": float(t_stat),
        "p_value": float(p_value),
        "alpha": alpha,
        "rejected_null": bool(rejected),
        "mu_hypothesized": mu,
        "sample_mean": float(np.mean(data)),
        "sample_size": len(data)
    }


def run_f_test_variance(
    data: Union[np.ndarray, pd.Series],
    sigma0_squared: float = 1.0,
    alpha: float = 0.05
) -> Dict[str, Any]:
    """
    Perform an F-test for variance.

    Tests the null hypothesis that the variance of the data is equal to `sigma0_squared`.
    This is a two-tailed test.

    Args:
        data: The data series to test.
        sigma0_squared: The hypothesized variance.
        alpha: The significance level.

    Returns:
        A dictionary containing the test statistic, p-value, and rejection decision.

    Raises:
        HypothesisTestError: If data is invalid or test cannot be performed.
    """
    if not isinstance(data, (np.ndarray, pd.Series)):
        raise HypothesisTestError("Data must be a numpy array or pandas Series.")

    if len(data) < 2:
        raise HypothesisTestError("Data must have at least 2 points for F-test.")

    if sigma0_squared <= 0:
        raise HypothesisTestError("Hypothesized variance must be positive.")

    sample_variance = np.var(data, ddof=1)
    n = len(data)

    # F-statistic: (n-1) * s^2 / sigma0^2
    f_stat = (n - 1) * sample_variance / sigma0_squared

    # Two-tailed p-value
    # P(F < f_stat) and P(F > f_stat)
    p_lower = stats.f.cdf(f_stat, n - 1, np.inf) # df2 -> inf for variance test against constant
    # Actually, for testing variance against a constant, we use Chi-squared distribution
    # F-test is typically for comparing two variances.
    # However, scipy.stats.chisquare or manual calculation for variance test:
    # Statistic: (n-1)*s^2 / sigma0^2 ~ Chi^2(n-1)
    
    # Let's use Chi-squared for single variance test as it's more direct
    # But the task description says "F-tests". In the context of single sample variance,
    # it is often colloquially referred to, but mathematically it's Chi-squared.
    # If the requirement strictly implies F-distribution usage (e.g. comparing to a baseline),
    # we might need two samples. Assuming single sample variance test against a constant.
    # Standard approach: Chi-squared test for variance.
    
    # Re-reading context: "one-sample t-tests and F-tests".
    # If it implies comparing variance of two groups, we need two samples.
    # If it implies testing variance against a theoretical value, it's Chi-squared.
    # Let's assume the standard "F-test for equality of two variances" is not applicable here
    # unless we have two groups.
    # However, sometimes "F-test" is used loosely.
    # Let's implement the Chi-squared test for single variance but label it appropriately
    # or implement the F-test if we assume a comparison to a reference variance (which is effectively Chi-squared).
    
    # Let's stick to the Chi-squared distribution for single variance testing as it is the exact test.
    # If the user insists on "F-test" name, we can note the equivalence.
    # But to be safe and accurate:
    
    chi2_stat = (n - 1) * sample_variance / sigma0_squared
    p_value = 2 * min(stats.chi2.cdf(chi2_stat, n - 1), 1 - stats.chi2.cdf(chi2_stat, n - 1))

    rejected = p_value < alpha

    return {
        "test_type": "variance_test_chi2",
        "statistic": float(chi2_stat),
        "p_value": float(p_value),
        "alpha": alpha,
        "rejected_null": bool(rejected),
        "hypothesized_variance": sigma0_squared,
        "sample_variance": float(sample_variance),
        "sample_size": n,
        "note": "Using Chi-squared distribution for single variance test against constant."
    }


def run_hypothesis_tests_for_series(
    data: Union[np.ndarray, pd.Series],
    test_types: List[str] = ["ttest", "variance_test"],
    mu: float = 0.0,
    sigma0_squared: float = 1.0,
    alpha: float = 0.05
) -> Dict[str, Any]:
    """
    Run a suite of hypothesis tests on a single series.

    Args:
        data: The data series.
        test_types: List of tests to run. Supported: "ttest", "variance_test".
        mu: Hypothesized mean for t-test.
        sigma0_squared: Hypothesized variance for variance test.
        alpha: Significance level.

    Returns:
        Dictionary of results for each test.
    """
    results = {}

    if "ttest" in test_types:
        try:
            results["ttest"] = run_one_sample_ttest(data, mu, alpha)
        except HypothesisTestError as e:
            log_warning(f"t-test failed for series: {str(e)}")
            results["ttest"] = {"error": str(e)}

    if "variance_test" in test_types:
        try:
            results["variance_test"] = run_f_test_variance(data, sigma0_squared, alpha)
        except HypothesisTestError as e:
            log_warning(f"Variance test failed for series: {str(e)}")
            results["variance_test"] = {"error": str(e)}

    return results


def main():
    """
    Entry point for running hypothesis tests.
    Currently acts as a demonstration of the exclusion logic and basic functionality.
    """
    log_info("Starting Hypothesis Tests Module")
    
    # Demonstrate the exclusion message
    log_warning(
        "Two-sample t-test is explicitly excluded per Spec FR-004.",
        extra={
            "reason": "Invalid for detrended residuals with long-range dependence.",
            "impact": "Prevents inflated Type I error rates."
        }
    )

    # Example usage with synthetic data (for demonstration only)
    # In a real run, this would load data from data/processed/
    np.random.seed(42)
    sample_data = np.random.normal(0, 1, 1000)
    
    results = run_hypothesis_tests_for_series(sample_data)
    log_info(f"Example test results: {results}")

    return results

if __name__ == "__main__":
    main()