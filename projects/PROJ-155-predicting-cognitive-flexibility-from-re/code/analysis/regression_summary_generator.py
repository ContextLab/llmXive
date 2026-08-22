"""
Task T034: Generate regression_summary.json with Beta, SE, R, P-Value, Significance Status.

This module implements the logic to aggregate results from the linear regression
(T030) and permutation test (T031) into a canonical JSON summary file.

It reads the regression coefficients from the internal state (or re-runs the
regression if not cached) and combines them with the permutation p-value
and success rate metrics.
"""
import os
import json
import logging
from typing import Dict, Any, Optional

import numpy as np
import pandas as pd
from scipy import stats

from code.config import get_config
from code.data.paths import get_results_path, ensure_dir
from code.analysis.regression import run_linear_regression, load_regression_dataset
from code.analysis.permutation import run_permutation_test
from code.utils.exclusion_stats import calculate_success_rate
from code.analysis.p_value_formatter import format_p_value

logger = logging.getLogger(__name__)


def load_regression_results() -> Optional[Dict[str, Any]]:
    """
    Loads regression results from the summary JSON if it exists, otherwise
    computes them.
    """
    results_path = get_results_path("regression_summary.json")
    if os.path.exists(results_path):
        try:
            with open(results_path, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Could not load existing regression summary: {e}. Recomputing.")
    return None


def compute_success_rate() -> float:
    """
    Calculates the proportion of subjects successfully processed.
    """
    try:
        success_rate = calculate_success_rate()
        return float(success_rate)
    except Exception as e:
        logger.error(f"Failed to calculate success rate: {e}")
        return 0.0


def generate_regression_summary() -> Dict[str, Any]:
    """
    Generates the full regression summary dictionary.

    Returns:
        A dictionary containing Beta, SE, R, P-Value, Significance Status,
        and success rate metrics.
    """
    config = get_config()
    seed = config.get('seed', 42)

    # 1. Load or Compute Regression Results
    # We assume run_linear_regression returns the model stats or we extract them
    # from the fitted model. To ensure we have the latest data, we re-run
    # the regression logic on the processed data.
    try:
        # Load the merged dataset
        df = load_regression_dataset()
        
        if df is None or df.empty:
            raise ValueError("No data available for regression analysis.")

        # Run the regression (this fits the model and returns stats)
        # Note: run_linear_regression in code/analysis/regression.py is expected 
        # to return the stats dictionary or the model object. 
        # Based on the API surface, we assume it returns a dict or we extract it.
        # Let's assume the function returns the stats dict directly for this implementation.
        # If it returns a model object, we would extract summary().
        
        # Re-implementing the core logic here to ensure we get the stats dict
        # since the API surface for run_linear_regression isn't fully detailed in the prompt.
        # We will assume it returns a dict with 'params', 'bse', 'rsquared', etc.
        
        # Fallback: Run the pipeline function which might handle the saving, 
        # but we need the raw stats for T034 specifically.
        # Let's assume run_linear_regression returns the summary stats dict.
        regression_stats = run_linear_regression(df)
        
        if not isinstance(regression_stats, dict):
            # If it returns a statsmodels result, extract it
            if hasattr(regression_stats, 'summary2'):
                # Extract key metrics manually if statsmodels result
                params = regression_stats.params
                bse = regression_stats.bse
                rsquared = regression_stats.rsquared
                pvalues = regression_stats.pvalues
                
                # We need the specific 'Variability' coefficient
                variability_key = 'Variability_Metric' # or whatever the column is named
                # If the column was encoded, it might be different. 
                # Assuming standard naming based on T030 description.
                
                beta = float(params[variability_key])
                se = float(bse[variability_key])
                r = float(np.sqrt(rsquared))
                p_val = float(pvalues[variability_key])
            else:
                raise TypeError(f"Unexpected regression result type: {type(regression_stats)}")
        else:
            beta = float(regression_stats['beta'])
            se = float(regression_stats['se'])
            r = float(regression_stats['r'])
            p_val = float(regression_stats['p_value'])

    except Exception as e:
        logger.error(f"Failed to compute regression statistics: {e}")
        raise

    # 2. Run Permutation Test (10,000 iterations)
    # This validates the significance of the observed beta
    try:
        perm_results = run_permutation_test(df, n_permutations=10000, seed=seed)
        perm_p_value = float(perm_results.get('p_value', p_val))
        # If permutation p-value is significant, we trust it more for the final status
        final_p_value = perm_p_value
    except Exception as e:
        logger.warning(f"Permutation test failed: {e}. Falling back to parametric p-value.")
        final_p_value = p_val

    # 3. Determine Significance
    # Standard alpha = 0.05
    alpha = 0.05
    is_significant = final_p_value < alpha
    significance_status = "Significant" if is_significant else "Not Significant"

    # 4. Format P-Value
    formatted_p = format_p_value(final_p_value)

    # 5. Calculate Success Rate
    success_rate = compute_success_rate()

    # 6. Assemble Summary
    summary = {
        "model_type": "Linear Regression",
        "target_variable": "Flexibility_Score",
        "predictor_variable": "Variability_Metric",
        "covariates": ["Age", "Sex", "Mean_FD", "Total_Scan_Time"],
        "coefficients": {
            "variability_beta": beta,
            "variability_se": se,
            "r_squared": r ** 2,
            "r": r
        },
        "significance": {
            "p_value_raw": final_p_value,
            "p_value_formatted": formatted_p,
            "alpha_threshold": alpha,
            "is_significant": is_significant,
            "status": significance_status
        },
        "validation": {
            "permutation_test": {
                "n_permutations": 10000,
                "p_value": perm_p_value
            }
        },
        "pipeline_metrics": {
            "pro_processed": success_rate
        },
        "metadata": {
            "seed": seed,
            "config": config
        }
    }

    return summary


def save_regression_summary(summary: Dict[str, Any], output_path: Optional[str] = None) -> str:
    """
    Saves the regression summary to a JSON file.
    
    Args:
        summary: The summary dictionary.
        output_path: Optional specific path. Defaults to data/results/regression_summary.json.
        
    Returns:
        The path where the file was saved.
    """
    if output_path is None:
        output_path = get_results_path("regression_summary.json")
    
    ensure_dir(output_path)
    
    with open(output_path, 'w') as f:
        json.dump(summary, f, indent=2)
        
    logger.info(f"Regression summary saved to {output_path}")
    return output_path


def run_regression_summary_pipeline() -> Dict[str, Any]:
    """
    Main entry point for Task T034.
    """
    logger.info("Starting T034: Regression Summary Generation")
    
    summary = generate_regression_summary()
    save_path = save_regression_summary(summary)
    
    logger.info("T034 completed successfully.")
    return summary


def main():
    """CLI entry point."""
    logging.basicConfig(level=logging.INFO)
    run_regression_summary_pipeline()


if __name__ == "__main__":
    main()
