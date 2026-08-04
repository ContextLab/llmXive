"""
Time-to-Pivot Analysis with Tobit Regression (Censored Data Handling).

Performs paired Tobit regression on time-to-pivot differences between Rule Engine and Baseline,
explicitly handling censored observations (timeouts).

Pre-check: Verifies that the `results.csv` contains complete pairs of task_ids for both methods.
If any pair is incomplete, the analysis aborts with a clear error.
"""
import json
import sys
import os
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
import numpy as np
from statsmodels.stats.power import TTestPower
from statsmodels.regression.mixed_linear_model import MixedLM
# Note: statsmodels does not have a native Tobit model in all versions.
# We implement a standard Tobit estimator or use a survival analysis approach if Tobit is missing.
# For this implementation, we use a custom Tobit likelihood or fallback to a robust survival model if necessary.
# However, to strictly follow "statsmodels" usage as per plan, we will attempt to use `statsmodels`
# or a standard library implementation of Tobit if available, otherwise a custom MLE.
# Given strict constraints, we will implement a custom Tobit MLE using scipy.optimize if statsmodels lacks it.
from scipy.optimize import minimize
from scipy.stats import norm

# Import local config
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from code.utils.config import TIMEOUT_SECONDS

# Setup logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(handler)

def get_logger():
    return logger

def load_results_csv(file_path: Path) -> pd.DataFrame:
    """Load the merged results CSV."""
    if not file_path.exists():
        raise FileNotFoundError(f"Results file not found: {file_path}")
    df = pd.read_csv(file_path)
    # Ensure columns exist
    required_cols = ['task_id', 'method', 'time_to_pivot', 'success', 'failure_type']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in {file_path}: {missing}")
    return df

def verify_paired_data(df: pd.DataFrame) -> Tuple[bool, List[str]]:
    """
    Pre-check: Ensure that the `task_id` pairs in results.csv are complete.
    Every task_id must have exactly one 'rule_engine' and one 'baseline' entry.
    
    Returns:
        (is_valid, list_of_missing_pairs)
    """
    logger.info("Verifying paired data integrity...")
    
    # Count occurrences of each task_id per method
    pivot_table = df.pivot_table(index='task_id', columns='method', values='time_to_pivot', aggfunc='count', fill_value=0)
    
    # Check for completeness
    # A valid pair must have count == 1 for both methods
    rule_engine_count = pivot_table['rule_engine'] if 'rule_engine' in pivot_table.columns else pd.Series(0, index=df['task_id'].unique())
    baseline_count = pivot_table['baseline'] if 'baseline' in pivot_table.columns else pd.Series(0, index=df['task_id'].unique())
    
    # Reindex to ensure alignment
    all_tasks = df['task_id'].unique()
    rule_engine_count = rule_engine_count.reindex(all_tasks, fill_value=0)
    baseline_count = baseline_count.reindex(all_tasks, fill_value=0)
    
    missing_pairs = []
    for task_id in all_tasks:
        has_rule = rule_engine_count.get(task_id, 0) > 0
        has_baseline = baseline_count.get(task_id, 0) > 0
        
        if not has_rule or not has_baseline:
            reason = []
            if not has_rule: reason.append("missing rule_engine")
            if not has_baseline: reason.append("missing baseline")
            missing_pairs.append(f"{task_id}: {', '.join(reason)}")
    
    if missing_pairs:
        logger.error(f"Paired data integrity check FAILED. {len(missing_pairs)} incomplete pairs found.")
        for pair in missing_pairs[:5]: # Log first 5
            logger.error(f"  - {pair}")
        if len(missing_pairs) > 5:
            logger.error(f"  ... and {len(missing_pairs) - 5} more.")
        return False, missing_pairs
    
    logger.info("Paired data integrity check PASSED. All task_ids have complete pairs.")
    return True, []

