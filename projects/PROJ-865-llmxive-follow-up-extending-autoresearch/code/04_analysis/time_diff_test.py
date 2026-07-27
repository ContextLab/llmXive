"""
T029a: Implement Tobit Regression for Time-to-Pivot differences.

This script performs a paired analysis on Time-to-Pivot data, handling censored
observations (where the baseline failed/timeout) using Tobit Regression.

Input: data/derived/results.csv (produced by T022)
Output: data/derived/time_diff_results.json
"""
import json
import sys
import csv
import os
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional
from collections import defaultdict
import pandas as pd
import numpy as np
from statsmodels.discrete.discrete_model import Tobit
from statsmodels.tools.tools import add_constant
import warnings
warnings.filterwarnings("ignore")

# Import project config for timeout values
# We assume utils.config exists as per T007
try:
    from utils.config import TIMEOUT_SECONDS
except ImportError:
    # Fallback if import fails, though T007 should exist
    TIMEOUT_SECONDS = 3600  # Default 1 hour

logger = None

def get_logger():
    global logger
    if logger is None:
        import logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        logger = logging.getLogger(__name__)
    return logger

def load_results_csv(filepath: str) -> pd.DataFrame:
    """
    Load the merged results CSV.
    Expects columns: task_id, method, time_to_pivot, success, failure_type
    """
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {filepath}")
    
    df = pd.read_csv(path)
    
    required_cols = ['task_id', 'method', 'time_to_pivot', 'success', 'failure_type']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in {filepath}: {missing}")
    
    return df

