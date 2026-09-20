import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.formula.api import ols

from data.config import get_config
from utils.logger import get_logger

# Ensure statsmodels is imported for the formula API used in regression
# The regression module uses: outcome: post_self_esteem, covariate: pre_self_esteem
# predictors: avatar_condition, comparison_tendency, interaction

logger = get_logger(__name__)

CONFIG = get_config()
MAX_ITERATIONS = 5000
TARGET_VARIANCE = 0.01
MIN_ITERATIONS = 1000

def run_single_bootstrap_iteration(
    data: pd.DataFrame,
    formula: str,
    seed: int
) -> Dict[str, float]:
    """
    Perform a single bootstrap iteration.
    Resamples the data with replacement, fits the ANCOVA model,
    and returns the estimated coefficients.
    """
    np.random.seed(seed)
    # Resample indices with replacement
    n = len(data)
    indices = np.random.choice(n, size=n, replace=True)
    boot_data = data.iloc[indices].reset_index(drop=True)

    try:
        # Fit the model
        model = ols(formula, data=boot_data).fit()
        # Extract coefficients
        coeffs = model.params.to_dict()
        return coeffs
    except Exception as e:
        logger.warning(f"Bootstrap iteration failed: {e}")
        return None

def calculate_confidence_intervals(
    coefficient_values: List[float],
    confidence_level: float = 0.95
) -> Tuple[float, float]:
    """
    Calculate the confidence interval for a list of coefficient values
    using the percentile method.
    """
    if not coefficient_values:
        return (np.nan, np.nan)
    
    alpha = 1 - confidence_level
    lower_pct = (alpha / 2) * 100
    upper_pct = (1 - alpha / 2) * 100
    
    lower = np.percentile(coefficient_values, lower_pct)
    upper = np.percentile(coefficient_values, upper_pct)
    
    return (lower, upper)

def calculate_ci_width_variance(
    all_coefficient_lists: List[Dict[str, List[float]]],
    target_coef: str
) -> float:
    """
    Calculate the variance of the CI widths for a specific coefficient
    across the accumulated bootstrap iterations.
    """
    if len(all_coefficient_lists) < 2:
        return float('inf')
    
    ci_widths = []
    for iteration_data in all_coefficient_lists:
        if target_coef in iteration_data:
            vals = iteration_data[target_coef]
            if len(vals) >= 2:
                ci = calculate_confidence_intervals(vals)
                width = ci[1] - ci[0]
                ci_widths.append(width)
    
    if len(ci_widths) < 2:
        return float('inf')
    
    return float(np.var(ci_widths))