def calculate_paired_differences(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculate paired differences (Rule Engine - Baseline) for time_to_pivot.
    Handles censored data by marking them appropriately.
    """
    # Pivot to wide format
    wide_df = df.pivot(index='task_id', columns='method', values='time_to_pivot')
    wide_df = wide_df.reset_index()
    
    # Calculate difference
    # Note: If either is censored (timeout), the difference is still calculable as a value,
    # but the statistical model must treat it as censored.
    # We will create a 'diff' column and a 'censored' flag.
    wide_df['diff'] = wide_df['rule_engine'] - wide_df['baseline']
    
    # Determine censoring status
    # Censored if EITHER value is exactly TIMEOUT_SECONDS
    wide_df['censored'] = (wide_df['rule_engine'] == TIMEOUT_SECONDS) | (wide_df['baseline'] == TIMEOUT_SECONDS)
    
    return wide_df

def fit_tobit_model(data: pd.DataFrame) -> Dict[str, Any]:
    """
    Fit a Tobit regression model on the paired differences.
    Since statsmodels does not have a direct Tobit model for simple regression in all versions,
    we implement a Maximum Likelihood Estimation (MLE) for the Tobit model.
    
    Model: y* = X*beta + epsilon, epsilon ~ N(0, sigma^2)
    Observed y = y* if y* > c, else c (left-censored at c, or right-censored).
    Here we are testing if the mean difference is significantly different from 0.
    We can treat this as a one-sample Tobit test on the differences.
    
    Alternatively, we can use the `statsmodels` survival analysis if available, or a custom solver.
    We will implement a custom MLE for simplicity and robustness.
    
    Hypothesis: The mean difference (beta_0) is 0.
    """
    logger.info("Fitting Tobit model on paired differences...")
    
    y = data['diff'].values
    is_censored = data['censored'].values
    n = len(y)
    
    # Define negative log-likelihood for Tobit model (censored at TIMEOUT_SECONDS for the difference? No)
    # The censoring is on the *components* (time_to_pivot), not necessarily the difference.
    # However, the task requires handling censored data in the *comparison*.
    # Standard Tobit handles censoring on the dependent variable.
    # If the difference itself is censored (e.g. if both are censored, diff=0? No, diff=0 if both timeout).
    # Actually, the prompt says: "Treat any time_to_pivot equal to TIMEOUT_SECONDS as censored."
    # In a paired difference context, if one is censored, the difference is uncertain.
    # A rigorous approach: Use a survival model (Kaplan-Meier) for the difference distribution,
    # or a Tobit model where the dependent variable is the difference, and the censoring point is derived.
    # But the simplest interpretation of "Tobit on paired differences" in this context is:
    # We have a distribution of differences. Some observations are censored because the underlying time was censored.
    # If baseline is censored (>= T), and rule is finite, diff <= (rule - T). This is right-censored difference.
    # If rule is censored, diff >= (T - baseline). This is left-censored difference.
    # If both censored, diff is undefined/0? Usually treated as 0 or excluded.
    
    # Given complexity, we will implement a simplified Tobit where we treat the difference as the variable
    # and flag rows where the *observation* is censored based on the original components.
    # We will define the censoring limits for the difference.
    
    # Let's simplify: We are testing if the mean difference is 0.
    # We will use a custom MLE for a Tobit model where the dependent variable is 'diff'.
    # Censoring limits:
    # If baseline is censored (time >= T), then diff = rule - baseline <= rule - T. (Right censored at rule - T)
    # If rule is censored (time >= T), then diff = rule - baseline >= T - baseline. (Left censored at T - baseline)
    
    # We will construct the likelihood manually.
    # Parameters: mu (mean), sigma (std)
    # We assume X is just a constant (intercept) for the mean.
    
    def nll(params):
        mu, log_sigma = params
        sigma = np.exp(log_sigma)
        if sigma <= 0: return 1e10
        
        ll = 0.0
        for i in range(n):
            yi = y[i]
            censored = is_censored[i]
            
            # We need to determine the censoring direction and limit for this specific row.
            # This requires the original wide data, which we don't have in this function scope easily.
            # We will pass the limits as well.
            pass
        
        return -ll

    # To make this robust and simple, we will use a standard approach:
    # If the dataset is small, we can use a non-parametric test (Wilcoxon) on the uncensored subset,
    # but the requirement is Tobit.
    # Let's use `statsmodels` if we can find a Tobit, otherwise a custom implementation.
    # Since `statsmodels` doesn't have a direct `Tobit` class in the main API, we will implement a simple one.
    # We will assume the difference is censored if the underlying data was censored.
    # We will approximate the censoring limit.
    
    # Re-calculate limits here
    wide_data = data[['diff', 'censored', 'rule_engine', 'baseline']].copy()
    
    # Censoring limits for the difference
    # If baseline censored: diff <= rule - T (Right censored)
    # If rule censored: diff >= T - baseline (Left censored)
    # If both: diff is 0? Or we exclude? Let's exclude if both are censored (diff is 0 but uncertain).
    # Actually, if both are censored, we know both >= T, so diff is in [-inf, inf] but likely small?
    # Let's assume if both censored, we mark as 'unknown' and exclude from MLE or treat as 0 with high variance.
    # For simplicity in this script, we will exclude rows where BOTH are censored (as the difference is uninformative).
    
    mask_both_censored = (wide_data['rule_engine'] == TIMEOUT_SECONDS) & (wide_data['baseline'] == TIMEOUT_SECONDS)
    if mask_both_censored.any():
        logger.warning(f"Excluding {mask_both_censored.sum()} rows where both methods timed out (diff uninformative).")
        wide_data = wide_data[~mask_both_censored]
    
    if len(wide_data) == 0:
        raise ValueError("No valid data remaining after excluding double-censored rows.")
    
    y = wide_data['diff'].values
    
    # Construct censoring info
    # 0 = uncensored, 1 = left-censored (diff >= L), 2 = right-censored (diff <= R)
    censor_status = np.zeros(len(y), dtype=int)
    censor_limits = np.zeros(len(y))
    
    for i, row in wide_data.iterrows():
        rule = row['rule_engine']
        base = row['baseline']
        d = row['diff']
        
        if rule == TIMEOUT_SECONDS:
            # Left censored: diff >= T - base
            censor_status[i] = 1
            censor_limits[i] = TIMEOUT_SECONDS - base
        elif base == TIMEOUT_SECONDS:
            # Right censored: diff <= rule - T
            censor_status[i] = 2
            censor_limits[i] = rule - TIMEOUT_SECONDS
        else:
            censor_status[i] = 0
            censor_limits[i] = d # Not used for uncensored
    
    # Custom MLE for Tobit
    def neg_log_likelihood(params):
        mu, log_sigma = params
        sigma = np.exp(log_sigma)
        if sigma <= 1e-6: return 1e10
        
        nll = 0.0
        for i in range(len(y)):
            status = censor_status[i]
            limit = censor_limits[i]
            yi = y[i]
            
            z = (yi - mu) / sigma
            z_limit = (limit - mu) / sigma
            
            if status == 0: # Uncensored
                # PDF
                ll = norm.logpdf(yi, mu, sigma)
            elif status == 1: # Left censored (y >= limit)
                # CDF at limit? No, P(Y >= limit) = 1 - Phi((limit-mu)/sigma)
                # But we observe y=limit? No, we observe that it is >= limit.
                # In Tobit, we observe the value if it's above limit, else the limit.
                # Here, we know the difference is >= limit.
                # Likelihood is 1 - Phi(z_limit)
                ll = np.log(1 - norm.cdf(z_limit))
            elif status == 2: # Right censored (y <= limit)
                # Likelihood is Phi(z_limit)
                ll = np.log(norm.cdf(z_limit))
            
            if np.isnan(ll):
                return 1e10
            nll -= ll
        
        return nll
    
    # Initial guess
    x0 = [np.mean(y), np.log(np.std(y) + 1e-6)]
    try:
        res = minimize(neg_log_likelihood, x0, method='L-BFGS-B', bounds=[(None, None), (np.log(1e-6), None)])
        if not res.success:
            raise RuntimeError("Optimization failed: " + res.message)
        
        mu_est, log_sigma_est = res.x
        sigma_est = np.exp(log_sigma_est)
        
        # Calculate p-value for mu = 0
        # Standard error of mu
        # Hessian approximation
        hess = res.hess_inv
        if isinstance(hess, np.ndarray):
            se_mu = np.sqrt(hess[0, 0])
        else:
            # Fallback
            se_mu = sigma_est / np.sqrt(len(y))
        
        t_stat = mu_est / se_mu if se_mu > 0 else 0
        p_value = 2 * (1 - norm.cdf(abs(t_stat)))
        
        # Confidence Interval
        ci_lower = mu_est - 1.96 * se_mu
        ci_upper = mu_est + 1.96 * se_mu
        
        return {
            "mu": mu_est,
            "sigma": sigma_est,
            "p_value": p_value,
            "ci_lower": ci_lower,
            "ci_upper": ci_upper,
            "statistic": t_stat,
            "n_samples": len(y),
            "n_censored": int((censor_status != 0).sum())
        }
    except Exception as e:
        logger.error(f"Tobit model fitting failed: {e}")
        raise

def save_results(results: Dict[str, Any], output_path: Path):
    """Save results to JSON."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Results saved to {output_path}")

def main():
    """Main entry point."""
    input_path = Path("data/derived/results.csv")
    output_path = Path("data/derived/time_diff_tobit_results.json")
    
    logger.info("Starting Time-to-Pivot Tobit Analysis...")
    
    try:
        # 1. Load Data
        df = load_results_csv(input_path)
        
        # 2. Pre-check: Verify Paired Data Integrity
        is_valid, missing_pairs = verify_paired_data(df)
        if not is_valid:
            logger.error("Analysis aborted due to incomplete paired data.")
            # Write a failure report? Or just exit.
            # The task says: "If any pair is incomplete, the analysis MUST abort with a clear error message."
            sys.exit(1)
        
        # 3. Calculate Differences
        wide_df = calculate_paired_differences(df)
        
        # 4. Fit Tobit Model
        results = fit_tobit_model(wide_df)
        
        # 5. Save Results
        save_results(results, output_path)
        
        logger.info("Analysis completed successfully.")
        
    except FileNotFoundError as e:
        logger.error(f"Input file error: {e}")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"Data validation error: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
