"""
Task T015b: A priori Power Analysis for Disorder Effect Study.

Verifies that 100 realizations provide >= 80% power to detect a slope deviation
from -2 in the log(xi) vs log(W) relationship at alpha=0.05.

This implements Statistical Criterion SC-003.
"""
import json
import math
import os
from pathlib import Path
from typing import Dict, Any, Tuple

import numpy as np
from scipy import stats

# Import project config
from config import get_config


def estimate_effect_size() -> float:
    """
    Estimate the standardized effect size (Cohen's d) for the slope deviation.
    
    Based on literature (e.g., Abrahams et al., 1979; MacKinnon et al., 2002),
    the slope of log(xi) vs log(W) in the strong disorder regime is theoretically -2.
    We assume a meaningful deviation (delta) of 0.2 from -2 (i.e., detecting a slope of -1.8 or -2.2).
    
    The standard error of the slope in a linear regression is approximately:
    SE_beta = sigma_y / (sigma_x * sqrt(n_samples))
    
    We estimate sigma_y (residual std dev) based on typical variance in localization length
    measurements for 1D chains, and sigma_x based on the spread of log(W) values.
    
    Returns:
        float: Estimated Cohen's d (effect size) for the test.
    """
    # Hypothesized theoretical slope
    slope_null = -2.0
    
    # Minimum meaningful deviation we want to detect
    # A 10% change in the exponent is physically significant
    delta_slope = 0.2 
    
    # Estimate of residual standard deviation in log(xi)
    # Based on typical variance in localization length studies (sigma ~ 0.2-0.3 in log scale)
    sigma_residual = 0.25
    
    # Range of log(W) values used in the study
    # Assuming W ranges from 0.5 to 10.0
    log_w_min = math.log(0.5)
    log_w_max = math.log(10.0)
    # Approximate standard deviation of log(W) assuming uniform distribution
    sigma_x = (log_w_max - log_w_min) / math.sqrt(12)
    
    # Number of data points (disorder widths)
    # Typically 5-10 widths are used
    n_widths = 8
    
    # Standard error of the slope for n_widths points
    # SE = sigma_y / (sigma_x * sqrt(n_widths))
    se_slope = sigma_residual / (sigma_x * math.sqrt(n_widths))
    
    # Effect size (delta / SE)
    effect_size = delta_slope / se_slope
    
    return effect_size


def calculate_power(effect_size: float, n_realizations: int, alpha: float = 0.05) -> Tuple[float, Dict[str, Any]]:
    """
    Calculate statistical power for detecting the slope deviation.
    
    Uses the non-central t-distribution approximation for linear regression slope tests.
    
    Args:
        effect_size: Standardized effect size (Cohen's d)
        n_realizations: Number of disorder realizations per width
        alpha: Significance level
        
    Returns:
        Tuple of (power, details_dict)
    """
    # Degrees of freedom for the t-test (approximate)
    # df = N - 2 for simple linear regression, but here we have multiple widths
    # We approximate the effective sample size as n_widths * n_realizations
    # However, the slope is estimated across widths, so the effective n is closer to n_widths
    # But the variance of the slope estimate is reduced by n_realizations
    # We use the non-centrality parameter lambda = effect_size * sqrt(n_realizations)
    
    # For a t-test on the slope, the non-centrality parameter is:
    # lambda = (beta - beta_null) / SE_beta
    # Since we defined effect_size as delta / SE_slope (where SE includes sigma_residual/sqrt(n_widths)),
    # we need to adjust for the number of realizations.
    # Actually, the effect_size calculated above is for a single realization.
    # With n_realizations, the standard error of the mean log(xi) at each width decreases by sqrt(n_realizations).
    # Thus, the SE of the slope decreases by sqrt(n_realizations).
    # So the non-centrality parameter increases by sqrt(n_realizations).
    
    ncp = effect_size * math.sqrt(n_realizations)
    
    # Degrees of freedom: n_widths - 2 (for the regression across widths)
    # But the variance estimate comes from the residuals across all realizations.
    # A conservative estimate is df = n_widths * (n_realizations - 1) - 2
    # However, for power analysis of the slope, the critical df is often approximated as n_widths - 2
    # Let's use a more robust approximation: df = (n_widths - 2) * n_realizations
    # Actually, the standard error of the slope is based on the variance of the means at each width.
    # The degrees of freedom for the t-statistic is n_widths - 2.
    # The non-centrality parameter scales with sqrt(n_realizations).
    df = 8 - 2  # n_widths - 2
    
    # Critical t-value for two-tailed test
    t_crit = stats.t.ppf(1 - alpha / 2, df)
    
    # Power is the probability that the t-statistic exceeds t_crit under the alternative hypothesis
    # This is the CDF of the non-central t-distribution
    # Power = P(T > t_crit | ncp) + P(T < -t_crit | ncp)
    # For a positive effect (we expect to detect deviation in either direction, but let's assume positive for calculation)
    # We use the survival function for the upper tail and CDF for the lower tail
    
    # Since we are looking for deviation from -2 (could be -1.8 or -2.2), it's a two-tailed test.
    # However, the non-central t-distribution is asymmetric.
    # We approximate by using the absolute value of ncp and the two-tailed critical value.
    
    # Power = 1 - beta = P(reject H0 | H1 is true)
    # Using the non-central t-distribution
    power_upper = stats.nct.sf(t_crit, df, ncp)
    power_lower = stats.nct.cdf(-t_crit, df, ncp)
    
    total_power = power_upper + power_lower
    
    details = {
        "non_central_parameter": ncp,
        "degrees_of_freedom": df,
        "critical_t_value": t_crit,
        "power_upper_tail": power_upper,
        "power_lower_tail": power_lower,
        "total_power": total_power
    }
    
    return total_power, details


