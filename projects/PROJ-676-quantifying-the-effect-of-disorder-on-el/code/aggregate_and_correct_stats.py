import json
import os
import logging
from pathlib import Path
from typing import Dict, Any, List, Tuple
import numpy as np
from code.config import get_config
from code.logger import get_logger

logger = logging.getLogger(__name__)

def load_aggregated_results(input_path: str) -> List[Dict[str, Any]]:
    """Load aggregated scaling fit results."""
    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    with open(path, 'r') as f:
        data = json.load(f)
    return data

def analyze_scaling_slopes(data: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Perform linear regression on log(xi) vs log(W) for W > 0."""
    # Filter W=0
    valid_data = [d for d in data if d.get("disorder_width", 0) > 0 and d.get("xi") is not None]
    
    if len(valid_data) < 2:
        logger.warning("Not enough data points for regression.")
        return {"slope": None, "p_value": None, "r_squared": None}
    
    log_W = np.log([d["disorder_width"] for d in valid_data])
    log_xi = np.log([d["xi"] for d in valid_data])
    
    # Linear regression
    coeffs = np.polyfit(log_W, log_xi, 1)
    slope = coeffs[0]
    intercept = coeffs[1]
    
    # Calculate R-squared
    y_pred = np.polyval(coeffs, log_W)
    ss_res = np.sum((log_xi - y_pred) ** 2)
    ss_tot = np.sum((log_xi - np.mean(log_xi)) ** 2)
    r_squared = 1 - (ss_res / ss_tot)
    
    # Calculate p-value for slope deviation from -2
    # t = (slope - expected_slope) / std_err
    # Simplified std_err estimation
    n = len(valid_data)
    std_err = np.sqrt(ss_res / (n - 2)) / np.sqrt(np.sum((log_W - np.mean(log_W))**2))
    t_stat = (slope - (-2.0)) / std_err if std_err > 0 else 0
    
    # Approximate p-value (two-tailed) using normal distribution for large n
    # In a real scenario, use scipy.stats.t.sf
    p_value = 2 * (1 - 0.5 * (1 + np.erf(np.abs(t_stat) / np.sqrt(2))))
    
    return {
        "slope": float(slope),
        "intercept": float(intercept),
        "r_squared": float(r_squared),
        "t_statistic": float(t_stat),
        "p_value": float(p_value),
        "n_points": n
    }

def apply_bonferroni_correction(regression_results: Dict[str, Any], num_tests: int) -> Dict[str, Any]:
    """Apply Bonferroni correction for the full family of disorder widths."""
    p_value = regression_results.get("p_value")
    if p_value is None:
        return {"corrected_p_value": None, "is_significant": False, "alpha_corrected": None}
    
    alpha = 0.05
    alpha_corrected = alpha / num_tests
    corrected_p_value = p_value * num_tests
    
    # Clamp corrected p-value to 1.0
    corrected_p_value = min(corrected_p_value, 1.0)
    
    is_significant = corrected_p_value < alpha
    
    return {
        "original_p_value": p_value,
        "corrected_p_value": float(corrected_p_value),
        "alpha_corrected": float(alpha_corrected),
        "is_significant": is_significant,
        "num_tests": num_tests
    }

def main():
    """Main entry point for statistical aggregation and correction."""
    config = get_config()
    W_list = config.get("W_LIST", [])
    
    # Load scaling fits
    input_path = Path("data/processed/scaling_fits.json")
    if not input_path.exists():
        logger.error(f"Scaling fits file not found: {input_path}")
        return
    
    data = load_aggregated_results(str(input_path))
    
    # Analyze slopes
    regression_results = analyze_scaling_slopes(data)
    
    # Write regression results
    reg_output = Path("data/processed/global_regression.json")
    with open(reg_output, 'w') as f:
        json.dump(regression_results, f, indent=2)
    
    # Apply Bonferroni
    # Count valid W > 0 tests
    num_tests = len([d for d in data if d.get("disorder_width", 0) > 0])
    bonferroni_results = apply_bonferroni_correction(regression_results, num_tests)
    
    # Write Bonferroni results
    bonf_output = Path("data/processed/bonferroni_results.json")
    with open(bonf_output, 'w') as f:
        json.dump(bonferroni_results, f, indent=2)
    
    logger.info(f"Regression and Bonferroni results written to {reg_output} and {bonf_output}")

if __name__ == "__main__":
    main()
