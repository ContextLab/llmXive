import os
import numpy as np
import pandas as pd
from scipy import stats
from pathlib import Path
from config_manager import get_results_path, get_alpha_level, get_analysis_seed

def calculate_ncp(effect_size, n_per_group, num_groups=2):
    """
    Calculate the non-centrality parameter (ncp) for an F-test.
    For an interaction effect in a 2x2 design (or equivalent),
    we approximate the ncp based on the effect size (f) and sample size.
    
    f = Cohen's f for ANOVA
    ncp = f^2 * N (where N is total sample size)
    """
    total_n = n_per_group * num_groups
    ncp = (effect_size ** 2) * total_n
    return ncp

def calculate_power_from_ncp(ncp, df_num, df_denom, alpha):
    """
    Calculate statistical power given the non-centrality parameter,
    degrees of freedom, and alpha level.
    """
    # The critical value from the central F distribution
    f_crit = stats.f.ppf(1 - alpha, df_num, df_denom)
    
    # Power is the probability that the non-central F exceeds the critical value
    power = 1 - stats.ncf.cdf(f_crit, df_num, df_denom, ncp)
    return power

def find_min_sample_size(effect_size, df_num, df_denom_func, alpha, target_power=0.80, max_n=10000):
    """
    Find the minimum total sample size required to achieve the target power.
    Uses a simple search (bisection or linear scan) to find the smallest N.
    
    Args:
        effect_size: Cohen's f
        df_num: Numerator degrees of freedom (for interaction, typically 1)
        df_denom_func: A function that takes total_n and returns denominator df
        alpha: Significance level
        target_power: Desired power
        max_n: Maximum sample size to search
    """
    low = 10
    high = max_n
    best_n = None
    
    # Binary search for efficiency
    while low <= high:
        mid = (low + high) // 2
        if mid < 20: # Minimum reasonable sample size
            low = mid + 1
            continue
            
        ncp = calculate_ncp(effect_size, mid)
        df_denom = df_denom_func(mid)
        
        if df_denom <= 0:
            low = mid + 1
            continue
            
        power = calculate_power_from_ncp(ncp, df_num, df_denom, alpha)
        
        if power >= target_power:
            best_n = mid
            high = mid - 1
        else:
            low = mid + 1
    
    return best_n

def run_power_analysis(effect_size=0.15, alpha=None, target_power=0.80, seed=None):
    """
    Run the a priori power analysis for the interaction effect.
    
    For the model: IAT_D ~ news_exposure_z * political_ideology
    This is effectively a 2-way interaction in a regression context.
    We approximate this as an ANOVA interaction with df_num = 1.
    
    Args:
        effect_size: Cohen's f. 0.10=small, 0.15=medium, 0.25=large (Cohen's conventions for interaction)
        alpha: Significance level (default from config)
        target_power: Target power (default 0.80)
        seed: Random seed (not strictly needed for calculation, but for consistency)
    
    Returns:
        dict: Results including required_n, effect_size, power, alpha
    """
    if alpha is None:
        alpha = get_alpha_level()
    
    if seed is None:
        seed = get_analysis_seed()
    
    np.random.seed(seed)
    
    # Degrees of freedom for the interaction term (numerator)
    # In a regression with one interaction term, df_num = 1
    df_num = 1
    
    # Denominator df depends on total N and number of predictors
    # Model: Y = b0 + b1*X1 + b2*X2 + b3*X1*X2 + e
    # Predictors = 3 (X1, X2, X1X2) + intercept = 4 parameters
    # df_denom = N - k (where k is number of parameters)
    def get_df_denom(total_n):
        k = 4 # intercept + 2 main effects + 1 interaction
        return max(1, total_n - k)
    
    required_n = find_min_sample_size(
        effect_size=effect_size,
        df_num=df_num,
        df_denom_func=get_df_denom,
        alpha=alpha,
        target_power=target_power
    )
    
    if required_n is None:
        # If we couldn't find a sample size within max_n, try a larger search or fail
        # For typical effect sizes, 10000 should be enough.
        raise ValueError(f"Could not achieve power {target_power} with effect size {effect_size} within max_n={max_n}")
    
    # Verify the power at the found N
    ncp = calculate_ncp(effect_size, required_n)
    df_denom = get_df_denom(required_n)
    final_power = calculate_power_from_ncp(ncp, df_num, df_denom, alpha)
    
    return {
        'required_n': required_n,
        'effect_size': effect_size,
        'target_power': target_power,
        'alpha': alpha,
        'achieved_power': final_power,
        'df_num': df_num,
        'df_denom': get_df_denom(required_n),
        'met_target': final_power >= target_power
    }

def ensure_dirs():
    """Ensure the results directory exists."""
    results_path = get_results_path()
    results_path.mkdir(parents=True, exist_ok=True)

def save_power_results(results_dict, filename='power_design.csv'):
    """Save power analysis results to a CSV file."""
    ensure_dirs()
    results_path = get_results_path()
    output_file = results_path / filename
    
    df = pd.DataFrame([results_dict])
    df.to_csv(output_file, index=False)
    return output_file

def run_power_pipeline(effect_size=0.15, alpha=None, target_power=0.80, seed=None):
    """
    Main entry point for the a priori power analysis task.
    Calculates the required sample size and saves the results.
    """
    results = run_power_analysis(
        effect_size=effect_size,
        alpha=alpha,
        target_power=target_power,
        seed=seed
    )
    
    output_file = save_power_results(results)
    return results, output_file

if __name__ == "__main__":
    # Run the power analysis for the task
    # Using Cohen's medium effect size (f=0.15) as a literature-based estimate
    # for interaction effects in social psychology
    results, output_path = run_power_pipeline(effect_size=0.15)
    print(f"Power analysis complete. Results saved to: {output_path}")
    print(f"Required sample size: {results['required_n']}")
    print(f"Met target power: {results['met_target']}")
