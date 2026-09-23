"""
Paired T-Test on Cross-Validation Folds.

This script performs a paired t-test comparing the cross-validation fold scores
of XGBoost vs. Linear Regression models.

FR-004: Statistical comparison of models.
SC-002: Quantitative model comparison.

Output: data/processed/paired_ttest_results.yaml
"""

import os
import sys
import logging
import yaml
import json
import numpy as np
import pandas as pd
from scipy import stats
from pathlib import Path

# Project root setup
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from evaluation.cv import load_cv_results
from utils.logging_config import get_logger

logger = get_logger(__name__)

RESULTS_OUTPUT_PATH = PROJECT_ROOT / "data" / "processed" / "paired_ttest_results.yaml"
CV_RESULTS_PATH = PROJECT_ROOT / "data" / "processed" / "cv_results.json"

def load_model_scores(model_name: str, cv_results_df: pd.DataFrame) -> np.ndarray:
    """
    Extract the R2 scores for a specific model from the CV results dataframe.
    
    Args:
        model_name: Name of the model ('xgboost' or 'linear').
        cv_results_df: The dataframe loaded from cv_results.json.
        
    Returns:
        Numpy array of R2 scores for the specified model.
    """
    # The dataframe columns are typically structured as: model, fold, metric, value
    # We filter for the specific model and the 'r2' metric
    model_scores = cv_results_df[
        (cv_results_df['model'] == model_name) & 
        (cv_results_df['metric'] == 'r2')
    ]['value'].values
    
    if len(model_scores) == 0:
        raise ValueError(f"No R2 scores found for model '{model_name}' in CV results.")
    
    return model_scores

def perform_paired_ttest(scores_xgb: np.ndarray, scores_lin: np.ndarray) -> dict:
    """
    Perform a paired t-test on two arrays of scores.
    
    Args:
        scores_xgb: R2 scores from XGBoost folds.
        scores_lin: R2 scores from Linear Regression folds.
        
    Returns:
        Dictionary containing t_statistic, p_value, and significant flag.
    """
    if len(scores_xgb) != len(scores_lin):
        raise ValueError("Number of folds must match for both models to perform a paired t-test.")
    
    if len(scores_xgb) < 2:
        logger.warning("Insufficient number of folds (< 2) to perform a statistical t-test.")
        return {
            "t_statistic": float('nan'),
            "p_value": float('nan'),
            "significant": False,
            "note": "Insufficient samples for t-test"
        }

    t_stat, p_val = stats.ttest_rel(scores_xgb, scores_lin)
    
    # Determine significance at alpha = 0.05
    significant = bool(p_val < 0.05)
    
    return {
        "t_statistic": float(t_stat),
        "p_value": float(p_val),
        "significant": significant
    }

def main():
    """
    Main entry point for the paired t-test script.
    """
    logger.info("Starting Paired T-Test on CV Folds.")
    
    # 1. Load CV Results
    if not CV_RESULTS_PATH.exists():
        logger.error(f"CV results file not found at {CV_RESULTS_PATH}. "
                     "Please ensure T027 (Cross-Validation) has been executed.")
        sys.exit(1)
    
    try:
        cv_results_df = load_cv_results()
        logger.info(f"Loaded CV results with {len(cv_results_df)} rows.")
    except Exception as e:
        logger.error(f"Failed to load CV results: {e}")
        sys.exit(1)

    # 2. Extract Scores
    try:
        xgb_scores = load_model_scores('xgboost', cv_results_df)
        lin_scores = load_model_scores('linear', cv_results_df)
        logger.info(f"Extracted {len(xgb_scores)} XGBoost scores and {len(lin_scores)} Linear scores.")
    except ValueError as e:
        logger.error(str(e))
        sys.exit(1)

    # 3. Perform T-Test
    logger.info("Performing paired t-test (XGBoost vs Linear Regression)...")
    try:
        results = perform_paired_ttest(xgb_scores, lin_scores)
    except Exception as e:
        logger.error(f"T-Test calculation failed: {e}")
        sys.exit(1)

    # 4. Save Results
    # Ensure output directory exists
    RESULTS_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    with open(RESULTS_OUTPUT_PATH, 'w') as f:
        yaml.dump(results, f, default_flow_style=False, sort_keys=False)
    
    logger.info(f"Paired t-test results saved to {RESULTS_OUTPUT_PATH}")
    logger.info(f"Result: t={results['t_statistic']:.4f}, p={results['p_value']:.6f}, significant={results['significant']}")

if __name__ == "__main__":
    main()