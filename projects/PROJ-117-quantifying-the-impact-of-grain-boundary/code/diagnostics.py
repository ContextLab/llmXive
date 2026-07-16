"""
Diagnostics module for grain boundary diffusivity analysis.

This module computes collinearity diagnostics, specifically Mutual Information (MI)
between misorientation angle and Sigma (Σ) value, to inform feature selection.
"""

import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List

import numpy as np
import pandas as pd
from scipy.stats import entropy
from sklearn.metrics import mutual_info_regression

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROCESSED_DATA_PATH = PROJECT_ROOT / "data" / "processed" / "cleaned_dataset.parquet"
REPORTS_DIR = PROJECT_ROOT / "artifacts" / "reports"
DIAGNOSTIC_REPORT_PATH = REPORTS_DIR / "collinearity_diagnostic.json"

def calculate_sigma_from_misorientation(misorientation_angle: float) -> float:
    """
    Calculate Sigma (Σ) value from misorientation angle for a specific grain boundary type.
    
    Note: This is a simplified approximation for a specific boundary type (e.g., Σ3 twin).
    In a real implementation, this would use the full CSL calculation logic.
    For the purpose of this diagnostic, we assume a relationship exists if the angle is valid.
    
    Args:
        misorientation_angle: Angle in degrees.
        
    Returns:
        Sigma value (float) or NaN if calculation fails.
    """
    if np.isnan(misorientation_angle) or misorientation_angle <= 0:
        return np.nan
    
    # Placeholder logic: In a real scenario, this would use pymatgen's CSL calculation.
    # For this diagnostic, we simulate a relationship to test the MI logic.
    # A common approximation for low-angle boundaries is Σ ≈ 180 / angle (very rough).
    # For this task, we just return a value to ensure the MI calculation can run.
    # If the real data has a 'sigma_value' column, we use that directly.
    # This function is primarily for cases where 'sigma_value' is missing but 'misorientation' exists.
    
    # Simulate a deterministic relationship for testing MI > 0
    # In reality, this should be replaced by the actual CSL calculation from T010
    try:
        # Example: For a specific boundary type, Sigma is often inversely related to angle
        # This is a placeholder to ensure the MI calculation has something to work with
        # if the real 'sigma_value' column is missing or NaN.
        # If the dataset already has 'sigma_value', this function's output is ignored.
        return 1.0 / (misorientation_angle + 1e-6) 
    except Exception:
        return np.nan

def compute_mutual_information(data: pd.DataFrame, feature_x: str, feature_y: str) -> float:
    """
    Compute Mutual Information between two features.
    
    Args:
        data: DataFrame containing the features.
        feature_x: Name of the first feature (e.g., 'misorientation_angle').
        feature_y: Name of the second feature (e.g., 'sigma_value').
        
    Returns:
        Mutual Information score (float). Returns -1.0 if calculation fails.
    """
    try:
        x = data[feature_x].dropna().values.reshape(-1, 1)
        y = data[feature_y].dropna().values
        
        if len(x) == 0 or len(y) == 0 or len(x) != len(y):
            logger.warning(f"Insufficient data for MI calculation between {feature_x} and {feature_y}.")
            return -1.0
        
        # Check for constant features
        if np.std(x) == 0 or np.std(y) == 0:
            logger.warning(f"Constant feature detected in {feature_x} or {feature_y}. MI cannot be computed.")
            return 0.0
        
        # Use sklearn's mutual_info_regression for continuous variables
        mi_score = mutual_info_regression(x, y, random_state=42, n_neighbors=min(5, len(x) - 1))
        return float(mi_score[0])
        
    except Exception as e:
        logger.error(f"Error computing Mutual Information: {e}")
        return -1.0

def run_collinearity_diagnostic() -> Dict[str, Any]:
    """
    Run the collinearity diagnostic between misorientation angle and Sigma value.
    
    Returns:
        Dictionary containing the diagnostic results.
    """
    logger.info("Starting collinearity diagnostic...")
    
    # Ensure output directory exists
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Load data
    if not PROCESSED_DATA_PATH.exists():
        error_msg = f"Error: Cleaned dataset not found at {PROCESSED_DATA_PATH}. " \
                    "Please run T011 (preprocess.py) first."
        logger.error(error_msg)
        return {
            "status": "failed",
            "message": error_msg,
            "file": str(PROCESSED_DATA_PATH)
        }
    
    try:
        data = pd.read_parquet(PROCESSED_DATA_PATH)
        logger.info(f"Loaded {len(data)} records from {PROCESSED_DATA_PATH}")
    except Exception as e:
        error_msg = f"Error loading dataset: {e}"
        logger.error(error_msg)
        return {
            "status": "failed",
            "message": error_msg
        }
    
    # Check for required columns
    required_cols = ['misorientation_angle', 'sigma_value']
    missing_cols = [col for col in required_cols if col not in data.columns]
    
    if missing_cols:
        error_msg = f"Missing required columns: {missing_cols}"
        logger.error(error_msg)
        return {
            "status": "failed",
            "message": error_msg,
            "missing_columns": missing_cols
        }
    
    # Count valid Sigma values
    valid_sigma_count = data['sigma_value'].notna().sum()
    total_count = len(data)
    
    if valid_sigma_count == 0:
        logger.warning("No valid Sigma values found in the dataset.")
        report = {
            "status": "unavailable",
            "message": "No valid Σ values in dataset after preprocessing.",
            "count": int(valid_sigma_count),
            "total_records": int(total_count)
        }
        logger.info(f"Diagnostic report saved to {DIAGNOSTIC_REPORT_PATH}")
        with open(DIAGNOSTIC_REPORT_PATH, 'w') as f:
            json.dump(report, f, indent=2)
        return report
    
    # Compute Mutual Information
    mi_score = compute_mutual_information(data, 'misorientation_angle', 'sigma_value')
    
    if mi_score < 0:
        logger.warning("Mutual Information calculation failed or returned invalid score.")
        report = {
            "status": "error",
            "message": "Mutual Information calculation failed.",
            "mi_score": None
        }
    else:
        logger.info(f"Mutual Information between misorientation_angle and sigma_value: {mi_score:.4f}")
        
        # Interpretation
        interpretation = "low"
        if mi_score > 0.8:
            interpretation = "strong"
            log_note = "MI > 0.8 indicates strong dependency; relationship is descriptive, not causal."
            logger.info(log_note)
        elif mi_score > 0.4:
            interpretation = "moderate"
        else:
            interpretation = "low"
        
        report = {
            "status": "success",
            "mi_score": float(mi_score),
            "interpretation": interpretation,
            "valid_sigma_count": int(valid_sigma_count),
            "total_records": int(total_count),
            "note": "The relationship between misorientation and Σ value is descriptive, not causal, as Σ is derived from misorientation."
        }
    
    # Save report
    try:
        with open(DIAGNOSTIC_REPORT_PATH, 'w') as f:
            json.dump(report, f, indent=2)
        logger.info(f"Diagnostic report saved to {DIAGNOSTIC_REPORT_PATH}")
    except Exception as e:
        logger.error(f"Failed to save diagnostic report: {e}")
        report["save_error"] = str(e)
    
    return report

def main():
    """Main entry point for the diagnostics script."""
    logger.info("=== Grain Boundary Collinearity Diagnostic ===")
    result = run_collinearity_diagnostic()
    logger.info(f"Diagnostic completed with status: {result.get('status', 'unknown')}")
    return result

if __name__ == "__main__":
    main()