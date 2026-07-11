"""
Linear Mixed-Effects Models for analyzing attention metrics vs recall accuracy.

Implements memory-efficient loading and fits LMMs using statsmodels.
"""
import os
import sys
import argparse
import json
from pathlib import Path
from typing import List, Dict, Any, Optional

import pandas as pd
import numpy as np
import statsmodels.api as sm
from statsmodels.regression.mixed_linear_model import MixedLM

# Import project utilities
from utils.logger import get_logger
from utils.config import get_project_root, get_data_path, get_output_path
from analysis.memory_loader import load_data_streaming, get_available_ram_gb

logger = get_logger(__name__)

def load_processed_data(file_path: str) -> pd.DataFrame:
    """
    Loads processed data using memory-efficient strategies.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Processed data not found: {file_path}")
    
    logger.info(f"Loading processed data from {file_path}...")
    # Use the memory loader to ensure we stay under RAM limits
    return load_data_streaming(file_path, target_ram_gb=6.0)

def fit_lmm_for_combination(
    data: pd.DataFrame,
    metric: str,
    valence: str,
    formula: str = "recall_accuracy ~ {metric} + (1|participant_id)"
) -> Dict[str, Any]:
    """
    Fits a Linear Mixed-Effects model for a specific metric and valence combination.
    
    Args:
        data: The DataFrame containing the data.
        metric: The name of the attention metric column.
        valence: The valence category.
        formula: The R-style formula for the model.
        
    Returns:
        A dictionary containing model results (coef, p-value, etc.).
    """
    # Filter data for the specific valence
    subset = data[data['valence'] == valence].copy()
    
    if len(subset) < 10:
        logger.warning(f"Insufficient data for valence {valence} and metric {metric}. Skipping.")
        return {
            "metric": metric,
            "valence": valence,
            "coef": np.nan,
            "p_raw": np.nan,
            "status": "insufficient_data"
        }
    
    # Ensure required columns exist
    if metric not in subset.columns or 'recall_accuracy' not in subset.columns:
        logger.error(f"Missing columns for {metric} or recall_accuracy in valence {valence}")
        return {
            "metric": metric,
            "valence": valence,
            "coef": np.nan,
            "p_raw": np.nan,
            "status": "missing_columns"
        }
    
    # Drop NaNs
    subset = subset.dropna(subset=[metric, 'recall_accuracy', 'participant_id'])
    
    if len(subset) < 10:
        logger.warning(f"Too few rows after dropping NaNs for {metric}/{valence}. Skipping.")
        return {
            "metric": metric,
            "valence": valence,
            "coef": np.nan,
            "p_raw": np.nan,
            "status": "insufficient_data_after_dropna"
        }
    
    # Construct formula dynamically if needed, but using the passed one is safer
    # Assuming the passed formula is pre-formatted or we format it here
    try:
        formatted_formula = formula.format(metric=metric)
        endog = subset['recall_accuracy']
        exog = subset[metric]
        groups = subset['participant_id']
        
        # Fit the model
        # statsmodels MixedLM requires exog to be a DataFrame or array
        model = MixedLM(endog, exog, groups=groups)
        result = model.fit(reml=False)
        
        # Extract coefficients
        # The fixed effects are in result.fe_params
        # The first coefficient is usually the intercept, second is the slope for the metric
        if len(result.fe_params) >= 2:
            coef = result.fe_params.iloc[1] # Slope for the metric
        else:
            coef = result.fe_params.iloc[0] # If only intercept (unlikely with formula)
        
        # P-values are in result.pvalues
        # Map the metric name to the p-value
        p_raw = result.pvalues.get(metric, np.nan)
        
        return {
            "metric": metric,
            "valence": valence,
            "coef": float(coef),
            "p_raw": float(p_raw),
            "status": "success"
        }
        
    except Exception as e:
        logger.error(f"Error fitting LMM for {metric}/{valence}: {e}")
        return {
            "metric": metric,
            "valence": valence,
            "coef": np.nan,
            "p_raw": np.nan,
            "status": f"error: {str(e)}"
        }

def run_lmm_analysis(
    data: pd.DataFrame,
    metrics: List[str],
    valences: List[str]
) -> List[Dict[str, Any]]:
    """
    Runs LMM analysis for all combinations of metrics and valences.
    
    Args:
        data: The full DataFrame.
        metrics: List of attention metric column names.
        valences: List of valence categories.
        
    Returns:
        List of result dictionaries.
    """
    results = []
    logger.info(f"Starting LMM analysis for {len(metrics)} metrics and {len(valences)} valences.")
    
    for metric in metrics:
        for valence in valences:
            logger.info(f"Fitting model for {metric} vs {valence}...")
            res = fit_lmm_for_combination(data, metric, valence)
            results.append(res)
            
            # Force GC periodically during long loops
            if len(results) % 10 == 0:
                import gc
                gc.collect()
    
    return results

def save_results(results: List[Dict[str, Any]], output_path: str):
    """
    Saves LMM results to a CSV file.
    """
    df_results = pd.DataFrame(results)
    df_results.to_csv(output_path, index=False)
    logger.info(f"Saved LMM results to {output_path}")

def main():
    """
    CLI entry point for LMM analysis.
    Usage: python code/analysis/lmm_model.py --input <path> --output <path>
    """
    parser = argparse.ArgumentParser(description="Run LMM Analysis")
    parser.add_argument("--input", type=str, required=True, help="Path to processed data CSV")
    parser.add_argument("--output", type=str, required=True, help="Path to output results CSV")
    parser.add_argument("--metrics", type=str, nargs='+', default=['fixation_duration', 'saccade_amplitude', 'gaze_distribution'], help="Attention metrics to analyze")
    parser.add_argument("--valences", type=str, nargs='+', default=['positive', 'negative', 'neutral'], help="Valence categories")
    
    args = parser.parse_args()
    
    # Resolve paths
    project_root = get_project_root()
    if not os.path.isabs(args.input):
        data_path = get_data_path()
        input_path = os.path.join(data_path, args.input)
    else:
        input_path = args.input
        
    if not os.path.isabs(args.output):
        output_dir = get_output_path()
        output_path = os.path.join(output_dir, args.output)
    else:
        output_path = args.output
        
    # Ensure output directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    try:
        data = load_processed_data(input_path)
        results = run_lmm_analysis(data, args.metrics, args.valences)
        save_results(results, output_path)
        print("LMM Analysis completed successfully.")
        sys.exit(0)
    except Exception as e:
        logger.error(f"LMM Analysis failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