def run_power_analysis() -> Dict[str, Any]:
    """
    Run the full a priori power analysis.
    
    Returns:
        Dictionary with analysis results.
    """
    config = get_config()
    
    n_realizations = config.get("NUM_REALIZATIONS", 100)
    alpha = 0.05
    target_power = 0.80
    
    # Estimate effect size based on physical expectations
    effect_size = estimate_effect_size()
    
    # Calculate power
    power, power_details = calculate_power(effect_size, n_realizations, alpha)
    
    # Determine if the target power is met
    meets_target = power >= target_power
    
    # Calculate required sample size if target not met
    required_n = n_realizations
    if not meets_target:
        # Binary search for required n
        low, high = 1, 10000
        while high - low > 1:
            mid = (low + high) // 2
            p, _ = calculate_power(effect_size, mid, alpha)
            if p >= target_power:
                high = mid
            else:
                low = mid
        required_n = high
    
    result = {
        "task_id": "T015b",
        "description": "A priori power analysis for slope deviation detection",
        "parameters": {
            "n_realizations": n_realizations,
            "alpha": alpha,
            "target_power": target_power,
            "null_slope": -2.0,
            "detectable_deviation": 0.2,
            "effect_size_estimate": effect_size
        },
        "results": {
            "achieved_power": power,
            "meets_target": meets_target,
            "required_realizations": required_n
        },
        "details": power_details,
        "timestamp": str(np.datetime64('now'))
    }
    
    return result


def main():
    """Main entry point for the power analysis script."""
    # Ensure output directory exists
    output_dir = Path("data/metadata")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_path = output_dir / "power_analysis.json"
    
    print(f"Running power analysis for task T015b...")
    print(f"Output will be written to: {output_path}")
    
    # Run analysis
    results = run_power_analysis()
    
    # Write results to JSON
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)
    
    # Print summary
    print("\n--- Power Analysis Summary ---")
    print(f"Number of realizations: {results['parameters']['n_realizations']}")
    print(f"Effect size (Cohen's d): {results['parameters']['effect_size_estimate']:.3f}")
    print(f"Achieved power: {results['results']['achieved_power']:.3f}")
    print(f"Target power: {results['parameters']['target_power']}")
    print(f"Meets target (>= 80%): {results['results']['meets_target']}")
    
    if not results['results']['meets_target']:
        print(f"WARNING: Target power not met. Required realizations: {results['results']['required_realizations']}")
    else:
        print("SUCCESS: Power analysis confirms 100 realizations are sufficient.")
        
    return results


if __name__ == "__main__":
    main()