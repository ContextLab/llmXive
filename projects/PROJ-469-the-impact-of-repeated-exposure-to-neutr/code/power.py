"""
Power analysis module for the Political IAT study.

Contains functions for both a priori and retrospective power analysis.
"""
import os
import numpy as np
import pandas as pd
from scipy import stats
from pathlib import Path
from config_manager import get_results_path, get_alpha_level, get_analysis_seed
from logging_config import get_logger
from models import run_primary_analysis

logger = get_logger(__name__)

def calculate_ncp(effect_size, n, alpha=0.05, df_num=1):
    """
    Calculate the Non-Centrality Parameter (NCP) for an F-test.
    
    Args:
        effect_size: Cohen's f (effect size)
        n: Total sample size
        alpha: Significance level
        df_num: Numerator degrees of freedom (default 1 for interaction term)
        
    Returns:
        float: Non-centrality parameter (lambda)
    """
    # lambda = f^2 * N
    return (effect_size ** 2) * n

def calculate_power_from_ncp(ncp, df_num, df_denom, alpha=0.05):
    """
    Calculate statistical power given the NCP and degrees of freedom.
    
    Args:
        ncp: Non-centrality parameter
        df_num: Numerator degrees of freedom
        df_denom: Denominator degrees of freedom
        alpha: Significance level
        
    Returns:
        float: Statistical power (probability of rejecting null when false)
    """
    # Critical F value
    f_crit = stats.f.ppf(1 - alpha, df_num, df_denom)
    
    # Power is the probability that a non-central F variable exceeds the critical value
    power = 1 - stats.ncf.cdf(f_crit, df_num, df_denom, ncp)
    return power

def find_min_sample_size(effect_size, target_power=0.80, alpha=0.05, df_num=1, max_n=10000):
    """
    Find the minimum sample size required to achieve target power.
    
    Args:
        effect_size: Cohen's f
        target_power: Desired power (default 0.80)
        alpha: Significance level
        df_num: Numerator degrees of freedom
        max_n: Maximum sample size to search
        
    Returns:
        int: Minimum required sample size
    """
    # Simple binary search or linear search for required N
    # For interaction effect in regression with 1 df numerator
    n = 10
    while n < max_n:
        ncp = calculate_ncp(effect_size, n, alpha, df_num)
        # Approximate df_denom = n - (number of parameters)
        # For primary model: Intercept + News + Ideology + Interaction + Covariates?
        # Let's assume a base model with ~6 parameters for estimation
        df_denom = n - 6 
        if df_denom <= 0:
            n += 1
            continue
            
        power = calculate_power_from_ncp(ncp, df_num, df_denom, alpha)
        if power >= target_power:
            return n
        n += 10 # Step up
    
    return max_n

def run_power_analysis():
    """
    Perform a priori power analysis based on literature effect sizes.
    
    Uses a small effect size (f = 0.10) typical for social science interactions.
    Outputs results to results/power_design.csv.
    """
    logger.info("Running a priori power analysis...")
    
    # Literature-based effect size (small interaction effect)
    literature_effect_size = 0.10 
    alpha = get_alpha_level()
    target_power = 0.80
    
    required_n = find_min_sample_size(
        effect_size=literature_effect_size,
        target_power=target_power,
        alpha=alpha
    )
    
    results_path = get_results_path()
    output_file = results_path / "power_design.csv"
    
    df = pd.DataFrame([{
        "effect_size": literature_effect_size,
        "alpha": alpha,
        "target_power": target_power,
        "required_n": required_n,
        "met_target": "Yes" if required_n < 5000 else "No" # Arbitrary threshold for 'met'
    }])
    
    df.to_csv(output_file, index=False)
    logger.info(f"A priori power analysis saved to {output_file}")
    return df

