"""
Hypothesis Testing Module for Robustness Evaluation (US3).

Implements one-sample t-tests and F-tests to evaluate statistical robustness
under non-independence. Explicitly excludes two-sample t-tests as per requirements.
"""
import numpy as np
import pandas as pd
from scipy import stats
from typing import Dict, Any, List, Optional, Tuple, Union
import logging

from src.utils.config import get_path, set_seed

logger = logging.getLogger(__name__)


def one_sample_ttest(
    series: Union[np.ndarray, pd.Series, List[float]],
    mu: float = 0.0,
    alternative: str = "two-sided"
) -> Dict[str, float]:
    """
    Perform a one-sample t-test on a time series against a hypothesized mean.

    This function tests the null hypothesis that the mean of the data is equal
    to a specified value (mu). It assumes the data is a single sample.

    Parameters
    ----------
    series : array-like
        The time series data to test.
    mu : float, default 0.0
        The hypothesized population mean.
    alternative : str, default "two-sided"
        Defines the alternative hypothesis. Must be one of:
        "two-sided" (mean != mu), "greater" (mean > mu), "less" (mean < mu).

    Returns
    -------
    dict
        A dictionary containing:
        - 'statistic': The t-statistic.
        - 'pvalue': The p-value of the test.
        - 'df': Degrees of freedom.
        - 'mean': The sample mean.
        - 'n': Sample size.

    Raises
    ------
    ValueError
        If the series has fewer than 2 observations or if alternative is invalid.
    """
    # Convert input to numpy array
    data = np.asarray(series)

    # Validation
    n = len(data)
    if n < 2:
        raise ValueError(f"Series must have at least 2 observations. Got {n}.")

    # Handle NaNs
    if np.any(np.isnan(data)):
        logger.warning("NaN values detected in series. Dropping them.")
        data = data[~np.isnan(data)]
        n = len(data)
        if n < 2:
            raise ValueError("Series has fewer than 2 non-NaN observations after cleaning.")

    # Perform t-test
    try:
        result = stats.ttest_1samp(data, popmean=mu, alternative=alternative)
    except Exception as e:
        logger.error(f"t-test failed: {e}")
        raise

    return {
        "statistic": float(result.statistic),
        "pvalue": float(result.pvalue),
        "df": float(result.df),
        "mean": float(np.mean(data)),
        "n": n
    }


def variance_ratio_ftest(
    series: Union[np.ndarray, pd.Series, List[float]],
    mu_variance: float = 1.0
) -> Dict[str, float]:
    """
    Perform an F-test for variance against a hypothesized variance.

    This function tests the null hypothesis that the variance of the data is
    equal to a specified value (mu_variance). It uses the Chi-square distribution
    for a single sample variance test (often referred to as a one-sample F-test
    in the context of comparing to a fixed value, though technically a Chi-square test).
    However, to strictly follow the "F-test" nomenclature often used in robustness
    contexts (comparing two variances), we interpret this as comparing the observed
    variance to a theoretical variance.

    Note: Strictly speaking, a single-sample variance test uses the Chi-square statistic:
    chi2 = (n-1) * s^2 / sigma0^2.
    We will return the p-value derived from this distribution.

    Parameters
    ----------
    series : array-like
        The time series data to test.
    mu_variance : float, default 1.0
        The hypothesized population variance.

    Returns
    -------
    dict
        A dictionary containing:
        - 'statistic': The Chi-square statistic (often interpreted in F-test context).
        - 'pvalue': The two-sided p-value.
        - 'df': Degrees of freedom (n-1).
        - 'variance': The sample variance.
        - 'n': Sample size.

    Raises
    ------
    ValueError
        If the series has fewer than 2 observations.
    """
    data = np.asarray(series)

    # Validation
    n = len(data)
    if n < 2:
        raise ValueError(f"Series must have at least 2 observations. Got {n}.")

    if np.any(np.isnan(data)):
        logger.warning("NaN values detected in series. Dropping them.")
        data = data[~np.isnan(data)]
        n = len(data)
        if n < 2:
            raise ValueError("Series has fewer than 2 non-NaN observations after cleaning.")

    sample_var = np.var(data, ddof=1)

    if mu_variance <= 0:
        raise ValueError("Hypothesized variance must be positive.")

    # Chi-square statistic for single variance
    # H0: sigma^2 = sigma0^2
    # stat = (n-1) * s^2 / sigma0^2
    stat = (n - 1) * sample_var / mu_variance

    # Two-sided p-value using Chi-square distribution
    # P(Chi2 > stat) + P(Chi2 < stat) depending on where stat falls
    # scipy.stats.chi2.sf gives P(X > x)
    p_upper = stats.chi2.sf(stat, df=n - 1)
    p_lower = stats.chi2.cdf(stat, df=n - 1)

    # Two-sided p-value: 2 * min(p_upper, p_lower)
    p_value = 2 * min(p_upper, p_lower)

    return {
        "statistic": float(stat),
        "pvalue": float(p_value),
        "df": float(n - 1),
        "variance": float(sample_var),
        "n": n
    }


