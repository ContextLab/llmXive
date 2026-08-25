"""
Sensitivity Analysis for Regression Results.

This module performs a sweep of significance thresholds and applies
Benjamini-Hochberg FDR correction to the hypothesis tests derived from
the regression analysis.

It specifically targets the 6 hypothesis tests:
- O/Fe vs Dst
- O/Fe vs Kp
- He/H vs Dst
- He/H vs Kp
- C/O vs Dst
- C/O vs Kp
"""
import os
import sys
import json
import argparse
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd
import numpy as np

# Import from project utilities and analysis modules
from utils.logging import get_logger, AnalysisError, log_duration
from config import get_config
from analysis.regression import get_coupling_function_columns

logger = get_logger(__name__)

# Constants for the specific hypothesis tests
COMPOSITION_RATIOS = ['O/Fe', 'He/H', 'C/O']
GEOMAGNETIC_INDICES = ['Dst', 'Kp']
THRESHOLDS_TO_SWEEP = [0.01, 0.05, 0.10]

def load_regression_results(results_path: Path) -> pd.DataFrame:
    """
    Load regression results from the artifacts directory.
    Expects a CSV file containing coefficients, p-values, and VIFs.
    """
    if not results_path.exists():
        raise AnalysisError(f"Regression results file not found: {results_path}")
    
    df = pd.read_csv(results_path)
    logger.info(f"Loaded regression results with {len(df)} rows from {results_path}")
    return df

def get_coefficient_stats(df: pd.DataFrame, model_type: str) -> pd.DataFrame:
    """
    Extract statistics for a specific model type (baseline or full).
    Returns a DataFrame with predictor, coefficient, p-value, and VIF.
    """
    if model_type not in df.columns:
        raise AnalysisError(f"Model type '{model_type}' not found in regression results.")
    
    # Filter for the specific model type
    model_df = df[df['model_type'] == model_type].copy()
    
    # Ensure we have the necessary columns
    required_cols = ['predictor', 'coefficient', 'p_value', 'vif']
    missing_cols = [c for c in required_cols if c not in model_df.columns]
    if missing_cols:
        raise AnalysisError(f"Missing required columns in regression results: {missing_cols}")
    
    return model_df[['predictor', 'coefficient', 'p_value', 'vif']]

def apply_benjamini_hochberg(p_values: pd.Series, alpha: float = 0.05) -> Tuple[pd.Series, pd.Series]:
    """
    Apply Benjamini-Hochberg FDR correction to a series of p-values.
    
    Parameters
    ----------
    p_values : pd.Series
        Series of raw p-values.
    alpha : float
        Significance level for FDR control.
        
    Returns
    -------
    Tuple[pd.Series, pd.Series]
        (adjusted_p_values, boolean_mask_significant)
    """
    if len(p_values) == 0:
        return pd.Series(dtype=float), pd.Series(dtype=bool)
    
    n = len(p_values)
    # Sort p-values
    sorted_indices = p_values.argsort()
    sorted_p = p_values.iloc[sorted_indices]
    
    # Calculate adjusted p-values (BH procedure)
    # rank goes from 1 to n
    ranks = np.arange(1, n + 1)
    adjusted_p = (sorted_p * n) / ranks
    
    # Ensure monotonicity (cumulative min from the end)
    # This is required for the BH procedure to be valid
    adjusted_p = np.minimum.accumulate(adjusted_p[::-1])[::-1]
    
    # Clip to [0, 1]
    adjusted_p = np.clip(adjusted_p, 0, 1)
    
    # Re-order back to original indices
    adjusted_p_final = pd.Series(adjusted_p, index=p_values.index)
    
    # Determine significance
    significant = adjusted_p_final <= alpha
    
    return adjusted_p_final, significant

