"""
Meta-analysis module for pairwise Diebold-Mariano tests with Westfall-Young correction.

Implements FR-006 and SC-003.
Sanctioned Exception: Overrides Plan's rejection of DM for static forecasts.
Documented deviation in research.md.
"""
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.stats.multitest import multipletests

# Local imports
from src.utils.config import get_data_root, get_project_root, resolve_path
from src.utils.logging import get_logger

logger = get_logger(__name__)

def diebold_mariano_test(
    error1: np.ndarray, 
    error2: np.ndarray, 
    h: int = 1
) -> Tuple[float, float]:
    """
    Perform Diebold-Mariano test for equal predictive accuracy.
    
    Parameters
    ----------
    error1 : np.ndarray
        Forecast errors for model 1 (actual - forecast).
    error2 : np.ndarray
        Forecast errors for model 2 (actual - forecast).
    h : int
        Forecast horizon (default 1 for nowcast/short-term).
    
    Returns
    -------
    tuple
        (statistic, p_value)
        
    Notes
    -----
    Uses squared error loss by default. The test statistic follows
    an asymptotic N(0,1) distribution under the null hypothesis of
    equal predictive accuracy.
    """
    if len(error1) != len(error2):
        raise ValueError("Error series must be of equal length")
    
    n = len(error1)
    if n < 10:
        logger.warning(f"Small sample size (n={n}) for DM test; results may be unreliable")
    
    # Loss differential (squared error loss)
    d = error1**2 - error2**2
    
    # Mean loss differential
    d_bar = np.mean(d)
    
    # Autocovariances for long-run variance estimation
    # Using Bartlett kernel with Newey-West adjustment
    gamma = np.zeros(h)
    for k in range(h):
        if k == 0:
            gamma[k] = np.mean(d * d)
        else:
            gamma[k] = np.mean(d[k:] * d[:-k])
    
    # Long-run variance estimator
    # Weights: 1 for k=0, (1 - k/(h+1)) for k>0 (Bartlett)
    var_d = gamma[0]
    for k in range(1, h):
        weight = 1 - k / (h + 1)
        var_d += 2 * weight * gamma[k]
    
    # Standard error
    se = np.sqrt(var_d / n)
    
    if se == 0:
        # If no variance, p-value is 1 (cannot reject null)
        return 0.0, 1.0
    
    # DM statistic
    dm_stat = d_bar / se
    
    # Two-tailed p-value from standard normal
    p_value = 2 * (1 - stats.norm.cdf(abs(dm_stat)))
    
    return dm_stat, p_value

