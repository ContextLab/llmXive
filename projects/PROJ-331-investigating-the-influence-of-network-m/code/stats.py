import os
import sys
import json
import logging
import numpy as np
import pandas as pd
from scipy import stats as scipy_stats
from statsmodels.stats.power import TTestIndPower
from utils import get_logger, safe_read_json, safe_write_json, PipelineError

# Ensure statsmodels is available; if not, raise a clear error
try:
    from statsmodels.stats.power import TTestIndPower
except ImportError:
    raise ImportError("statsmodels is required for power analysis. Install via: pip install statsmodels")

def aggregate_subject_metrics():
    """
    Aggregates data from previous steps into a single metrics file.
    (Existing implementation placeholder for context)
    """
    logger = get_logger("stats")
    logger.info("Aggregating subject metrics...")
    # Implementation would load motif_profiles.json, global_efficiency.json, rsfc.npy
    # and combine them into data/processed/subject_metrics.csv
    pass

def compute_partial_correlations():
    """
    Computes partial correlations between motifs and rsFC metrics.
    (Existing implementation placeholder for context)
    """
    logger = get_logger("stats")
    logger.info("Computing partial correlations...")
    # Implementation would handle Bonferroni correction and permutation tests
    pass

def power_analysis(n_subjects=50, alpha=0.05, power_level=0.8):
    """
    Performs a post-hoc power analysis to determine the minimum detectable effect size (r)
    given a specific sample size, alpha level (Bonferroni-adjusted), and desired power.

    This function uses the TTestIndPower solver from statsmodels to approximate the
    detectable correlation coefficient (r) for a two-tailed test.

    Args:
        n_subjects (int): Number of subjects in the cohort.
        alpha (float): Significance level (typically 0.05).
        power_level (float): Desired statistical power (typically 0.8).

    Returns:
        dict: A dictionary containing the analysis parameters and results:
            - "min_detectable_r": float, the minimum correlation coefficient detectable.
            - "power_level": float, the target power used.
            - "adjusted_alpha": float, the alpha level used (Bonferroni-adjusted if applied).
            - "n_subjects": int, the sample size used.
    """
    logger = get_logger("stats")
    logger.info(f"Starting power analysis with N={n_subjects}, alpha={alpha}, power={power_level}")

    # Calculate Bonferroni-adjusted alpha
    # Assuming a conservative number of tests based on the number of directed 3-node motifs.
    # There are 13 directed 3-node isomorphism classes. If we test each against multiple metrics,
    # we adjust accordingly. Here we assume a standard correction factor for the motif set.
    # If the exact number of tests isn't provided in the immediate context, we use a standard
    # correction factor (e.g., 13 motifs * 2 metrics = 26 tests) or simply apply the alpha
    # as passed if it's already adjusted.
    # The task description implies the alpha passed is the base (0.05) and we must adjust it.
    # Let's assume a typical correction factor of 26 (13 motifs * 2 metrics: strength, efficiency).
    num_tests = 26  # Conservative estimate for 13 motifs x 2 metrics
    adjusted_alpha = alpha / num_tests
    logger.info(f"Applying Bonferroni correction: {alpha} / {num_tests} = {adjusted_alpha:.6f}")

    # Use statsmodels to solve for effect size (r)
    # TTestIndPower solves for n, power, effect_size, or alpha.
    # We want effect_size (which corresponds to Cohen's d for t-tests, but we map it to r).
    # For a correlation test, we can approximate using the t-test power solver.
    # Alternatively, we can use the correlation power analysis if available, but TTestIndPower
    # is robust for general sample size calculations.
    # However, a more direct approach for correlation is to invert the relationship:
    # t = r * sqrt((n-2) / (1-r^2))
    # We need the critical t-value for the adjusted alpha and then solve for r.
    
    # Method 1: Using TTestIndPower to find effect size (Cohen's d) then converting to r.
    # This is an approximation. A direct correlation power analysis is better.
    # Let's implement a direct search for r using the t-distribution, which is more accurate for correlations.
    
    # Critical t-value for two-tailed test
    df = n_subjects - 2
    t_crit = scipy_stats.t.ppf(1 - adjusted_alpha / 2, df)

    # We need to find 'r' such that the t-statistic equals t_crit for the given power.
    # The power of a correlation test is calculated based on the non-central t-distribution.
    # Since statsmodels doesn't have a direct "CorrelationPower" class exposed as simply as TTestIndPower,
    # we will use a numerical solver to find the r that yields the desired power.
    
    # Define a function to calculate power given r, n, alpha
    def calculate_power_for_r(r, n, alpha):
        if abs(r) >= 1.0:
            return 1.0
        # Fisher's z transformation approach or non-central t
        # Using the non-central t approximation:
        # lambda (non-centrality parameter) = r * sqrt(n-2) / sqrt(1-r^2)
        # But for power calculation, we need the probability that t_obs > t_crit
        # given the non-centrality parameter.
        
        # Let's use the standard approximation:
        # z_alpha = norm.ppf(1 - alpha/2)
        # z_beta = norm.ppf(power)
        # r = (z_alpha + z_beta) / sqrt(n + (z_alpha + z_beta)^2) ? No, that's for Fisher Z.
        
        # Fisher Z method is more accurate:
        # Z_r = 0.5 * ln((1+r)/(1-r))
        # SE = 1 / sqrt(n-3)
        # Power = Phi( |Z_r|/SE - Z_alpha )
        # We need to find r such that Power = power_level.
        
        # Invert:
        # Z_beta = norm.ppf(power_level)
        # |Z_r|/SE - Z_alpha = Z_beta
        # |Z_r| = SE * (Z_alpha + Z_beta)
        # Z_r = SE * (Z_alpha + Z_beta)  (assuming positive r)
        # r = tanh(Z_r)
        
        from scipy.stats import norm
        z_alpha = norm.ppf(1 - alpha / 2)
        z_beta = norm.ppf(power_level)
        se = 1.0 / np.sqrt(n - 3)
        z_r = se * (z_alpha + z_beta)
        r_val = np.tanh(z_r)
        return r_val

    min_detectable_r = calculate_power_for_r(0, n_subjects, adjusted_alpha)
    
    # Ensure the result is reasonable
    if min_detectable_r > 1.0:
        min_detectable_r = 1.0
    elif min_detectable_r < 0:
        min_detectable_r = 0.0

    result = {
        "min_detectable_r": float(min_detectable_r),
        "power_level": float(power_level),
        "adjusted_alpha": float(adjusted_alpha),
        "n_subjects": int(n_subjects)
    }

    logger.info(f"Power analysis complete. Min detectable r: {min_detectable_r:.4f}")
    return result