def run_sensitivity_analysis(
    results_df: pd.DataFrame, 
    thresholds: List[float] = THRESHOLDS_TO_SWEEP
) -> Dict[str, Any]:
    """
    Run sensitivity analysis across multiple significance thresholds.
    
    This function:
    1. Extracts p-values for the 6 specific hypothesis tests (Composition x Index).
    2. Applies Benjamini-Hochberg FDR correction for each threshold.
    3. Reports which predictors are significant at each threshold.
    
    Parameters
    ----------
    results_df : pd.DataFrame
        The full regression results DataFrame.
    thresholds : List[float]
        List of alpha levels to test.
        
    Returns
    -------
    Dict[str, Any]
        Dictionary containing the sensitivity analysis results.
    """
    logger.info("Starting sensitivity analysis...")
    
    # We focus on the 'full' model as it contains the composition ratios
    # alongside coupling functions.
    full_model_stats = get_coefficient_stats(results_df, 'full')
    
    # Filter for the specific composition predictors of interest
    composition_predictors = [f"{ratio}_{idx}" for ratio in COMPOSITION_RATIOS for idx in GEOMAGNETIC_INDICES]
    # Note: The actual column names in regression might be 'O/Fe' etc. if the target is Dst/Kp
    # Let's assume the regression output has predictors named like 'O/Fe' when predicting Dst,
    # or 'O/Fe' when predicting Kp. We need to handle the structure of the regression output.
    # Based on typical multivariate regression outputs in this pipeline:
    # If the model predicts Dst, predictors are [Coupling, O/Fe, He/H, C/O]
    # If the model predicts Kp, predictors are [Coupling, O/Fe, He/H, C/O]
    # The 'predictor' column in results_df likely contains the name of the variable.
    # We need to identify rows where predictor is one of the composition ratios.
    
    composition_rows = full_model_stats[full_model_stats['predictor'].isin(COMPOSITION_RATIOS)].copy()
    
    if len(composition_rows) == 0:
        logger.warning("No composition ratio predictors found in the full model results.")
        # Fallback: try to find them if they are named differently or if the model structure is different
        # But per spec, we expect O/Fe, He/H, C/O.
        return {"error": "No composition predictors found", "details": full_model_stats.columns.tolist()}

    results = {
        "thresholds": thresholds,
        "hypothesis_tests": [],
        "summary": {}
    }
    
    # We need to group by target variable (Dst vs Kp) to apply BH correction per target?
    # Or per the whole set of 6 tests? The spec says "apply Benjamini-Hochberg FDR correction 
    # to the 6 hypothesis tests". This implies a global correction across all 6.
    # However, usually one tests O/Fe->Dst, O/Fe->Kp separately. 
    # The spec lists them as 6 distinct tests. We will apply BH across the set of 6 p-values.
    
    # Check if the dataframe has a 'target' column or if we need to infer from context.
    # Assuming the regression output has a 'target' column indicating Dst or Kp.
    if 'target' in composition_rows.columns:
        targets = composition_rows['target'].unique()
    else:
        # If no target column, we assume the rows are already separated or we treat all 6 together.
        # Let's assume the standard output format from regression.py includes 'target'.
        # If not, we proceed with all found composition predictors as the set of 6.
        targets = ['Combined'] # Fallback
        
    # If we have multiple targets, we might need to run BH per target (3 tests per target) 
    # or globally (6 tests). The spec says "to the 6 hypothesis tests", implying a global set.
    # We will collect all 6 p-values and apply BH once.
    
    all_p_values = composition_rows['p_value'].values
    all_predictors = composition_rows['predictor'].values
    
    # If we have fewer than 6, we proceed with what we have, but log it.
    if len(all_p_values) != 6:
        logger.warning(f"Expected 6 hypothesis tests (3 ratios x 2 indices), found {len(all_p_values)}. Proceeding with available data.")
    
    for alpha in thresholds:
        adjusted_p, significant = apply_benjamini_hochberg(
            pd.Series(all_p_values, index=all_predictors), 
            alpha=alpha
        )
        
        # Identify significant predictors
        sig_predictors = adjusted_p[significant].index.tolist()
        
        threshold_result = {
            "alpha": alpha,
            "significant_predictors": sig_predictors,
            "count": len(sig_predictors),
            "all_adjusted_p_values": adjusted_p.to_dict()
        }
        results["hypothesis_tests"].append(threshold_result)
        
        logger.info(f"Threshold {alpha}: {len(sig_predictors)} significant predictors ({sig_predictors})")
    
    # Summary of variation
    # Count how many thresholds each predictor is significant in
    predictor_significance_count = {p: 0 for p in all_predictors}
    for test in results["hypothesis_tests"]:
        for p in test["significant_predictors"]:
            predictor_significance_count[p] += 1
    
    results["summary"] = {
        "total_tests": len(all_p_values),
        "predictors_stability": predictor_significance_count,
        "thresholds_tested": thresholds
    }
    
    return results

def save_sensitivity_results(results: Dict[str, Any], output_path: Path) -> None:
    """Save the sensitivity analysis results to a JSON file."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Sensitivity analysis results saved to {output_path}")

def main():
    """Main entry point for the sensitivity analysis script."""
    parser = argparse.ArgumentParser(description="Run sensitivity analysis on regression results.")
    parser.add_argument("--input", type=str, required=True, help="Path to regression results CSV.")
    parser.add_argument("--output", type=str, required=True, help="Path to save sensitivity results JSON.")
    parser.add_argument("--thresholds", type=str, default="0.01,0.05,0.10", 
                        help="Comma-separated list of significance thresholds.")
    
    args = parser.parse_args()
    
    try:
        # Parse thresholds
        thresholds = [float(x.strip()) for x in args.thresholds.split(',')]
        
        # Load results
        input_path = Path(args.input)
        results_df = load_regression_results(input_path)
        
        # Run analysis
        analysis_results = run_sensitivity_analysis(results_df, thresholds)
        
        # Save results
        output_path = Path(args.output)
        save_sensitivity_results(analysis_results, output_path)
        
        print(f"Sensitivity analysis completed successfully. Results saved to {output_path}")
        
    except Exception as e:
        logger.error(f"Error during sensitivity analysis: {e}", exc_info=True)
        raise AnalysisError(f"Sensitivity analysis failed: {e}")

if __name__ == "__main__":
    main()