def westfall_young_stepdown_maxt(
    p_values: np.ndarray, 
    test_names: List[str], 
    errors_dict: Dict[str, np.ndarray], 
    n_permutations: int = 1000, 
    random_seed: Optional[int] = None
) -> Tuple[np.ndarray, Dict[str, float]]:
    """
    Implement Westfall-Young step-down max-t correction for multiple testing.
    
    This is a custom implementation since statsmodels does not support
    Westfall-Young directly. Uses permutation-based resampling to control
    the family-wise error rate (FWER).
    
    Parameters
    ----------
    p_values : np.ndarray
        Array of raw p-values from individual tests.
    test_names : List[str]
        Names of the tests corresponding to p_values.
    errors_dict : Dict[str, np.ndarray]
        Dictionary mapping model names to their error arrays.
    n_permutations : int
        Number of permutations for the correction (default 1000).
    random_seed : Optional[int]
        Random seed for reproducibility.
    
    Returns
    -------
    tuple
        (adjusted_p_values, corrected_p_values_dict)
        adjusted_p_values: Array of Westfall-Young adjusted p-values.
        corrected_p_values_dict: Dictionary mapping test names to adjusted p-values.
    """
    if random_seed is not None:
        np.random.seed(random_seed)
    
    n_tests = len(p_values)
    model_names = list(errors_dict.keys())
    
    # Build a list of pairwise comparisons that were actually tested
    # We assume the input p_values correspond to a specific set of comparisons
    # For simplicity, we'll reconstruct the comparisons from the test_names
    comparisons = []
    for name in test_names:
        if ' vs ' in name:
            parts = name.split(' vs ')
            if len(parts) == 2:
                comparisons.append((parts[0].strip(), parts[1].strip()))
    
    if len(comparisons) != n_tests:
        raise ValueError("Number of test names does not match number of p-values")
    
    # Get the original test statistics (absolute DM statistics)
    # We need to recompute the DM statistics for the permutation procedure
    original_stats = []
    for i, (m1, m2) in enumerate(comparisons):
        if m1 in errors_dict and m2 in errors_dict:
            err1 = errors_dict[m1]
            err2 = errors_dict[m2]
            dm_stat, _ = diebold_mariano_test(err1, err2)
            original_stats.append(abs(dm_stat))
        else:
            # If model not found, use the p-value to back-calculate approximate stat
            # This is a fallback; ideally all models should be present
            if p_values[i] < 1.0:
                stat = stats.norm.ppf(1 - p_values[i] / 2)
            else:
                stat = 0.0
            original_stats.append(stat)
    
    original_stats = np.array(original_stats)
    
    # Permutation procedure
    n_obs = len(next(iter(errors_dict.values())))
    adjusted_counts = np.zeros(n_tests)
    
    logger.info(f"Starting Westfall-Young correction with {n_permutations} permutations...")
    
    for perm in range(n_permutations):
        # Generate random signs for permutation (sign-flipping bootstrap)
        # This preserves the dependency structure under the null
        signs = np.random.choice([-1, 1], size=n_obs)
        
        # Compute permuted statistics for all tests
        perm_stats = []
        for m1, m2 in comparisons:
            if m1 in errors_dict and m2 in errors_dict:
                err1 = errors_dict[m1]
                err2 = errors_dict[m2]
                
                # Apply sign flipping to the loss differential
                # Under H0, the sign of the loss differential is random
                d = err1**2 - err2**2
                d_perm = d * signs
                
                # Recompute DM statistic with permuted data
                d_bar_perm = np.mean(d_perm)
                
                # Autocovariances (same as original)
                h = 1
                gamma_perm = np.zeros(h)
                for k in range(h):
                    if k == 0:
                        gamma_perm[k] = np.mean(d_perm * d_perm)
                    else:
                        gamma_perm[k] = np.mean(d_perm[k:] * d_perm[:-k])
                
                var_d_perm = gamma_perm[0]
                for k in range(1, h):
                    weight = 1 - k / (h + 1)
                    var_d_perm += 2 * weight * gamma_perm[k]
                
                se_perm = np.sqrt(var_d_perm / n_obs)
                
                if se_perm > 0:
                    dm_stat_perm = d_bar_perm / se_perm
                else:
                    dm_stat_perm = 0.0
                
                perm_stats.append(abs(dm_stat_perm))
        
        perm_stats = np.array(perm_stats)
        
        # Step-down max-t: count how many permuted stats exceed each original stat
        for i in range(n_tests):
            # Count permutations where the max stat >= original stat i
            # (conservative step-down approach)
            if np.max(perm_stats) >= original_stats[i]:
                adjusted_counts[i] += 1
    
    # Calculate adjusted p-values
    adjusted_p_values = (adjusted_counts + 1) / (n_permutations + 1)
    
    # Create dictionary of corrected p-values
    corrected_p_values_dict = {}
    for i, name in enumerate(test_names):
        corrected_p_values_dict[name] = adjusted_p_values[i]
    
    logger.info(f"Westfall-Young correction completed. Max adjusted p-value: {np.max(adjusted_p_values):.4f}")
    
    return adjusted_p_values, corrected_p_values_dict

def run_pairwise_dm_tests(
    forecast_results: pd.DataFrame, 
    actual_outcomes: pd.DataFrame
) -> Tuple[pd.DataFrame, Dict[str, np.ndarray]]:
    """
    Perform pairwise Diebold-Mariano tests between all forecast methods.
    
    Parameters
    ----------
    forecast_results : pd.DataFrame
        DataFrame containing forecasts from different methods.
        Expected columns: 'date', 'method', 'forecast_value', 'actual' (optional).
    actual_outcomes : pd.DataFrame
        DataFrame containing actual election outcomes.
        Expected columns: 'date', 'actual_vote_share'.
    
    Returns
    -------
    tuple
        (results_df, errors_dict)
        results_df: DataFrame with DM test results.
        errors_dict: Dictionary of error arrays for each method.
    """
    # Merge forecasts with actuals
    merged = pd.merge(
        forecast_results, 
        actual_outcomes, 
        on='date', 
        how='inner'
    )
    
    if 'actual' not in merged.columns and 'actual_vote_share' in merged.columns:
        merged['actual'] = merged['actual_vote_share']
    
    if 'actual' not in merged.columns:
        raise ValueError("Could not find actual outcomes in merged data")
    
    # Calculate errors for each method
    methods = merged['method'].unique()
    errors_dict = {}
    
    for method in methods:
        method_data = merged[merged['method'] == method].sort_values('date')
        errors = method_data['actual'].values - method_data['forecast_value'].values
        errors_dict[method] = errors
    
    # Perform pairwise DM tests
    comparisons = []
    raw_p_values = []
    test_names = []
    
    for i, m1 in enumerate(methods):
        for j, m2 in enumerate(methods):
            if i < j:  # Only test each pair once
                err1 = errors_dict[m1]
                err2 = errors_dict[m2]
                
                # Ensure equal length
                min_len = min(len(err1), len(err2))
                err1_trim = err1[:min_len]
                err2_trim = err2[:min_len]
                
                dm_stat, p_val = diebold_mariano_test(err1_trim, err2_trim)
                
                comparisons.append((m1, m2))
                raw_p_values.append(p_val)
                test_names.append(f"{m1} vs {m2}")
    
    raw_p_values = np.array(raw_p_values)
    
    # Create results DataFrame
    results_data = {
        'comparison': test_names,
        'method1': [c[0] for c in comparisons],
        'method2': [c[1] for c in comparisons],
        'dm_statistic': [abs(p) for p in raw_p_values],  # Store absolute value
        'raw_p_value': raw_p_values
    }
    
    results_df = pd.DataFrame(results_data)
    
    return results_df, errors_dict

