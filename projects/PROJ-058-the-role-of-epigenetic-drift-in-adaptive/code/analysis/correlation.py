import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

from config import get_env
from preprocess.methyl import get_sample_metadata as get_methyl_metadata
from preprocess.rna_seq import get_sample_metadata as get_rna_metadata

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_variance_matrix() -> pd.DataFrame:
    """Load the unified variance matrix from data/processed/variance_matrix.csv."""
    path = Path(get_env("DATA_PROCESSED", "data/processed")) / "variance_matrix.csv"
    if not path.exists():
        raise FileNotFoundError(f"Variance matrix not found at {path}")
    logger.info(f"Loading variance matrix from {path}")
    return pd.read_csv(path)

def filter_by_condition(df: pd.DataFrame, condition: str) -> pd.DataFrame:
    """Filter the dataframe by the 'condition' column."""
    if 'condition' not in df.columns:
        logger.warning(f"'condition' column not found in dataframe. Returning all rows.")
        return df
    return df[df['condition'] == condition]

def calculate_spearman_correlation(df: pd.DataFrame, x_col: str, y_col: str) -> Tuple[float, float]:
    """Calculate Spearman's rho and p-value."""
    # Drop rows with missing values in the relevant columns
    clean_df = df[[x_col, y_col]].dropna()
    if len(clean_df) < 3:
        logger.warning(f"Insufficient data points ({len(clean_df)}) for correlation calculation.")
        return 0.0, 1.0
    
    rho, p_val = spearmanr(clean_df[x_col], clean_df[y_col])
    return float(rho), float(p_val)

def run_iterative_permutation_test(
    df: pd.DataFrame, 
    x_col: str, 
    y_col: str, 
    initial_iterations: int = 1000,
    stability_threshold: float = 0.001,
    max_iterations: int = 50000
) -> Tuple[float, float, bool]:
    """
    Run an iterative permutation test to estimate the p-value.
    Stops if the variance of the p-value over the last N iterations is stable,
    or when max_iterations is reached.
    
    Returns: (rho, empirical_p_value, converged)
    """
    x = df[x_col].dropna()
    y = df[y_col].dropna()
    
    # Ensure equal length after dropna
    min_len = min(len(x), len(y))
    if min_len < 3:
        return 0.0, 1.0, True
        
    x = x.iloc[:min_len].values
    y = y.iloc[:min_len].values
    
    # Calculate observed rho
    observed_rho, _ = spearmanr(x, y)
    
    iterations = initial_iterations
    p_values = []
    converged = False
    
    logger.info(f"Starting permutation test with {initial_iterations} iterations.")
    
    while iterations <= max_iterations:
        count_extreme = 0
        for _ in range(iterations):
            # Permute y
            perm_y = np.random.permutation(y)
            perm_rho, _ = spearmanr(x, perm_y)
            if abs(perm_rho) >= abs(observed_rho):
                count_extreme += 1
        
        p_val = count_extreme / iterations
        p_values.append(p_val)
        
        # Check convergence if we have enough history
        if len(p_values) >= 10:
            recent_p_vals = p_values[-10:]
            variance = np.var(recent_p_vals)
            if variance < stability_threshold:
                converged = True
                logger.info(f"Permutation test converged at {iterations} iterations. Variance: {variance}")
                break
        
        # Increase iterations for next check
        if iterations < max_iterations:
            iterations = min(max_iterations, iterations + 1000)
            logger.info(f"Increasing iterations to {iterations}.")
        
        if iterations >= max_iterations and not converged:
            logger.warning(f"Permutation test did not converge within {max_iterations} iterations.")
            break

    return float(observed_rho), float(p_values[-1]), converged

def run_correlation_analysis() -> Dict[str, Any]:
    """
    Main analysis function:
    1. Load variance matrix.
    2. Check temporal resolution (T026 requirement).
    3. Filter by conditions (fluctuating/constant).
    4. Calculate Spearman correlation and permutation test.
    5. Return results dictionary.
    """
    df = load_variance_matrix()
    
    results = {
        "analysis_type": "correlation",
        "total_samples": len(df),
        "conditions_analyzed": []
    }

    # T026: Temporal Resolution Flag Logic
    # Check for 'generation_count' and 'timescale' metadata.
    # If N < 3 generations or missing timescale, flag as insufficient.
    temporal_flags = {}
    
    # We need to check metadata for the dataset(s) used.
    # Assuming the variance matrix might have a 'dataset_id' or we check global metadata.
    # For this implementation, we assume the dataframe has 'generation_count' if available,
    # or we rely on external metadata check.
    # Based on task description: "if N<3 generations or missing timescale"
    
    # Let's assume the dataframe contains a 'generation_count' column or similar.
    # If not present, we check if we can infer from 'sample_id' or metadata.
    # For robustness, we check if the column exists.
    
    has_generation_data = 'generation_count' in df.columns
    has_timescale_data = 'timescale' in df.columns or 'fluctuation_timescale' in df.columns or 'env_period' in df.columns

    insufficient_flag = False
    insufficient_reasons = []

    if not has_generation_data:
        insufficient_flag = True
        insufficient_reasons.append("Missing 'generation_count' column")
    elif df['generation_count'].min() < 3:
        insufficient_flag = True
        insufficient_reasons.append(f"Minimum generation count < 3 (min: {df['generation_count'].min()})")

    if not has_timescale_data:
        insufficient_flag = True
        insufficient_reasons.append("Missing timescale metadata (fluctuation_timescale, env_period, etc.)")

    if insufficient_flag:
        results["temporal_resolution_flag"] = "insufficient"
        results["temporal_resolution_reasons"] = insufficient_reasons
        logger.warning(f"Temporal resolution insufficient: {', '.join(insufficient_reasons)}")
        # Exclude from final claim logic handled by caller or by setting a specific flag
        results["excluded_from_claim"] = True
    else:
        results["temporal_resolution_flag"] = "sufficient"
        results["excluded_from_claim"] = False

    # If excluded, we might still run analysis for logging, but mark it.
    # The task says "exclude from final claim", which implies the flag is the primary output.
    
    conditions = df['condition'].unique() if 'condition' in df.columns else ['all']
    
    for cond in conditions:
        cond_df = df if cond == 'all' else filter_by_condition(df, cond)
        
        if len(cond_df) < 3:
            logger.warning(f"Condition '{cond}' has insufficient samples ({len(cond_df)}). Skipping.")
            continue

        rho, p_val = calculate_spearman_correlation(cond_df, 'epigenetic_variance', 'expression_variance')
        perm_rho, emp_p_val, converged = run_iterative_permutation_test(cond_df, 'epigenetic_variance', 'expression_variance')
        
        cond_result = {
            "condition": cond,
            "sample_count": len(cond_df),
            "spearman_rho": rho,
            "theoretical_p_value": p_val,
            "permutation_rho": perm_rho,
            "empirical_p_value": emp_p_val,
            "permutation_converged": converged
        }
        results["conditions_analyzed"].append(cond_result)

    return results

def save_results(results: Dict[str, Any], output_path: str) -> None:
    """Save results to a JSON file."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Results saved to {path}")

def main():
    """Entry point for the correlation analysis."""
    output_file = get_env("OUTPUT_CORRELATION", "output/correlation_results.json")
    
    try:
        results = run_correlation_analysis()
        save_results(results, output_file)
        logger.info("Correlation analysis completed successfully.")
    except Exception as e:
        logger.error(f"Correlation analysis failed: {e}", exc_info=True)
        # Ensure we still output a status file if possible, or fail loudly
        raise

if __name__ == "__main__":
    main()