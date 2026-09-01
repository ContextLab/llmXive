"""
Statistical validation module for null-model comparison.

Implements SC-002: One-sample t-test comparing cross-validation RMSE scores
against the null model (dummy regressor) test RMSE.
"""

import json
import os
import sys
import logging
from typing import Dict, Any

import numpy as np
from scipy import stats

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Paths relative to project root
CV_METRICS_PATH = "data/models/cv_metrics.json"
NULL_RMSE_PATH = "data/models/null_model_rmse.json"
OUTPUT_PATH = "data/models/statistical_comparison.json"

def load_json(filepath: str) -> Any:
    """Load and parse a JSON file."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Required file not found: {filepath}")
    with open(filepath, 'r') as f:
        return json.load(f)

def save_json(filepath: str, data: Dict[str, Any]) -> None:
    """Save data to a JSON file."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w') as f:
        json.dump(data, f, indent=2)

def run_statistical_test() -> Dict[str, Any]:
    """
    Perform one-sample t-test (SC-002) comparing CV RMSE scores against null model RMSE.
    
    Returns:
        Dict containing p_value, t_statistic, and sc002_met boolean.
    """
    logger.info("Loading cross-validation metrics from %s", CV_METRICS_PATH)
    cv_metrics = load_json(CV_METRICS_PATH)
    
    if "fold_scores" not in cv_metrics or not isinstance(cv_metrics["fold_scores"], list):
        raise ValueError("Invalid cv_metrics.json: missing 'fold_scores' list")
    
    cv_rmse_scores = np.array(cv_metrics["fold_scores"])
    logger.info("Loaded %d CV fold RMSE scores: %s", len(cv_rmse_scores), cv_rmse_scores)
    
    if len(cv_rmse_scores) < 2:
        raise ValueError("Need at least 2 CV fold scores for t-test")
    
    logger.info("Loading null model RMSE from %s", NULL_RMSE_PATH)
    null_metrics = load_json(NULL_RMSE_PATH)
    
    if "rmse" not in null_metrics:
        raise ValueError("Invalid null_model_rmse.json: missing 'rmse' key")
    
    null_rmse = float(null_metrics["rmse"])
    logger.info("Null model test RMSE: %.4f", null_rmse)
    
    # Perform one-sample t-test (two-sided)
    # H0: The mean of CV RMSE scores is equal to the null model RMSE
    # H1: The mean of CV RMSE scores is NOT equal to the null model RMSE
    logger.info("Performing one-sample t-test (scipy.stats.ttest_1samp)")
    t_statistic, p_value = stats.ttest_1samp(cv_rmse_scores, null_rmse)
    
    logger.info("t-statistic: %.6f", t_statistic)
    logger.info("p-value: %.6f", p_value)
    
    # Determine if SC-002 is met (p < 0.05 means we reject H0)
    sc002_met = p_value < 0.05
    logger.info("SC-002 met (p < 0.05): %s", sc002_met)
    
    result = {
        "p_value": float(p_value),
        "t_statistic": float(t_statistic),
        "sc002_met": sc002_met,
        "cv_mean_rmse": float(np.mean(cv_rmse_scores)),
        "cv_std_rmse": float(np.std(cv_rmse_scores, ddof=1)),
        "null_rmse": null_rmse,
        "method": "one-sample t-test (two-sided) comparing 5-fold CV RMSE vs null model RMSE"
    }
    
    logger.info("Saving results to %s", OUTPUT_PATH)
    save_json(OUTPUT_PATH, result)
    
    return result

def main():
    """Entry point for the statistical test script."""
    try:
        result = run_statistical_test()
        logger.info("Statistical test completed successfully.")
        logger.info("SC-002 Status: %s (p-value: %.6f)", 
                   "PASSED" if result["sc002_met"] else "FAILED", 
                   result["p_value"])
        return 0
    except Exception as e:
        logger.error("Statistical test failed: %s", str(e))
        return 1

if __name__ == "__main__":
    sys.exit(main())