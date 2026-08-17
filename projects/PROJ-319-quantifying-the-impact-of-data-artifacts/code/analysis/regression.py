"""
Regression and Calibration module.
Implements T027 (Fit Calibration Models).
"""
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

import numpy as np
from scipy import stats
from code.config import (
    get_project_root, 
    DATA_PROCESSED,
    CALIBRATION_FUNCTIONS_FILE
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def fit_calibration_models():
    """
    Fit linear/polynomial models linking artifact intensity to bias.
    Uses AIC for model selection (T044).
    Output: data/processed/calibration_functions.json
    """
    root = get_project_root()
    processed_dir = DATA_PROCESSED
    output_file = processed_dir / CALIBRATION_FUNCTIONS_FILE
    
    # Load noise stats
    noise_stats_file = processed_dir / "noise_stats.csv"
    sat_stats_file = processed_dir / "saturation_stats.csv"
    
    models = {
        "ellipticity_model": {}, # Proxy: noise -> intensity bias
        "asymmetry_model": {}    # Proxy: saturation -> intensity bias
    }
    
    # Fit Noise Model (Linear)
    if noise_stats_file.exists():
        # Read data
        data = []
        with open(noise_stats_file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                data.append({
                    "x": float(row['sigma']),
                    "y": float(row['mean_bias'])
                })
        
        if data:
            x = [d['x'] for d in data]
            y = [d['y'] for d in data]
            
            # Linear
            slope, intercept, r, p, se = stats.linregress(x, y)
            aic_linear = len(x) * np.log(np.var(y - (slope * np.array(x) + intercept))) + 2 * 2
            
            # Quadratic (if enough points)
            if len(x) >= 3:
                coeffs = np.polyfit(x, y, 2)
                p_fit = np.poly1d(coeffs)
                residuals = y - p_fit(x)
                aic_quad = len(x) * np.log(np.var(residuals)) + 2 * 3
                
                if aic_quad < aic_linear:
                    models["ellipticity_model"] = {
                        "type": "quadratic",
                        "coefficients": coeffs.tolist(),
                        "aic": float(aic_quad)
                    }
                else:
                    models["ellipticity_model"] = {
                        "type": "linear",
                        "slope": float(slope),
                        "intercept": float(intercept),
                        "aic": float(aic_linear)
                    }
            else:
                models["ellipticity_model"] = {
                    "type": "linear",
                    "slope": float(slope),
                    "intercept": float(intercept),
                    "aic": float(aic_linear)
                }
    
    # Fit Saturation Model
    if sat_stats_file.exists():
        # Simplified: use the single slope from stats
        # In a real scenario, we would aggregate raw data
        models["asymmetry_model"] = {
            "type": "linear",
            "slope": 0.0, # Placeholder, would be calculated from raw sweep data
            "intercept": 0.0
        }
    
    # Save
    with open(output_file, 'w') as f:
        json.dump(models, f, indent=2)
    
    logger.info(f"Calibration models saved to {output_file}")

def main():
    """Main entry point for regression."""
    logger.info("Starting regression analysis...")
    fit_calibration_models()
    logger.info("Regression analysis complete.")

if __name__ == "__main__":
    main()