def run_bootstrap_stability(
    data: pd.DataFrame,
    formula: str,
    target_coef: str = 'avatar_condition',
    seed: Optional[int] = None
) -> Dict[str, Any]:
    """
    Run bootstrap resampling until CI width variance < 0.01 or max iterations reached.
    Returns the final coefficients, CI, and stability metrics.
    """
    if seed is None:
        seed = CONFIG.get('seed', 42)
    
    logger.info(f"Starting bootstrap stability analysis for {target_coef}")
    logger.info(f"Target: CI width variance < {TARGET_VARIANCE}, Min iterations: {MIN_ITERATIONS}")
    
    all_coefficients: Dict[str, List[float]] = {target_coef: []}
    iteration = 0
    current_variance = float('inf')
    
    # We need to store all coefficient lists to calculate variance of CI widths over time?
    # Actually, the requirement is "CI width variance < 0.01".
    # This usually means the variance of the CI width estimates across the bootstrap samples?
    # No, standard interpretation: The variance of the CI width *estimates* as we add more samples should stabilize.
    # Or simpler: The variance of the coefficient distribution is the standard error squared.
    # Re-reading FR-005: "until CI width variance < 0.01".
    # Interpretation: We calculate the CI width at each step (or batch) and check the variance of those widths.
    # However, a more robust interpretation for "stopping criterion" is that the CI width itself has stabilized.
    # Let's implement: Run iterations. After MIN_ITERATIONS, calculate the CI width.
    # Then run more. If the variance of the CI widths (calculated over a sliding window or the whole set) drops below 0.01, stop.
    
    # Simpler interpretation for "CI width variance":
    # The variance of the bootstrap distribution of the coefficient is the square of the SE.
    # The "CI Width" is 1.96 * 2 * SE (approx).
    # Maybe it means the variance of the *estimates* of the CI width?
    # Let's assume the prompt means: The variance of the coefficient estimates (which determines CI width)
    # should be stable. But the prompt says "CI width variance".
    # Let's calculate the CI width for the current accumulated set.
    # Then calculate the variance of the *sequence* of CI widths?
    # Given the ambiguity, I will implement:
    # 1. Run iterations.
    # 2. Every N iterations, calculate the CI width of the current accumulated set.
    # 3. Check the variance of these CI width values.
    
    # To be safe and meet "CI width variance < 0.01":
    # We will collect the CI width at each iteration (or batch) and check the variance of that list.
    
    # Let's simplify: We will run iterations. We maintain a list of coefficient values.
    # We calculate the CI width of this list.
    # We check if the variance of the *coefficient values* is stable? No, prompt says CI width variance.
    # Let's assume it means: The variance of the bootstrap distribution of the CI width.
    # This requires nested bootstrapping or a specific estimator.
    # Alternative: The variance of the CI width *estimate* as N increases.
    
    # Practical implementation:
    # Run iterations. Store coefficient values.
    # Calculate CI width for the current set.
    # Check if the variance of the coefficient values (which drives CI width) is stable?
    # Let's stick to the literal text: "CI width variance".
    # We will calculate the CI width at each step (or batch) and compute the variance of that sequence.
    # If the sequence is short, variance is high. As it grows, it should stabilize.
    
    # Implementation:
    # Accumulate coefficients.
    # Every 100 iterations (after MIN), calculate the CI width of the *current* accumulated set.
    # Store these widths in a list `width_history`.
    # Calculate variance of `width_history`. If < 0.01 and iterations >= MIN, stop.
    
    width_history: List[float] = []
    check_interval = 100
    
    for i in range(MAX_ITERATIONS):
        iteration += 1
        current_seed = seed + i
        
        coeffs = run_single_bootstrap_iteration(data, formula, current_seed)
        if coeffs is None:
            continue
        
        if target_coef in coeffs:
            all_coefficients[target_coef].append(coeffs[target_coef])
        
        # Check stability after MIN iterations
        if iteration >= MIN_ITERATIONS and iteration % check_interval == 0:
            vals = all_coefficients[target_coef]
            if len(vals) >= 2:
                ci = calculate_confidence_intervals(vals)
                width = ci[1] - ci[0]
                width_history.append(width)
                
                if len(width_history) >= 3:
                    var_width = float(np.var(width_history))
                    logger.debug(f"Iteration {iteration}: CI Width = {width:.4f}, Variance of widths = {var_width:.6f}")
                    
                    if var_width < TARGET_VARIANCE:
                        logger.info(f"Stability criterion met at iteration {iteration}. Variance: {var_width:.6f}")
                        current_variance = var_width
                        break
    
    # Final calculation
    final_vals = all_coefficients[target_coef]
    final_ci = calculate_confidence_intervals(final_vals)
    final_width = final_ci[1] - final_ci[0]
    
    # If we didn't break early, calculate variance of the last batch or all history
    if current_variance == float('inf') and len(width_history) > 0:
        current_variance = float(np.var(width_history))
    
    if current_variance == float('inf'):
        logger.warning(f"Stability criterion NOT met after {iteration} iterations. Final variance: {current_variance}")
    else:
        logger.info(f"Bootstrap completed. Iterations: {iteration}, Final CI Width Variance: {current_variance:.6f}")
    
    return {
        "iterations": iteration,
        "coefficients": final_vals,
        "ci_lower": final_ci[0],
        "ci_upper": final_ci[1],
        "ci_width": final_width,
        "ci_width_variance": current_variance,
        "stability_met": current_variance < TARGET_VARIANCE and iteration >= MIN_ITERATIONS
    }

def run_bootstrap_analysis(
    data: pd.DataFrame,
    formula: str,
    target_coef: str = 'avatar_condition',
    seed: Optional[int] = None
) -> Dict[str, Any]:
    """
    Wrapper to run the bootstrap analysis and return results in a standardized format.
    """
    results = run_bootstrap_stability(data, formula, target_coef, seed)
    
    # Add summary stats
    results["mean"] = float(np.mean(results["coefficients"]))
    results["std"] = float(np.std(results["coefficients"]))
    results["target_coef"] = target_coef
    
    return results

def main():
    """
    Main entry point for the bootstrap module.
    Loads processed data, runs bootstrap, and saves results.
    """
    config = get_config()
    data_path = Path(config.get("processed_data_path", "data/processed/imputed_data.csv"))
    
    if not data_path.exists():
        logger.error(f"Data file not found: {data_path}")
        return
    
    logger.info(f"Loading data from {data_path}")
    df = pd.read_csv(data_path)
    
    # Define the formula based on the regression task (T018)
    # Outcome: post_self_esteem, Covariate: pre_self_esteem
    # Predictors: avatar_condition, comparison_tendency, interaction
    formula = "post_self_esteem ~ pre_self_esteem + avatar_condition + comparison_tendency + avatar_condition:comparison_tendency"
    
    logger.info(f"Running bootstrap analysis with formula: {formula}")
    
    results = run_bootstrap_analysis(df, formula, target_coef='avatar_condition', seed=config.get('seed'))
    
    output_path = Path("data/processed/bootstrap_results.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    import json
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Bootstrap results saved to {output_path}")
    return results

if __name__ == "__main__":
    main()
