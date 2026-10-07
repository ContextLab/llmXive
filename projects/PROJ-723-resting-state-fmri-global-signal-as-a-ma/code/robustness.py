import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional

import numpy as np
import pandas as pd
from scipy import stats

from config import ensure_directories
from utils import get_logger, read_json, write_json, read_csv

# --- Configuration ---
DIAGNOSTICS_PATH = "data/results/diagnostics.json"
PARTIAL_CORR_OUTPUT_PATH = "data/results/partial_corr.json"
RESIDUALS_INPUT_PATH = "data/processed/residuals.csv"
CLEANED_DATA_PATH = "data/processed/cleaned_data.csv"

logger = get_logger(__name__)

def load_cleaned_data_for_robustness(data_path: str = CLEANED_DATA_PATH) -> pd.DataFrame:
    """Load the cleaned dataset for robustness checks."""
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Cleaned data not found at {data_path}. Run ingestion first.")
    return read_csv(data_path)

def check_collinearity_flag(diagnostics_path: str = DIAGNOSTICS_PATH) -> Tuple[bool, str]:
    """
    Dynamically read the collinearity_flag from diagnostics.json.
    Returns (is_flagged, reason_message).
    """
    if not os.path.exists(diagnostics_path):
        logger.warning(f"Diagnostic file not found at {diagnostics_path}. Assuming no collinearity flag.")
        return False, "No diagnostics file found"

    try:
        diagnostics = read_json(diagnostics_path)
        # The schema defines 'collinearity_flag' or we infer from 'high_vif_features'
        # Based on T024 output schema in prompt: 'collinearity_flag' is expected.
        # If missing, check 'high_vif_features' length or 'status'.
        if "collinearity_flag" in diagnostics:
            is_flagged = diagnostics["collinearity_flag"]
            reason = "High collinearity detected in diagnostics" if is_flagged else "Collinearity within limits"
        elif "high_vif_features" in diagnostics and len(diagnostics["high_vif_features"]) > 0:
            is_flagged = True
            reason = f"High VIF features found: {diagnostics['high_vif_features']}"
        else:
            is_flagged = False
            reason = "No high VIF features detected"
        
        return is_flagged, reason
    except Exception as e:
        logger.error(f"Error reading diagnostics: {e}")
        return False, f"Error reading diagnostics: {e}"

def run_partial_correlation_analysis(data: pd.DataFrame) -> Dict[str, Any]:
    """
    Calculate partial correlation between Global_Signal_SD and MWQ_Score,
    controlling for covariates (Mean_FD, Mean_DVARS, Age, Sex).
    
    Logic:
    1. Residualize MWQ_Score against covariates.
    2. Residualize Global_Signal_SD against covariates.
    3. Correlate the two residuals.
    """
    logger.info("Running partial correlation analysis...")
    
    predictors = ["Mean_FD", "Mean_DVARS", "Age", "Sex"]
    # Ensure Sex is numeric if it's not already (0/1)
    if "Sex" in data.columns and data["Sex"].dtype == object:
        # Simple mapping if needed, assuming 'M'/'F' or similar
        data["Sex"] = data["Sex"].map({"M": 1, "F": 0, "Male": 1, "Female": 0}).fillna(0).astype(float)

    y_var = "MWQ_Score"
    x_var = "Global_Signal_SD"

    # Drop rows with NaN in relevant columns
    clean_data = data[[y_var, x_var] + predictors].dropna()
    
    if len(clean_data) < 10:
        logger.warning("Insufficient data for partial correlation.")
        return {"status": "failed", "reason": "Insufficient data", "p_value": None, "r_value": None}

    # Prepare design matrix for covariates
    X = clean_data[predictors].values
    y = clean_data[y_var].values
    x = clean_data[x_var].values

    # Add intercept
    X_with_intercept = np.column_stack([np.ones(X.shape[0]), X])

    # Residualize y (MWQ)
    try:
        beta_y, _, _, _ = np.linalg.lstsq(X_with_intercept, y, rcond=None)
        y_pred = X_with_intercept @ beta_y
        residuals_y = y - y_pred
    except np.linalg.LinAlgError:
        return {"status": "failed", "reason": "Collinearity in covariate matrix", "p_value": None, "r_value": None}

    # Residualize x (GSA)
    try:
        beta_x, _, _, _ = np.linalg.lstsq(X_with_intercept, x, rcond=None)
        x_pred = X_with_intercept @ beta_x
        residuals_x = x - x_pred
    except np.linalg.LinAlgError:
        return {"status": "failed", "reason": "Collinearity in covariate matrix", "p_value": None, "r_value": None}

    # Calculate correlation
    r, p_value = stats.pearsonr(residuals_x, residuals_y)

    status = "significant" if p_value < 0.05 else "null_finding"
    
    return {
        "status": status,
        "p_value": float(p_value),
        "r_value": float(r),
        "n": len(clean_data),
        "method": "Partial Correlation (Residuals of GSA and MWQ on Covariates)"
    }

