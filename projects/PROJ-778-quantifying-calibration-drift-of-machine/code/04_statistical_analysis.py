"""
Statistical Analysis for Calibration Drift (User Story 3).

This script performs:
1. Weighted Least Squares (WLS) regression of ECE vs. Year.
2. Spearman rank correlation between covariate shift and calibration error.
3. BIC-based change-point detection.
4. Saving results to data/processed/regression_results.json.
"""

import json
import logging
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

import numpy as np
from scipy import stats
from statsmodels.regression.linear_model import WLS
from statsmodels.tools import add_constant
import ruptures as rpt

# Import from local utils
from utils.config import get_path, ensure_directories, get_config_dict
from utils.shift_detection import detect_change_point_bic

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def load_metrics_records() -> List[Dict[str, Any]]:
    """
    Load the metrics records computed in T024.
    Expects data/processed/metrics_records.json.
    """
    metrics_path = get_path("data", "processed", "metrics_records.json")
    if not metrics_path.exists():
        raise FileNotFoundError(
            f"Metrics records not found at {metrics_path}. "
            "Please run 03_evaluation.py first."
        )
    
    with open(metrics_path, "r") as f:
        records = json.load(f)
    
    logger.info(f"Loaded {len(records)} metric records.")
    return records


def prepare_wls_data(records: List[Dict[str, Any]], model_type: str) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Prepare data for WLS regression: Year (X) vs ECE (Y).
    Returns: X (years), Y (ECE), weights (1/ECE_variance approx 1/ECE or constant if missing).
    For WLS, we use weights inversely proportional to variance. 
    A common heuristic for calibration error variance is proportional to the error itself.
    We will use weights = 1 / (ece + epsilon) to down-weight high-error years if variance is higher,
    or simply use constant weights if we assume homoscedasticity for the sake of the specific WLS implementation 
    requested (Plan override).
    
    However, the task explicitly requests WLS for heteroscedasticity. 
    We will estimate variance from the binning strategy differences if available, 
    or use a simple heuristic: weight = 1 / (ece^2 + epsilon) or similar.
    Given the data structure, we might not have per-year variance estimates directly.
    We will use a standard approach: weights = 1 / (y^2 + small_epsilon) if y varies significantly,
    or simply 1.0 if we want to avoid instability.
    
    Let's use a robust weight: 1 / (ece + 1e-6) assuming variance scales with mean.
    """
    years = []
    ece_values = []
    
    for record in records:
        if record.get("model_type") == model_type:
            years.append(record["year"])
            ece_values.append(record["ece_10"]) # Use ECE_10 as primary metric per task description
    
    if len(years) < 2:
        raise ValueError(f"Not enough data points for model {model_type} to perform regression.")
    
    X = np.array(years)
    Y = np.array(ece_values)
    
    # Weights for WLS: Inverse of variance estimate.
    # If we assume variance ~ mean^2 (common for errors), weight = 1/Y^2.
    # If we assume variance ~ mean, weight = 1/Y.
    # To avoid division by zero, add epsilon.
    # Let's use 1 / (Y + epsilon) as a standard stabilizing weight for positive errors.
    epsilon = 1e-6
    weights = 1.0 / (Y + epsilon)
    
    return X, Y, weights


def run_wls_regression(X: np.ndarray, Y: np.ndarray, weights: np.ndarray) -> Dict[str, float]:
    """
    Fit Weighted Least Squares (WLS) model: Y = slope * X + intercept.
    Returns dict with slope, intercept, p_value, r_squared.
    """
    X_const = add_constant(X)
    
    try:
        wls_model = WLS(Y, X_const, weights=weights)
        wls_results = wls_model.fit()
        
        slope = wls_results.params[1]
        intercept = wls_results.params[0]
        p_value = wls_results.pvalues[1] # p-value for the slope (year)
        r_squared = wls_results.rsquared
        
        logger.info(f"WLS Results: slope={slope:.6f}, intercept={intercept:.6f}, p={p_value:.6f}, r2={r_squared:.6f}")
        
        return {
            "slope": float(slope),
            "intercept": float(intercept),
            "p_value": float(p_value),
            "r_squared": float(r_squared)
        }
    except Exception as e:
        logger.error(f"WLS regression failed: {e}")
        raise


def compute_spearman_correlation(records: List[Dict[str, Any]], model_type: str) -> Dict[str, Any]:
    """
    Compute Spearman rank correlation between covariate shift (PCA shift) and calibration error (ECE).
    Verify robustness across binning strategies (5, 10, 20).
    """
    pca_shifts = []
    ece_5s = []
    ece_10s = []
    ece_20s = []
    
    for record in records:
        if record.get("model_type") == model_type:
            # We need a single shift metric and multiple ECE metrics
            # Using PCA shift as the covariate shift metric
            if "pca_shift" in record and "ece_5" in record:
                pca_shifts.append(record["pca_shift"])
                ece_5s.append(record["ece_5"])
                ece_10s.append(record["ece_10"])
                ece_20s.append(record["ece_20"])
    
    if len(pca_shifts) < 2:
        logger.warning("Insufficient data for Spearman correlation.")
        return {
            "rho_5": None, "rho_10": None, "rho_20": None,
            "rho_diff_5_10": None, "rho_diff_10_20": None, "max_rho_diff": None,
            "p_value": None
        }
    
    rho_5, p_5 = stats.spearmanr(pca_shifts, ece_5s)
    rho_10, p_10 = stats.spearmanr(pca_shifts, ece_10s)
    rho_20, p_20 = stats.spearmanr(pca_shifts, ece_20s)
    
    # Compute differences
    diff_5_10 = abs(rho_5 - rho_10)
    diff_10_20 = abs(rho_10 - rho_20)
    max_diff = max(diff_5_10, diff_10_20)
    
    logger.info(f"Spearman Correlation: rho_5={rho_5:.4f}, rho_10={rho_10:.4f}, rho_20={rho_20:.4f}")
    logger.info(f"Robustness Check: max_rho_diff={max_diff:.4f} (Threshold: 0.1)")
    
    return {
        "rho_5": float(rho_5),
        "rho_10": float(rho_10),
        "rho_20": float(rho_20),
        "rho_diff_5_10": float(diff_5_10),
        "rho_diff_10_20": float(diff_10_20),
        "max_rho_diff": float(max_diff),
        "p_value": float(p_5) # Using p_5 as representative, or could average
    }


def run_change_point_detection(records: List[Dict[str, Any]], model_type: str) -> Optional[int]:
    """
    Perform BIC-based change-point detection on ECE time series.
    Returns the year of the change point if found, else None.
    """
    years = []
    ece_values = []
    
    for record in records:
        if record.get("model_type") == model_type:
            years.append(record["year"])
            ece_values.append(record["ece_10"])
    
    if len(years) < 3:
        logger.warning("Insufficient data for change-point detection.")
        return None
    
    # Use the utility function from utils.shift_detection
    # The function expects a list of metrics (values) and returns the change point index or year
    # We pass the ECE values as the metric series
    change_point_year = detect_change_point_bic(ece_values, alpha=0.05, years=years)
    
    if change_point_year is not None:
        logger.info(f"Change point detected at year: {change_point_year}")
    else:
        logger.info("No significant change point detected.")
        
    return change_point_year


def run_analysis_pipeline():
    """
    Main entry point for statistical analysis.
    """
    config = get_config_dict()
    ensure_directories()
    
    # Load data
    records = load_metrics_records()
    
    # Define models to analyze
    models = ["LogisticRegression", "RandomForest"] # Adjust based on actual model names in data
    
    all_results = []
    
    for model_type in models:
        logger.info(f"Processing model: {model_type}")
        
        # 1. WLS Regression
        try:
            X, Y, weights = prepare_wls_data(records, model_type)
            regression_results = run_wls_regression(X, Y, weights)
        except Exception as e:
            logger.error(f"Failed to run WLS for {model_type}: {e}")
            regression_results = {"slope": None, "intercept": None, "p_value": None, "r_squared": None}
        
        # 2. Spearman Correlation
        correlation_results = compute_spearman_correlation(records, model_type)
        
        # 3. Change Point Detection
        change_point_year = run_change_point_detection(records, model_type)
        
        # Combine results
        model_analysis = {
            "model_type": model_type,
            "regression": regression_results,
            "correlation": correlation_results,
            "change_point_year": change_point_year
        }
        all_results.append(model_analysis)
        
        # Update the first matching record in the output list with p_value_wls and change_point_year
        # This satisfies the schema requirement for T005/T024 fields in the final record if we were updating them,
        # but here we are generating a summary. The task asks to save results to regression_results.json.
    
    # Save results
    output_path = get_path("data", "processed", "regression_results.json")
    with open(output_path, "w") as f:
        json.dump(all_results, f, indent=2)
    
    logger.info(f"Analysis complete. Results saved to {output_path}")
    return all_results


def main():
    run_analysis_pipeline()


if __name__ == "__main__":
    main()
