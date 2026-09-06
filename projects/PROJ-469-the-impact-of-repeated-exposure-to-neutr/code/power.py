import os
import numpy as np
import pandas as pd
from scipy import stats
from pathlib import Path
from config_manager import get_results_path, get_alpha_level, get_analysis_seed

def calculate_ncp(effect_size, n, alpha=0.05, k_predictors=2):
    """
    Calculate the Non-Centrality Parameter (NCP) for a t-test or F-test context.
    For a regression interaction term (t-test equivalent), NCP = effect_size * sqrt(n).
    For F-test with df1=k, NCP = f_squared * n.
    
    Here we assume a t-test context for the interaction term significance.
    """
    # Standard approximation for t-test NCP
    return effect_size * np.sqrt(n)

def calculate_power_from_ncp(ncp, alpha=0.05, df=1000):
    """
    Calculate power given NCP, alpha, and degrees of freedom.
    Uses the non-central t-distribution.
    """
    # Critical t-value for two-tailed test
    t_crit = stats.t.ppf(1 - alpha/2, df)
    # Power is the probability that a non-central t variable exceeds the critical value
    # Note: stats.nct.cdf gives CDF. We want 1 - CDF(t_crit) + CDF(-t_crit)
    # However, for positive NCP, the left tail is negligible.
    # Approximation: Power = 1 - CDF(t_crit, df, ncp)
    power = 1 - stats.nct.cdf(t_crit, df, ncp)
    # Add the lower tail probability for completeness (usually very small for positive NCP)
    power += stats.nct.cdf(-t_crit, df, ncp)
    return power

def find_min_sample_size(effect_size, alpha=0.05, target_power=0.80):
    """
    Find the minimum sample size required to achieve target_power.
    Uses a simple binary search or iterative approach.
    """
    n = 10
    while True:
        ncp = calculate_ncp(effect_size, n, alpha)
        power = calculate_power_from_ncp(ncp, alpha, df=n-2)
        if power >= target_power:
            return n
        if n > 100000:
            raise ValueError("Could not find sample size within reasonable bounds.")
        n += 1

def run_power_analysis(effect_size, alpha=0.05, target_power=0.80):
    """
    Run a priori power analysis.
    Returns a dictionary with required_n and met_target status.
    """
    required_n = find_min_sample_size(effect_size, alpha, target_power)
    return {
        "required_n": required_n,
        "met_target": True,
        "effect_size": effect_size,
        "alpha": alpha,
        "target_power": target_power
    }

def calculate_retrospective_power(observed_effect_size, n, alpha=0.05):
    """
    Calculate retrospective (post-hoc) power based on observed effect size and sample size.
    """
    ncp = calculate_ncp(observed_effect_size, n, alpha)
    df = n - 2  # Approximate df for regression
    power = calculate_power_from_ncp(ncp, alpha, df)
    return power

def run_retrospective_power_analysis(observed_effect_size, n, alpha=0.05, target_power=0.80):
    """
    Run retrospective power analysis.
    Calculates observed power and compares against target.
    """
    observed_power = calculate_retrospective_power(observed_effect_size, n, alpha)
    required_n = find_min_sample_size(observed_effect_size, alpha, target_power)
    
    return {
        "observed_power": observed_power,
        "required_n": required_n,
        "effect_size": observed_effect_size,
        "met_target": observed_power >= target_power
    }

def ensure_dirs():
    """Ensure results directory exists."""
    results_path = get_results_path()
    os.makedirs(results_path, exist_ok=True)

def run_retrospective_power_analysis_from_model(model_results, n, alpha=None):
    """
    Extract effect size from model results and run retrospective power analysis.
    
    Args:
        model_results: Dictionary containing 'interaction_coef' and 'interaction_se'
        n: Sample size used in the model
        alpha: Significance level (defaults to config)
    
    Returns:
        Dictionary with power analysis results
    """
    if alpha is None:
        alpha = get_alpha_level()
    
    # Cohen's d approximation for regression coefficients:
    # d = beta / SE(beta) is t-stat. 
    # For power analysis of the coefficient, we often use the t-statistic or the coefficient itself
    # normalized by the standard deviation of the predictor.
    # However, a common retrospective approach uses the observed t-statistic to estimate power.
    # t = coef / se
    # We can approximate effect size (Cohen's f2 or d) or use the t-stat directly for NCP.
    # NCP ~ t^2 for F-test, or t for t-test.
    # Let's use the t-statistic as the basis for NCP: NCP = t * sqrt(n) / something?
    # Actually, for a specific coefficient test:
    # t = beta / SE(beta)
    # The non-centrality parameter for the t-test is approximately t (if n is large) or related.
    # Let's use the definition: NCP = delta * sqrt(n).
    # We can estimate delta (effect size) from the t-stat: t = delta * sqrt(n) / sqrt(1 + ...)?
    # Simpler approach for retrospective: Use the observed t-statistic to estimate the probability
    # of rejecting H0 given the observed effect.
    # NCP = |t_obs| * sqrt(n / (n-2))? No.
    # Standard formula: NCP = t_obs. (For large n).
    # Let's use the t-statistic directly as the NCP estimate for the observed effect.
    
    t_stat = model_results['interaction_coef'] / model_results['interaction_se']
    # NCP for t-test is often approximated as t_stat.
    # But strictly, NCP = delta * sqrt(n).
    # If we assume the observed t is the true t, then NCP = t_stat.
    # Let's calculate power using NCP = t_stat.
    # Wait, t_stat is a random variable.
    # Correct approach: Estimate effect size (e.g., partial eta squared or Cohen's f2)
    # from the model, then compute power.
    # f2 = R2_change / (1 - R2_full).
    # Without R2, we can use the t-stat to estimate the non-centrality parameter directly.
    # NCP = t_stat^2 (for F with 1 df).
    # For t-test, NCP = t_stat.
    
    # Let's use the t-statistic as the NCP.
    ncp = abs(t_stat)
    
    # Calculate power
    df = n - 2
    power = calculate_power_from_ncp(ncp, alpha, df)
    
    # Estimate required N for this effect size (assuming effect size = t_stat / sqrt(n))
    # Effect size d ~ t / sqrt(n)
    effect_size = t_stat / np.sqrt(n)
    required_n = find_min_sample_size(effect_size, alpha, target_power=0.80)
    
    return {
        "observed_power": power,
        "required_n": required_n,
        "effect_size": effect_size,
        "met_target": power >= 0.80,
        "observed_t": t_stat,
        "n": n
    }

def save_retrospective_power_results(results_dict, filename="power_analysis.csv"):
    """
    Save retrospective power analysis results to a CSV file.
    """
    ensure_dirs()
    results_path = get_results_path()
    output_file = os.path.join(results_path, filename)
    
    df = pd.DataFrame([results_dict])
    df.to_csv(output_file, index=False)
    return output_file

def run_retrospective_power_pipeline(model_results, n, alpha=None):
    """
    Full pipeline: Calculate retrospective power and save results.
    """
    results = run_retrospective_power_analysis_from_model(model_results, n, alpha)
    output_file = save_retrospective_power_results(results)
    return results, output_file
