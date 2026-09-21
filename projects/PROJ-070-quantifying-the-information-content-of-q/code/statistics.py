"""
Statistics module for correlation analysis and hypothesis testing.

Implements:
- Partial correlation controlling for system size
- Bootstrap resampling for confidence intervals
- Statistical comparisons (Welch's t-test) for null model validation
"""
import numpy as np
from scipy import stats
from logging_config import logger

def calculate_correlation(x, y):
    """Calculate Pearson correlation coefficient and p-value."""
    if len(x) < 3 or len(y) < 3:
        logger.warning("Insufficient data for correlation calculation.")
        return 0.0, 1.0
    r, p_value = stats.pearsonr(x, y)
    return r, p_value

def calculate_partial_correlation(x, y, z):
    """
    Calculate partial correlation between x and y, controlling for z (system size).
    """
    if len(x) < 4 or len(y) < 4 or len(z) < 4:
        logger.warning("Insufficient data for partial correlation.")
        return 0.0, 1.0
    
    # Use statsmodels or manual calculation via residuals
    # Manual: regress x on z, y on z, correlate residuals
    try:
        # Linear regression for x ~ z
        slope_x, intercept_x, r_value_x, p_value_x, std_err_x = stats.linregress(z, x)
        residuals_x = x - (slope_x * z + intercept_x)
        
        # Linear regression for y ~ z
        slope_y, intercept_y, r_value_y, p_value_y, std_err_y = stats.linregress(z, y)
        residuals_y = y - (slope_y * z + intercept_y)
        
        # Correlation of residuals
        r_partial, p_partial = stats.pearsonr(residuals_x, residuals_y)
        return r_partial, p_partial
    except Exception as e:
        logger.error(f"Error in partial correlation: {e}")
        return 0.0, 1.0

def bootstrap_correlation(x, y, n_iterations=1000, random_state=None):
    """
    Perform bootstrap resampling to estimate confidence intervals for correlation.
    Returns mean correlation and 95% CI.
    """
    if random_state is not None:
        np.random.seed(random_state)
    
    n = len(x)
    boot_corrs = []
    
    for _ in range(n_iterations):
        indices = np.random.choice(n, size=n, replace=True)
        x_boot = x[indices]
        y_boot = y[indices]
        r, _ = stats.pearsonr(x_boot, y_boot)
        boot_corrs.append(r)
    
    boot_corrs = np.array(boot_corrs)
    mean_r = np.mean(boot_corrs)
    lower, upper = np.percentile(boot_corrs, [2.5, 97.5])
    return mean_r, (lower, upper)

def calculate_confidence_intervals(data, confidence=0.95):
    """Calculate confidence intervals for a dataset."""
    n = len(data)
    if n < 2:
        return 0.0, 0.0
    mean = np.mean(data)
    std_err = stats.sem(data)
    h = std_err * stats.t.ppf((1 + confidence) / 2.0, n - 1)
    return mean - h, mean + h

def analyze_stratified_correlation(x, y, z):
    """
    Perform stratified analysis by system size bins.
    Returns list of (bin_range, correlation, p_value).
    """
    # Simple binning by quartiles of z
    bins = np.percentile(z, [25, 50, 75])
    unique_bins = np.unique(bins)
    if len(unique_bins) < 2:
        return []
    
    results = []
    for i in range(len(unique_bins) - 1):
        mask = (z >= bins[i]) & (z < bins[i+1])
        if np.sum(mask) > 2:
            r, p = calculate_correlation(x[mask], y[mask])
            results.append(((bins[i], bins[i+1]), r, p))
    return results

def run_welch_t_test(group1, group2):
    """
    Perform Welch's t-test (unequal variance t-test) between two groups.
    Returns t-statistic and p-value.
    """
    if len(group1) < 2 or len(group2) < 2:
        logger.warning("Insufficient data for t-test.")
        return 0.0, 1.0
    t_stat, p_val = stats.ttest_ind(group1, group2, equal_var=False)
    return t_stat, p_val

def run_full_correlation_analysis(entropies, complexities, sizes):
    """
    Run full correlation analysis pipeline:
    1. Partial correlation (controlling for size)
    2. Bootstrap CI
    3. Stratified analysis
    """
    partial_r, partial_p = calculate_partial_correlation(entropies, complexities, sizes)
    boot_mean, boot_ci = bootstrap_correlation(entropies, complexities)
    strat_results = analyze_stratified_correlation(entropies, complexities, sizes)
    
    return {
        "partial_correlation": partial_r,
        "partial_p_value": partial_p,
        "bootstrap_mean": boot_mean,
        "bootstrap_ci": boot_ci,
        "stratified_results": strat_results
    }

# Placeholder for T030/T031 integration if needed later
# Currently, run_welch_t_test is the critical addition for T022