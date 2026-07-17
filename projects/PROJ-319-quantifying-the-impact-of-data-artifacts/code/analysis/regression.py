import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
import numpy as np
from scipy import stats
from code.config import get_project_root

logger = logging.getLogger(__name__)

def fit_calibration_models():
    """
    Fit linear/polynomial models linking artifact intensity to bias.
    Uses AIC for model selection (linear vs quadratic).
    Produces data/processed/calibration_functions.json.
    """
    root = get_project_root()
    processed_dir = root / "data" / "processed"
    
    # Load aggregated bias data
    agg_path = processed_dir / "aggregated_bias.csv"
    if not agg_path.exists():
        # Fallback to individual files if aggregated not present
        # For this task, we assume aggregation is done by T041
        logger.error("Aggregated bias data not found.")
        return

    # Read CSV
    data = []
    with open(agg_path, "r") as f:
        import csv
        reader = csv.DictReader(f)
        for row in reader:
            data.append(row)
    
    # Separate noise and saturation data
    noise_data = [r for r in data if r.get("type") == "noise"]
    sat_data = [r for r in data if r.get("type") == "saturation"]
    
    models = {}
    
    # Fit noise model
    if noise_data:
        x = np.array([float(r["artifact_value"]) for r in noise_data])
        y = np.array([float(r["bias"]) for r in noise_data])
        
        # Linear fit
        slope_l, intercept_l, r_l, p_l, se_l = stats.linregress(x, y)
        # Quadratic fit
        coeffs_q = np.polyfit(x, y, 2)
        # Calculate AIC (simplified)
        # AIC = 2k - 2ln(L)
        # For OLS, we can use RSS
        rss_l = np.sum((y - (slope_l * x + intercept_l))**2)
        rss_q = np.sum((y - np.polyval(coeffs_q, x))**2)
        n = len(x)
        aic_l = n * np.log(rss_l/n) + 2*2
        aic_q = n * np.log(rss_q/n) + 2*3
        
        if aic_q < aic_l:
            models["ellipticity_model"] = {
                "type": "quadratic",
                "coefficients": coeffs_q.tolist(),
                "aic": aic_q
            }
        else:
            models["ellipticity_model"] = {
                "type": "linear",
                "slope": slope_l,
                "intercept": intercept_l,
                "aic": aic_l
            }
    
    # Fit saturation model
    if sat_data:
        x = np.array([float(r["artifact_value"]) for r in sat_data])
        y = np.array([float(r["bias"]) for r in sat_data])
        
        slope_l, intercept_l, r_l, p_l, se_l = stats.linregress(x, y)
        coeffs_q = np.polyfit(x, y, 2)
        rss_l = np.sum((y - (slope_l * x + intercept_l))**2)
        rss_q = np.sum((y - np.polyval(coeffs_q, x))**2)
        n = len(x)
        aic_l = n * np.log(rss_l/n) + 2*2
        aic_q = n * np.log(rss_q/n) + 2*3
        
        if aic_q < aic_l:
            models["asymmetry_model"] = {
                "type": "quadratic",
                "coefficients": coeffs_q.tolist(),
                "aic": aic_q
            }
        else:
            models["asymmetry_model"] = {
                "type": "linear",
                "slope": slope_l,
                "intercept": intercept_l,
                "aic": aic_l
            }
    
    # Save models
    out_path = processed_dir / "calibration_functions.json"
    with open(out_path, "w") as f:
        json.dump(models, f, indent=2)
    
    logger.info(f"Calibration models saved to {out_path}")
    return models

def main():
    fit_calibration_models()
