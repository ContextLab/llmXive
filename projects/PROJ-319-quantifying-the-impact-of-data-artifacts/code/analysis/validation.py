"""
Validation: Apply corrections and check residuals.
"""
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
import numpy as np

def apply_corrections(model_file: Path, data_file: Path) -> Dict[str, Any]:
    """
    Apply calibration corrections to the data.
    """
    model_file = Path(model_file)
    data_file = Path(data_file)
    
    with open(model_file) as f:
        models = json.load(f)
    
    # Read data
    import csv
    data = []
    with open(data_file, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append(row)
    
    corrected_data = []
    for row in data:
        artifact_type = row.get('artifact_type')
        artifact_value = float(row.get('artifact_value', 0))
        bias = float(row.get('bias', 0))
        
        correction = 0
        if artifact_type == 'noise' and 'ellipticity_model' in models:
            model = models['ellipticity_model']
            if model['type'] == 'linear':
                correction = model['slope'] * artifact_value + model['intercept']
            elif model['type'] == 'quadratic':
                coeffs = model['coefficients']
                correction = coeffs[0] * artifact_value**2 + coeffs[1] * artifact_value + coeffs[2]
        
        elif artifact_type == 'saturation' and 'asymmetry_model' in models:
            model = models['asymmetry_model']
            if model['type'] == 'linear':
                correction = model['slope'] * artifact_value + model['intercept']
            elif model['type'] == 'quadratic':
                coeffs = model['coefficients']
                correction = coeffs[0] * artifact_value**2 + coeffs[1] * artifact_value + coeffs[2]
        
        residual_bias = bias - correction
        corrected_data.append({
            **row,
            'correction_applied': correction,
            'residual_bias': residual_bias
        })
    
    return {'corrected_data': corrected_data}

def validate_residuals(model_file: Path, data_file: Path, output_json: Path) -> None:
    """
    Validate that residual bias is non-significant.
    """
    result = apply_corrections(model_file, data_file)
    corrected_data = result['corrected_data']
    
    residuals = [d['residual_bias'] for d in corrected_data]
    mean_residual = np.mean(residuals)
    std_residual = np.std(residuals)
    
    # Simple t-test against 0
    from scipy import stats
    t_stat, p_value = stats.ttest_1samp(residuals, 0)
    
    report = {
        'mean_residual': float(mean_residual),
        'std_residual': float(std_residual),
        't_statistic': float(t_stat),
        'p_value': float(p_value),
        'is_significant': p_value < 0.05
    }
    
    output_json = Path(output_json)
    output_json.parent.mkdir(parents=True, exist_ok=True)
    with open(output_json, 'w') as f:
        json.dump(report, f, indent=2)
    
    logging.info(f"Residual validation report written to {output_json}")

def main():
    root = Path(__file__).resolve().parent.parent.parent
    model_file = root / "data" / "processed" / "calibration_functions.json"
    data_file = root / "data" / "processed" / "aggregated_bias.csv"
    output_json = root / "data" / "validation" / "residual_report.json"
    validate_residuals(model_file, data_file, output_json)

if __name__ == "__main__":
    main()