def run_hypothesis_test_suite(
    series: Union[np.ndarray, pd.Series, List[float]],
    mu: float = 0.0,
    mu_variance: float = 1.0,
    alpha: float = 0.05
) -> Dict[str, Any]:
    """
    Run a suite of hypothesis tests on a single series.

    This function applies both the one-sample t-test (for mean) and the
    variance test (F-test/Chi-square) to a given series. It returns the
    results and a summary of whether the null hypothesis was rejected.

    Parameters
    ----------
    series : array-like
        The time series data to test.
    mu : float, default 0.0
        Hypothesized mean for t-test.
    mu_variance : float, default 1.0
        Hypothesized variance for variance test.
    alpha : float, default 0.05
        Significance level.

    Returns
    -------
    dict
        A dictionary containing results for both tests and a summary.
    """
    t_results = one_sample_ttest(series, mu=mu)
    var_results = variance_ratio_ftest(series, mu_variance=mu_variance)

    t_rejected = t_results["pvalue"] < alpha
    var_rejected = var_results["pvalue"] < alpha

    return {
        "t_test": t_results,
        "variance_test": var_results,
        "summary": {
            "t_rejected": t_rejected,
            "variance_rejected": var_rejected,
            "alpha": alpha
        }
    }


def batch_test_series(
    series_dict: Dict[str, Union[np.ndarray, pd.Series, List[float]]],
    mu: float = 0.0,
    mu_variance: float = 1.0,
    alpha: float = 0.05
) -> Dict[str, Dict[str, Any]]:
    """
    Run hypothesis tests on multiple series.

    Parameters
    ----------
    series_dict : dict
        Dictionary mapping series names to data arrays.
    mu : float
        Hypothesized mean.
    mu_variance : float
        Hypothesized variance.
    alpha : float
        Significance level.

    Returns
    -------
    dict
        Dictionary of results keyed by series name.
    """
    results = {}
    for name, data in series_dict.items():
        try:
            results[name] = run_hypothesis_test_suite(
                data, mu=mu, mu_variance=mu_variance, alpha=alpha
            )
        except Exception as e:
            logger.error(f"Failed to test series '{name}': {e}")
            results[name] = {
                "error": str(e),
                "t_test": None,
                "variance_test": None,
                "summary": None
            }
    return results


def main():
    """
    Main entry point for demonstration/testing of hypothesis tests.
    Runs tests on a synthetic white noise series and a persistent series
    to demonstrate functionality.
    """
    set_seed(42)
    n = 1000

    # Create test data
    white_noise = np.random.normal(loc=0.0, scale=1.0, size=n)
    # Persistent series (AR(1) with phi=0.7)
    persistent = np.zeros(n)
    for i in range(1, n):
        persistent[i] = 0.7 * persistent[i-1] + np.random.normal(0, 1)

    test_data = {
        "white_noise": white_noise,
        "persistent": persistent
    }

    print("Running Hypothesis Test Suite...")
    results = batch_test_series(test_data, mu=0.0, mu_variance=1.0, alpha=0.05)

    for name, res in results.items():
        if "error" in res:
            print(f"\n{name}: ERROR - {res['error']}")
        else:
            print(f"\n{name}:")
            print(f"  T-Test: stat={res['t_test']['statistic']:.4f}, p={res['t_test']['pvalue']:.4f} (Reject: {res['summary']['t_rejected']})")
            print(f"  Var-Test: stat={res['variance_test']['statistic']:.4f}, p={res['variance_test']['pvalue']:.4f} (Reject: {res['summary']['variance_rejected']})")

    return results


if __name__ == "__main__":
    main()