def meta_analysis(
    forecast_results_path: str,
    actual_outcomes_path: str,
    output_path: str,
    n_permutations: int = 1000,
    random_seed: Optional[int] = None
) -> pd.DataFrame:
    """
    Main function to run meta-analysis with DM tests and Westfall-Young correction.
    
    Parameters
    ----------
    forecast_results_path : str
        Path to the frequentist forecasts CSV.
    actual_outcomes_path : str
        Path to the actual outcomes CSV.
    output_path : str
        Path to save the meta-analysis results.
    n_permutations : int
        Number of permutations for Westfall-Young correction.
    random_seed : Optional[int]
        Random seed for reproducibility.
    
    Returns
    -------
    pd.DataFrame
        DataFrame with DM test results and adjusted p-values.
    """
    logger.info(f"Loading forecast results from {forecast_results_path}")
    forecast_results = pd.read_csv(forecast_results_path)
    
    logger.info(f"Loading actual outcomes from {actual_outcomes_path}")
    actual_outcomes = pd.read_csv(actual_outcomes_path)
    
    # Run pairwise DM tests
    logger.info("Performing pairwise Diebold-Mariano tests...")
    results_df, errors_dict = run_pairwise_dm_tests(forecast_results, actual_outcomes)
    
    if len(results_df) == 0:
        logger.warning("No comparisons found. Returning empty results.")
        results_df.to_csv(output_path, index=False)
        return results_df
    
    # Apply Westfall-Young correction
    logger.info(f"Applying Westfall-Young correction ({n_permutations} permutations)...")
    test_names = results_df['comparison'].tolist()
    raw_p_values = results_df['raw_p_value'].values
    
    adjusted_p_values, corrected_dict = westfall_young_stepdown_maxt(
        raw_p_values, 
        test_names, 
        errors_dict, 
        n_permutations=n_permutations,
        random_seed=random_seed
    )
    
    # Add adjusted p-values to results
    results_df['westfall_young_p_value'] = adjusted_p_values
    results_df['significant_at_0.05'] = adjusted_p_values < 0.05
    
    # Save results
    results_df.to_csv(output_path, index=False)
    logger.info(f"Meta-analysis results saved to {output_path}")
    
    # Log summary
    significant_count = (adjusted_p_values < 0.05).sum()
    logger.info(f"Found {significant_count} significant differences out of {len(results_df)} comparisons")
    
    return results_df

def main():
    """Entry point for running meta-analysis."""
    project_root = get_project_root()
    data_root = get_data_root()
    
    # Define paths
    forecast_path = resolve_path("data/processed/frequentist_forecasts.csv", project_root)
    outcomes_path = resolve_path("data/processed/election_outcomes.csv", project_root)
    output_path = resolve_path("data/processed/meta_analysis_results.csv", project_root)
    
    # Check if input files exist
    if not os.path.exists(forecast_path):
        logger.error(f"Forecast results not found at {forecast_path}. Run frequentist analysis first.")
        sys.exit(1)
    
    if not os.path.exists(outcomes_path):
        logger.error(f"Actual outcomes not found at {outcomes_path}. Run data download/harmonization first.")
        sys.exit(1)
    
    # Run meta-analysis
    results = meta_analysis(
        forecast_path,
        outcomes_path,
        output_path,
        n_permutations=1000,
        random_seed=42
    )
    
    print("\n=== Meta-Analysis Results ===")
    print(results.to_string(index=False))
    print("\n" + "=" * 40)
    
    # Log the sanctioned exception note
    logger.info("SANCTIONED EXCEPTION: This task implements FR-006 DM test, overriding Plan's rejection.")
    logger.info("Documented in research.md as an architectural deviation for hypothesis testing.")

if __name__ == "__main__":
    main()
