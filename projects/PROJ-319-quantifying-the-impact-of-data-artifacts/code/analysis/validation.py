import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
import numpy as np
from code.config import get_project_root

logger = logging.getLogger(__name__)

def apply_corrections():
    """
    Apply inverse correction to bias and compute residuals.
    """
    root = get_project_root()
    processed_dir = root / "data" / "processed"
    
    # Load calibration models
    model_path = processed_dir / "calibration_functions.json"
    if not model_path.exists():
        logger.error("Calibration models not found.")
        return

    with open(model_path, "r") as f:
        models = json.load(f)
    
    # Load aggregated bias data
    agg_path = processed_dir / "aggregated_bias.csv"
    if not agg_path.exists():
        logger.error("Aggregated bias data not found.")
        return
    
    import csv
    data = []
    with open(agg_path, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append(row)
    
    corrected_data = []
    for row in data:
        artifact_type = row.get("type")
        artifact_value = float(row["artifact_value"])
        bias = float(row["bias"])
        
        correction = 0.0
        if artifact_type == "noise" and "ellipticity_model" in models:
            model = models["ellipticity_model"]
            if model["type"] == "linear":
                correction = model["slope"] * artifact_value + model["intercept"]
            else:
                coeffs = model["coefficients"]
                correction = coeffs[0]*artifact_value**2 + coeffs[1]*artifact_value + coeffs[2]
        elif artifact_type == "saturation" and "asymmetry_model" in models:
            model = models["asymmetry_model"]
            if model["type"] == "linear":
                correction = model["slope"] * artifact_value + model["intercept"]
            else:
                coeffs = model["coefficients"]
                correction = coeffs[0]*artifact_value**2 + coeffs[1]*artifact_value + coeffs[2]
        
        residual = bias - correction
        row["corrected_bias"] = residual
        corrected_data.append(row)
    
    # Save corrected data
    out_path = processed_dir / "corrected_bias.csv"
    with open(out_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=corrected_data[0].keys())
        writer.writeheader()
        writer.writerows(corrected_data)
    
    logger.info(f"Corrected bias saved to {out_path}")
    return corrected_data

def validate_residuals():
    """
    Validate residual bias is non-significant.
    """
    root = get_project_root()
    processed_dir = root / "data" / "processed"
    
    corrected_path = processed_dir / "corrected_bias.csv"
    if not corrected_path.exists():
        logger.error("Corrected bias data not found.")
        return
    
    import csv
    residuals = []
    with open(corrected_path, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            residuals.append(float(row["corrected_bias"]))
    
    if not residuals:
        return
    
    # Test if mean residual is significantly different from 0
    from scipy import stats
    t_stat, p_val = stats.ttest_1samp(residuals, 0.0)
    
    report = {
        "n_samples": len(residuals),
        "mean_residual": float(np.mean(residuals)),
        "std_residual": float(np.std(residuals)),
        "t_statistic": float(t_stat),
        "p_value": float(p_val),
        "significant": p_val < 0.05
    }
    
    report_path = processed_dir / "validation_report.json"
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"Validation report saved to {report_path}")
    return report

def main():
    apply_corrections()
    validate_residuals()
