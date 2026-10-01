"""
Regression models for calibration functions.
"""
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
import numpy as np
from scipy import stats

def fit_calibration_models(input_csv: Path, output_json: Path) -> None:
    """
    Fit calibration models (linear/polynomial) to aggregated bias data.
    Uses AIC for model selection.
    Output: data/processed/calibration_functions.json
    """
    import csv
    input_csv = Path(input_csv)
    output_json = Path(output_json)
    
    # Read aggregated data
    # Expected columns: artifact_type, artifact_value, bias
    data = []
    with open(input_csv, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append(row)
    
    # Group by artifact type
    ellipticity_data = []
    asymmetry_data = []
    
    for row in data:
        if row.get('artifact_type') == 'noise':
            ellipticity_data.append((float(row['artifact_value']), float(row['bias'])))
        elif row.get('artifact_type') == 'saturation':
            asymmetry_data.append((float(row['artifact_value']), float(row['bias'])))
    
    models = {}
    
    # Fit ellipticity model (noise -> bias)
    if ellipticity_data:
        x, y = zip(*ellipticity_data)
        x, y = np.array(x), np.array(y)
        
        # Linear fit
        slope, intercept, r, p, std_err = stats.linregress(x, y)
        residuals = y - (slope * x + intercept)
        ss_res = np.sum(residuals**2)
        ss_tot = np.sum((y - np.mean(y))**2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
        n = len(x)
        k = 2 # slope + intercept
        aic_linear = n * np.log(ss_res / n) + 2 * k
        
        # Quadratic fit (if n is large enough)
        if n >= 3:
            coeffs = np.polyfit(x, y, 2)
            p2 = np.poly1d(coeffs)
            residuals2 = y - p2(x)
            ss_res2 = np.sum(residuals2**2)
            k2 = 3
            aic_quad = n * np.log(ss_res2 / n) + 2 * k2
            
            if aic_quad < aic_linear:
                models['ellipticity_model'] = {
                    'type': 'quadratic',
                    'coefficients': coeffs.tolist(),
                    'r_squared': float(1 - (ss_res2 / ss_tot)) if ss_tot != 0 else 0
                }
            else:
                models['ellipticity_model'] = {
                    'type': 'linear',
                    'slope': float(slope),
                    'intercept': float(intercept),
                    'r_squared': float(r_squared)
                }
        else:
            models['ellipticity_model'] = {
                'type': 'linear',
                'slope': float(slope),
                'intercept': float(intercept),
                'r_squared': float(r_squared)
            }
    
    # Fit asymmetry model (saturation -> bias)
    if asymmetry_data:
        x, y = zip(*asymmetry_data)
        x, y = np.array(x), np.array(y)
        
        slope, intercept, r, p, std_err = stats.linregress(x, y)
        residuals = y - (slope * x + intercept)
        ss_res = np.sum(residuals**2)
        ss_tot = np.sum((y - np.mean(y))**2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
        n = len(x)
        k = 2
        aic_linear = n * np.log(ss_res / n) + 2 * k
        
        if n >= 3:
            coeffs = np.polyfit(x, y, 2)
            p2 = np.poly1d(coeffs)
            residuals2 = y - p2(x)
            ss_res2 = np.sum(residuals2**2)
            k2 = 3
            aic_quad = n * np.log(ss_res2 / n) + 2 * k2
            
            if aic_quad < aic_linear:
                models['asymmetry_model'] = {
                    'type': 'quadratic',
                    'coefficients': coeffs.tolist(),
                    'r_squared': float(1 - (ss_res2 / ss_tot)) if ss_tot != 0 else 0
                }
            else:
                models['asymmetry_model'] = {
                    'type': 'linear',
                    'slope': float(slope),
                    'intercept': float(intercept),
                    'r_squared': float(r_squared)
                }
        else:
            models['asymmetry_model'] = {
                'type': 'linear',
                'slope': float(slope),
                'intercept': float(intercept),
                'r_squared': float(r_squared)
            }
    
    output_json.parent.mkdir(parents=True, exist_ok=True)
    with open(output_json, 'w') as f:
        json.dump(models, f, indent=2)
    
    logging.info(f"Calibration models written to {output_json}")

def main():
    root = Path(__file__).resolve().parent.parent.parent
    input_csv = root / "data" / "processed" / "aggregated_bias.csv"
    output_json = root / "data" / "processed" / "calibration_functions.json"
    fit_calibration_models(input_csv, output_json)

if __name__ == "__main__":
    main()