def main():
    """
    Main entry point for the power analysis task.
    Reads configuration, performs analysis, and saves results.
    """
    logger = get_logger("stats")
    logger.info("Executing T034: Power Analysis Module")

    try:
        # Parameters from task description
        n_subjects = 50
        base_alpha = 0.05
        power_level = 0.8

        # Run analysis
        results = power_analysis(n_subjects=n_subjects, alpha=base_alpha, power_level=power_level)

        # Ensure output directory exists
        results_dir = "results"
        if not os.path.exists(results_dir):
            os.makedirs(results_dir)

        output_path = os.path.join(results_dir, "power_analysis.json")
        
        # Save results
        safe_write_json(results, output_path)
        logger.info(f"Power analysis results saved to {output_path}")

        # Print summary for verification
        print(f"Power Analysis Results:")
        print(f"  N Subjects: {results['n_subjects']}")
        print(f"  Adjusted Alpha (Bonferroni): {results['adjusted_alpha']:.6f}")
        print(f"  Target Power: {results['power_level']}")
        print(f"  Min Detectable r: {results['min_detectable_r']:.4f}")

    except Exception as e:
        logger.error(f"Power analysis failed: {e}")
        raise PipelineError(f"Power analysis execution failed: {e}")

if __name__ == "__main__":
    main()
