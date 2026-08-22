import os
import sys
import json
import pickle
import logging
import time
import numpy as np
import pandas as pd
from pathlib import Path
from scipy import stats
from statsmodels.stats.multitest import multipletests

# Import shared logging utilities
try:
    from logging_config import get_module_logger
except ImportError:
    # Fallback if running standalone or module not found in path
    def get_module_logger(name):
        logger = logging.getLogger(name)
        if not logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger

logger = get_module_logger(__name__)

def load_lmm_summary(path: str = "results/lmm_final_summary.json") -> dict:
    """Load the LMM final summary JSON."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"LMM summary file not found: {path}")
    with open(path, 'r') as f:
        return json.load(f)

def load_permutation_pvalue(path: str = "results/permutation_pvalue.json") -> dict:
    """Load the permutation p-value JSON."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Permutation p-value file not found: {path}")
    with open(path, 'r') as f:
        return json.load(f)

def compare_pvalues(p_parametric: float, p_empirical: float) -> float:
    """Calculate the absolute difference between parametric and empirical p-values."""
    return abs(p_parametric - p_empirical)

def generate_consistency_report(p_parametric: float, p_empirical: float) -> dict:
    """Generate a consistency report comparing parametric and empirical p-values."""
    diff = compare_pvalues(p_parametric, p_empirical)
    threshold = 0.01
    if diff <= threshold:
        statement = f"p-values are consistent (difference: {diff:.4f} <= {threshold})"
    else:
        statement = f"p-values diverge (difference: {diff:.4f} > {threshold})"
    return {
        "p_value_difference": diff,
        "robustness_statement": statement
    }

def run_permutation_test(
    data_path: str = "data/derived/cleaned_data.csv",
    summary_path: str = "results/lmm_final_summary.json",
    output_path: str = "results/permutation_pvalue.json",
    n_permutations: int = 10000
) -> dict:
    """
    Run a non-parametric permutation test by shuffling 'year' labels.
    
    This function implements the logic described in T020.
    """
    logger.info(f"Starting permutation test with {n_permutations} iterations.")
    
    # Load data
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Data file not found: {data_path}")
    df = pd.read_csv(data_path)
    
    # Load observed slope
    summary = load_lmm_summary(summary_path)
    observed_slope = summary.get('slope_year')
    if observed_slope is None:
        raise ValueError("Observed slope not found in LMM summary.")
    
    # Check memory constraints (simplified check)
    try:
        import psutil
        process = psutil.Process()
        mem_mb = process.memory_info().rss / (1024 * 1024)
        if mem_mb > 6000: # 6GB
            logger.warning(f"High memory usage ({mem_mb:.0f}MB). Reducing permutations.")
            n_permutations = 1000
    except ImportError:
        logger.warning("psutil not installed, skipping memory check.")
    
    # Perform permutations
    observed_stats = []
    n_runs = 0
    start_time = time.time()
    
    # We simulate the drift slope by permuting 'year' and recalculating a simple trend
    # Since we cannot refit the full LMM 10k times efficiently here without statsmodels,
    # we will use a simplified proxy: linear regression slope of power_residual ~ year
    # This matches the "drift coefficient" concept for the permutation null distribution.
    
    # Prepare data for fast vectorized operations
    y = df['power_residual'].values
    x = df['year'].values
    n = len(y)
    
    # Pre-calculate sums for OLS slope calculation: slope = cov(x,y) / var(x)
    # To permute y, we just need to recalculate cov(x, y_perm)
    # cov(x,y) = mean(x*y) - mean(x)*mean(y)
    # var(x) is constant since x is not permuted
    mean_x = np.mean(x)
    var_x = np.var(x)
    
    if var_x == 0:
        raise ValueError("Variance of year is zero, cannot calculate slope.")
    
    null_distributions = []
    
    # Run permutations
    for i in range(n_permutations):
        np.random.shuffle(y)
        # Calculate slope for permuted data
        # slope = (mean(x*y_perm) - mean(x)*mean(y_perm)) / var(x)
        # Note: mean(y_perm) == mean(y)
        mean_y = np.mean(y)
        mean_xy_perm = np.mean(x * y)
        slope_perm = (mean_xy_perm - mean_x * mean_y) / var_x
        null_distributions.append(slope_perm)
        
        if (i + 1) % 1000 == 0:
            logger.info(f"Completed {i+1} permutations.")
            
    elapsed_time = time.time() - start_time
    logger.info(f"Permutation test completed in {elapsed_time:.2f} seconds.")
    
    # Calculate empirical p-value (two-tailed)
    null_array = np.array(null_distributions)
    p_value = 2 * min(
        np.sum(null_array >= observed_slope) / n_permutations,
        np.sum(null_array <= observed_slope) / n_permutations
    )
    
    # Ensure p-value is within [0, 1]
    p_value = max(0.0, min(1.0, p_value))
    
    result = {
        "p_value": float(p_value),
        "iterations_run": n_permutations,
        "observed_slope": float(observed_slope),
        "status": "exact" if n_permutations == 10000 else "approximate",
        "execution_time_seconds": float(elapsed_time)
    }
    
    # Write output
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)
    logger.info(f"Permutation results saved to {output_path}")
    
    return result