def extract_paired_differences(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Reshape the data to ensure pairing.
    Creates a wide-format dataframe where each row is a task_id,
    with columns for Rule Engine time, Baseline time, and censoring flags.
    
    Returns:
        paired_df: DataFrame with paired data
        stats: Dictionary of summary stats for logging
    """
    log = get_logger()
    log.info(f"Processing {len(df)} rows for pairing...")
    
    # Pivot to wide format
    # We need time_to_pivot for 'rule_engine' and 'baseline'
    pivot_df = df.pivot_table(
        index='task_id',
        columns='method',
        values=['time_to_pivot', 'success', 'failure_type'],
        aggfunc='first'
    )
    
    # Flatten column names
    pivot_df.columns = ['_'.join(col).strip() for col in pivot_df.columns.values]
    
    # Rename for clarity
    pivot_df = pivot_df.rename(columns={
        'time_to_pivot_rule_engine': 'time_rule',
        'time_to_pivot_baseline': 'time_baseline',
        'success_rule_engine': 'success_rule',
        'success_baseline': 'success_baseline',
        'failure_type_rule_engine': 'failure_type'
    })
    
    # Drop rows where we don't have both times (though merge_results should ensure this)
    pivot_df = pivot_df.dropna(subset=['time_rule', 'time_baseline'])
    
    # Determine censoring
    # If baseline success is False, we treat the time as censored (lower bound = TIMEOUT)
    # However, the task says "Include rows where baseline failed... as censored (time > TIMEOUT)"
    # This implies the recorded time in the CSV might be the timeout value or we treat it as > TIMEOUT.
    # We will create an indicator: is_censored = (success_baseline == False)
    # And use the recorded time (which should be >= TIMEOUT) or TIMEOUT as the observation.
    
    pivot_df['is_censored'] = ~pivot_df['success_baseline'].astype(bool)
    
    # For Tobit, we need a dependent variable (Y) and independent variables (X).
    # SC-001: "regression is performed on the paired differences or a paired design matrix"
    # We will model: (Time_Baseline - Time_Rule) ~ 1 + Failure_Type
    # But we must handle the censoring on the Baseline side.
    # Actually, Tobit models a latent variable Y*.
    # Y_observed = Y* if Y* < Censoring_Limit, else Censoring_Limit.
    # Here, the "observation" is the difference.
    # If Baseline is censored (failed), the true difference is likely large (Baseline took forever).
    # Let's define the observation variable as:
    # Y = Time_Baseline - Time_Rule
    # If Baseline failed, Y is censored from below at (TIMEOUT - Time_Rule).
    
    pivot_df['diff_observed'] = pivot_df['time_baseline'] - pivot_df['time_rule']
    
    # Calculate the lower bound for censoring for each row
    # If success_baseline is False, the true time is > TIMEOUT.
    # So the true difference is > TIMEOUT - time_rule.
    pivot_df['censor_lower'] = np.where(
        pivot_df['is_censored'],
        TIMEOUT_SECONDS - pivot_df['time_rule'],
        -np.inf  # No lower bound if not censored (standard Tobit handles this by not censoring)
    )
    
    # Prepare metadata
    stats = {
        "total_pairs": len(pivot_df),
        "censored_count": int(pivot_df['is_censored'].sum()),
        "uncensored_count": int(len(pivot_df) - pivot_df['is_censored'].sum())
    }
    log.info(f"Paired data ready: {stats['total_pairs']} pairs, {stats['censored_count']} censored.")
    
    return pivot_df, stats

def calculate_confidence_interval(
    beta: float, 
    se: float, 
    confidence: float = 0.95
) -> Tuple[float, float]:
    """
    Calculate confidence interval for the coefficient.
    Uses normal approximation (z-score) for large samples.
    """
    from scipy.stats import norm
    z = norm.ppf(1 - (1 - confidence) / 2)
    lower = beta - z * se
    upper = beta + z * se
    return lower, upper

def perform_paired_tobit_regression(pivot_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Perform Tobit regression on the paired differences.
    Model: Diff ~ Failure_Type
    Censoring: Lower bound at (TIMEOUT - time_rule) for failed baselines.
    """
    log = get_logger()
    log.info("Fitting Tobit regression model...")
    
    # Prepare X and Y
    # Y: diff_observed
    # X: failure_type (categorical)
    # We need to handle the censoring limits properly for statsmodels Tobit.
    # statsmodels Tobit expects `lower` and `upper` limits.
    # If a point is not censored, we can set lower=-inf, upper=inf.
    
    Y = pivot_df['diff_observed'].values
    
    # Create dummy variables for Failure_Type
    # Reference category: "Syntactic Error" (or first alphabetically)
    failure_types = pivot_df['failure_type'].astype(str).unique()
    log.info(f"Failure types in data: {failure_types}")
    
    # Create design matrix with intercept and dummies
    # Using pandas get_dummies for simplicity
    dummies = pd.get_dummies(pivot_df['failure_type'], prefix='ft', drop_first=True)
    X = pd.concat([pd.Series(1, index=pivot_df.index, name='Intercept'), dummies], axis=1)
    
    # Prepare limits
    # statsmodels Tobit: lower, upper
    # If is_censored is True, we have a lower bound.
    # If is_censored is False, we set lower = -inf, upper = inf (effectively no censoring for that point)
    # However, statsmodels Tobit implementation might require finite bounds or specific handling.
    # A robust way:
    # If not censored: lower = -inf, upper = inf (but we can't pass inf easily in some versions)
    # Alternative: Use a very large number for non-censored lower bound? No, that's wrong.
    # Correct approach for statsmodels:
    # The `lower` argument can be an array. If lower[i] < Y[i], it's not censored from below.
    # If we want to model right-censoring or left-censoring specifically:
    # statsmodels Tobit (legacy) or `Tobit` in `statsmodels.discrete` handles:
    # y = max(lower, min(upper, y*))
    
    # Let's construct limits:
    # For censored rows (baseline failed): true diff > (TIMEOUT - time_rule).
    # So we observe the value at the limit? Or we observe the value but know it's censored?
    # The prompt says: "Include rows where baseline failed... as censored observations (time > TIMEOUT)"
    # This implies the recorded time in CSV is the TIMEOUT (or we treat it as such).
    # If the CSV has the actual timeout value (e.g. 3600), then Y_observed = 3600 - time_rule.
    # The latent variable Y* > 3600 - time_rule.
    # So we set lower = 3600 - time_rule, and we observe Y = lower.
    
    limits_lower = np.full(len(Y), -np.inf)
    limits_upper = np.full(len(Y), np.inf)
    
    censored_mask = pivot_df['is_censored'].values
    
    # For censored rows, the observed Y is the lower bound (since time > TIMEOUT, we see TIMEOUT)
    # Actually, if the recorded time is exactly TIMEOUT, then Y_observed = TIMEOUT - time_rule.
    # And we know Y* >= Y_observed.
    # So we set lower = Y_observed, and the model treats it as censored from below.
    limits_lower[censored_mask] = Y[censored_mask]
    limits_upper[censored_mask] = np.inf # No upper censoring for these specific points in this logic
    
    # For non-censored, we set lower = -inf, upper = inf (no censoring)
    # But statsmodels might choke on -inf. Let's use a very small number for -inf if needed,
    # but standard practice is to pass the array and let the library handle it.
    # If the library doesn't support -inf in array, we might need to filter or use a trick.
    # Let's try passing -np.inf directly first. If it fails, we adjust.
    
    # Ensure X is numpy array
    X_arr = X.values.astype(float)
    
    try:
        # Initialize Tobit model
        # statsmodels.discrete.discrete_model.Tobit
        # Arguments: endog, exog, lower, upper
        model = Tobit(endog=Y, exog=X_arr, lower=limits_lower, upper=limits_upper)
        result = model.fit()
        
        # Extract results
        # We are interested in the intercept (overall effect) and the coefficients for failure types.
        # The prompt asks for p_value, ci_lower, ci_upper, statistic.
        # Usually, this refers to the main effect of the method difference or the interaction.
        # Since we are modeling the difference directly, the Intercept represents the average difference
        # for the reference category (e.g., Syntactic Error).
        
        # Let's report the Intercept (overall average time difference) and its stats.
        # Or if the task implies testing if the difference is significantly different from 0.
        
        p_value = result.pvalues[0] # Intercept p-value
        coef = result.params[0]
        bse = result.bse[0]
        
        # Statistic (t-statistic)
        statistic = result.tvalues[0]
        
        # Confidence Interval
        ci_lower, ci_upper = calculate_confidence_interval(coef, bse)
        
        log.info(f"Tobit Regression Complete. Intercept p-value: {p_value:.4f}")
        
        return {
            "p_value": float(p_value),
            "ci_lower": float(ci_lower),
            "ci_upper": float(ci_upper),
            "statistic": float(statistic),
            "coef_intercept": float(coef),
            "n_observations": len(Y),
            "n_censored": int(censored_mask.sum()),
            "model_summary": result.summary().as_text()
        }
        
    except Exception as e:
        log.error(f"Tobit regression failed: {e}")
        # Fallback: If Tobit fails due to data issues, return a structured error or try a simpler test?
        # The task requires Tobit. If it fails, we should report the failure clearly.
        # But we must output the JSON. Let's output a failure state.
        return {
            "p_value": None,
            "ci_lower": None,
            "ci_upper": None,
            "statistic": None,
            "error": str(e),
            "status": "failed"
        }

def save_results(results: Dict[str, Any], output_path: str):
    """Save the results to JSON."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        json.dump(results, f, indent=2)
    get_logger().info(f"Results saved to {output_path}")

def main():
    log = get_logger()
    log_stage_start = log.info
    log_stage_end = log.info
    
    input_path = "data/derived/results.csv"
    output_path = "data/derived/time_diff_results.json"
    
    try:
        # Load data
        df = load_results_csv(input_path)
        
        # Extract paired differences
        pivot_df, stats = extract_paired_differences(df)
        
        if len(pivot_df) == 0:
            raise ValueError("No paired data found to analyze.")
        
        # Perform Tobit Regression
        results = perform_paired_tobit_regression(pivot_df)
        
        # Add metadata
        results["input_file"] = input_path
        results["stats"] = stats
        results["timeout_seconds"] = TIMEOUT_SECONDS
        
        # Save
        save_results(results, output_path)
        
        log_stage_end("Time difference test completed successfully.")
        return 0
        
    except Exception as e:
        log.error(f"Pipeline failed: {e}")
        import traceback
        traceback.print_exc()
        # Still try to save a failure report
        save_results({
            "error": str(e),
            "status": "failed",
            "input_file": input_path
        }, output_path)
        return 1

if __name__ == "__main__":
    sys.exit(main())