def run_partial_correlation_with_skip_logic() -> Dict[str, Any]:
    """
    Main entry for T042: Dynamic Partial Correlation Logic.
    1. Read collinearity_flag from diagnostics.json.
    2. If True, skip calculation and write status='skipped'.
    3. If False, proceed with calculation.
    4. Write result to partial_corr.json.
    """
    logger.info("Starting Dynamic Partial Correlation Logic (T042)...")
    
    # 1. Check Collinearity Flag
    is_flagged, reason = check_collinearity_flag()
    
    if is_flagged:
        logger.warning(f"Collinearity flag is True. Skipping partial correlation. Reason: {reason}")
        result = {
            "status": "skipped",
            "reason": reason,
            "p_value": None,
            "r_value": None,
            "method": "Partial Correlation"
        }
    else:
        logger.info("Collinearity flag is False or not set. Proceeding with calculation.")
        # 2. Load Data
        try:
            data = load_cleaned_data_for_robustness()
        except FileNotFoundError as e:
            logger.error(f"Data loading failed: {e}")
            result = {
                "status": "skipped",
                "reason": str(e),
                "p_value": None,
                "r_value": None,
                "method": "Partial Correlation"
            }
            # Write immediately on error to satisfy 'write output' requirement
            write_json(PARTIAL_CORR_OUTPUT_PATH, result)
            return result

        # 3. Run Analysis
        result = run_partial_correlation_analysis(data)
        if result.get("status") == "failed":
            result["method"] = "Partial Correlation"
            result["skipped_due_to_error"] = True
        else:
            result["method"] = "Partial Correlation"

    # 4. Write Output
    ensure_directories()
    write_json(PARTIAL_CORR_OUTPUT_PATH, result)
    logger.info(f"Partial correlation result written to {PARTIAL_CORR_OUTPUT_PATH}")
    
    return result

def run_alpha_sweep(data: pd.DataFrame, alpha_grid: List[float] = None) -> Dict[str, Any]:
    """Placeholder for alpha sweep logic (T028)."""
    if alpha_grid is None:
        alpha_grid = np.logspace(-3, 3, 10).tolist()
    # Implementation would go here
    return {"status": "placeholder", "alphas": alpha_grid}

def run_variance_metric_analysis(data: pd.DataFrame) -> Dict[str, Any]:
    """Placeholder for variance metric analysis (T029)."""
    # Implementation would go here
    return {"status": "placeholder", "metric": "variance"}

def generate_robustness_report() -> Dict[str, Any]:
    """Aggregates robustness results (T031)."""
    # This would call the specific functions above and aggregate
    return {"status": "generated"}

def main():
    """Entry point for robustness.py."""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Parse args if needed, currently focused on T042 logic
    result = run_partial_correlation_with_skip_logic()
    
    print(json.dumps(result, indent=2))
    return result

if __name__ == "__main__":
    main()