def calculate_retrospective_power(observed_df, alpha=0.05):
    """
    Calculate retrospective (post-hoc) power based on observed model results.
    
    Args:
        observed_df: DataFrame containing model results (must have 'effect_size' or 'f_stat')
        alpha: Significance level
        
    Returns:
        dict: Calculated power metrics
    """
    if observed_df.empty:
        logger.warning("Observed model results are empty. Cannot calculate retrospective power.")
        return {
            "observed_power": np.nan,
            "required_n": np.nan,
            "effect_size": np.nan,
            "met_target": False
        }
    
    # Extract observed effect size (Cohen's f)
    # If the model output has 'f_stat', we can derive f: f = sqrt(F / N)
    # If it has 'effect_size' (Cohen's f), use that directly.
    # Assuming the model output from run_primary_analysis includes 'effect_size' (Cohen's f)
    # or we calculate it from the F-statistic of the interaction term.
    
    # Fallback: assume we need to compute from F and N if not present
    # For now, let's assume the input df has 'f_stat' and 'n'
    if 'f_stat' in observed_df.columns and 'n' in observed_df.columns:
        f_stat = observed_df['f_stat'].iloc[0]
        n = observed_df['n'].iloc[0]
        # Cohen's f = sqrt(F / N)
        effect_size = np.sqrt(f_stat / n)
    elif 'effect_size' in observed_df.columns:
        effect_size = observed_df['effect_size'].iloc[0]
        n = observed_df['n'].iloc[0]
    else:
        logger.error("Cannot calculate retrospective power: missing 'f_stat' or 'effect_size' in model results.")
        return {
            "observed_power": np.nan,
            "required_n": np.nan,
            "effect_size": np.nan,
            "met_target": False
        }
    
    # Degrees of freedom for interaction term (numerator) = 1
    df_num = 1
    # Denominator df = N - k (k = number of parameters). Approximate k=6.
    k = 6
    df_denom = n - k
    if df_denom <= 0:
        df_denom = 1
        
    ncp = calculate_ncp(effect_size, n, alpha, df_num)
    observed_power = calculate_power_from_ncp(ncp, df_num, df_denom, alpha)
    
    # Recalculate required N for this observed effect size
    required_n = find_min_sample_size(effect_size, target_power=0.80, alpha=alpha)
    
    return {
        "observed_power": observed_power,
        "required_n": required_n,
        "effect_size": effect_size,
        "met_target": observed_power >= 0.80
    }

def run_retrospective_power_analysis():
    """
    Main entry point for retrospective power analysis.
    
    1. Runs the primary analysis to get model results.
    2. Calculates observed power.
    3. Saves results to results/power_analysis.csv.
    """
    logger.info("Starting retrospective power analysis...")
    
    # Ensure results directory exists
    results_path = get_results_path()
    ensure_dirs(results_path)
    
    # Run primary analysis to get the model results
    # This will load data, impute, and fit the model
    # We need to capture the model stats (F, N, Effect Size)
    # The run_primary_analysis function in models.py should return a summary dict or DF
    # If it doesn't, we might need to call fit_primary_model directly.
    
    try:
        # Attempt to get model summary from the primary analysis
        # Assuming run_primary_analysis returns a dict or DF with necessary stats
        model_results = run_primary_analysis()
        
        if model_results is None or (isinstance(model_results, pd.DataFrame) and model_results.empty):
            logger.error("Primary analysis failed to produce results. Cannot perform retrospective power analysis.")
            # Create a placeholder file indicating failure
            output_file = results_path / "power_analysis.csv"
            pd.DataFrame([{
                "observed_power": np.nan,
                "required_n": np.nan,
                "effect_size": np.nan,
                "met_target": False
            }]).to_csv(output_file, index=False)
            return
        
        # Ensure model_results is a DataFrame or convert to one if it's a dict
        if isinstance(model_results, dict):
            model_df = pd.DataFrame([model_results])
        else:
            model_df = model_results
        
        # Ensure 'n' is in the dataframe (sample size)
        if 'n' not in model_df.columns:
            # Try to infer from the data if possible, or use a default
            # For now, we assume the data loader or preprocessing sets a global or we can get it
            # A safer bet is to pass the data size from the calling context, but here we rely on the model output
            # If the model output doesn't have 'n', we might need to load data again or assume it's in the model summary
            # Let's assume the model summary from run_primary_analysis includes 'n'
            logger.warning("'n' not found in model results. Attempting to load data to determine N.")
            # Fallback: Load data to get N
            from data_loader import load_project_implicit_data
            from preprocessing import load_data
            try:
                raw_data = load_project_implicit_data()
                if raw_data is not None:
                    model_df['n'] = len(raw_data)
                else:
                    raise ValueError("Could not load data to determine N.")
            except Exception as e:
                logger.error(f"Failed to determine N: {e}")
                return
        
        # Calculate retrospective power
        metrics = calculate_retrospective_power(model_df)
        
        output_file = results_path / "power_analysis.csv"
        pd.DataFrame([metrics]).to_csv(output_file, index=False)
        logger.info(f"Retrospective power analysis saved to {output_file}")
        
    except Exception as e:
        logger.error(f"Retrospective power analysis failed: {e}")
        raise

def ensure_dirs(path):
    """Helper to ensure directories exist."""
    os.makedirs(path, exist_ok=True)