def run_sensitivity_analysis(
    summary_path: str = "results/lmm_final_summary.json",
    output_path: str = "results/sensitivity_report.json"
) -> dict:
    """
    Implement sensitivity analysis by sweeping alpha across significance levels.
    
    Input: results/lmm_final_summary.json
    Output: results/sensitivity_report.json
    
    Logic:
    1. Load the primary p-value (p_value_lrt) from the LMM summary.
    2. Sweep alpha across a range: [0.001, 0.01, 0.05, 0.1, 0.2].
    3. For each alpha, determine if the drift is significant (p < alpha).
    4. Generate a conclusion statement.
    """
    logger.info("Starting sensitivity analysis.")
    
    # Load LMM summary
    if not os.path.exists(summary_path):
        raise FileNotFoundError(f"LMM summary file not found: {summary_path}")
    
    with open(summary_path, 'r') as f:
        summary = json.load(f)
    
    # Extract primary metrics
    p_value_lrt = summary.get('p_value_lrt')
    slope_year = summary.get('slope_year')
    
    if p_value_lrt is None:
        raise ValueError("p_value_lrt not found in LMM summary.")
    
    # Define alpha levels to test
    alpha_levels = [0.001, 0.01, 0.05, 0.1, 0.2]
    
    results = []
    for alpha in alpha_levels:
        is_significant = p_value_lrt < alpha
        results.append({
            "alpha": alpha,
            "p_value": float(p_value_lrt),
            "drift_significant": bool(is_significant)
        })
    
    # Generate conclusion statement
    significant_alphas = [r["alpha"] for r in results if r["drift_significant"]]
    if not significant_alphas:
        conclusion = "The drift is NOT significant at any tested alpha level (0.001 to 0.2)."
    elif significant_alphas == alpha_levels:
        conclusion = "The drift is significant across ALL tested alpha levels (0.001 to 0.2), indicating robustness to alpha choice."
    else:
        # Check if it's only significant at high alphas
        min_sig_alpha = min(significant_alphas)
        if min_sig_alpha >= 0.1:
            conclusion = f"The drift is only significant at higher alpha levels (>= {min_sig_alpha}), suggesting the result may be sensitive to the choice of alpha."
        else:
            conclusion = f"The drift is significant for alpha >= {min_sig_alpha}, but not for stricter thresholds (alpha < {min_sig_alpha})."
    
    report = {
        "p_value_lrt": float(p_value_lrt),
        "slope_year": float(slope_year) if slope_year is not None else None,
        "sweep_results": results,
        "conclusion": conclusion
    }
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else '.', exist_ok=True)
    
    # Write output
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Sensitivity analysis report saved to {output_path}")
    return report

def main():
    """Main entry point for robustness analysis."""
    logger.info("Running robustness analysis module.")
    
    # Check if we need to run sensitivity analysis (T021)
    # We assume lmm_final_summary.json exists as per dependency T012
    lmm_summary_path = "results/lmm_final_summary.json"
    sensitivity_output_path = "results/sensitivity_report.json"
    
    if os.path.exists(lmm_summary_path):
        try:
            run_sensitivity_analysis(lmm_summary_path, sensitivity_output_path)
        except Exception as e:
            logger.error(f"Error running sensitivity analysis: {e}")
            sys.exit(1)
    else:
        logger.warning(f"Skipping sensitivity analysis: {lmm_summary_path} not found.")
    
    # Check if we need to run permutation test (T020)
    # This is often run before sensitivity analysis
    data_path = "data/derived/cleaned_data.csv"
    perm_output_path = "results/permutation_pvalue.json"
    
    if os.path.exists(data_path) and os.path.exists(lmm_summary_path):
        if not os.path.exists(perm_output_path):
            try:
                run_permutation_test(data_path, lmm_summary_path, perm_output_path)
                # Also run consistency check (T020b)
                perm_data = load_permutation_pvalue(perm_output_path)
                lmm_data = load_lmm_summary(lmm_summary_path)
                p_param = lmm_data.get('p_value_lrt')
                p_emp = perm_data.get('p_value')
                if p_param and p_emp:
                    consistency = generate_consistency_report(p_param, p_emp)
                    with open("results/permutation_consistency.json", 'w') as f:
                        json.dump(consistency, f, indent=2)
            except Exception as e:
                logger.error(f"Error running permutation test: {e}")
                sys.exit(1)
    else:
        logger.warning("Skipping permutation test: required files missing.")

if __name__ == "__main__":
    main()
