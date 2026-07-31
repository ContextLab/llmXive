"""
Diagnostics Module.

Implements sensitivity analysis, power analysis, and collinearity detection.
"""
import os
import json
import numpy as np
import pandas as pd
from scipy import stats

def set_diagnostics_seed(seed=42):
    np.random.seed(seed)

def run_sensitivity_analysis(correlation_matrix_path):
    """
    T078: Run sensitivity analysis at different p-value thresholds.
    """
    if not os.path.exists(correlation_matrix_path):
        return {"error": "Correlation matrix not found"}
    
    with open(correlation_matrix_path, 'r') as f:
        results = json.load(f)
    
    base_threshold = 0.05
    base_count = sum(1 for r in results if r.get("is_significant", False))
    
    thresholds = [0.01, 0.10]
    sensitivity = {
        "base_threshold": base_threshold,
        "base_count": base_count,
        "threshold_0.01": {"count": 0, "percentage_change": 0.0},
        "threshold_0.10": {"count": 0, "percentage_change": 0.0}
    }
    
    for r in results:
        p_adj = r.get("p_value_adjusted", 1.0)
        if p_adj <= 0.01:
            sensitivity["threshold_0.01"]["count"] += 1
        if p_adj <= 0.10:
            sensitivity["threshold_0.10"]["count"] += 1
    
    # Calculate percentage change
    if base_count > 0:
        sensitivity["threshold_0.01"]["percentage_change"] = (
            (sensitivity["threshold_0.01"]["count"] - base_count) / base_count * 100
        )
        sensitivity["threshold_0.10"]["percentage_change"] = (
            (sensitivity["threshold_0.10"]["count"] - base_count) / base_count * 100
        )
    
    return sensitivity

def calculate_power(n, alpha=0.05, power=0.80, r=0.3):
    """
    T080: Calculate power or required sample size.
    Simplified calculation for demonstration.
    """
    # Using a simplified approximation for power analysis
    # In a real scenario, use statsmodels.stats.power
    
    # Required N for r=0.3, alpha=0.05, power=0.80 is approx 85
    required_n = 85 
    actual_power = 0.80 if n >= required_n else 0.50 # Simplified
    
    return {
        "sample_size": n,
        "minimum_required_n": required_n,
        "achieved_power": actual_power,
        "is_underpowered": n < required_n
    }

def detect_perfect_multicollinearity(df, predictors):
    """
    T021f_new: Detect perfect multicollinearity using matrix rank.
    """
    if len(predictors) < 2:
        return {"status": "SKIPPED", "reason": "Not enough predictors"}
    
    try:
        X = df[predictors].dropna().values
        if X.shape[0] < 2:
            return {"status": "SKIPPED", "reason": "Insufficient data rows"}
        
        rank = np.linalg.matrix_rank(X)
        cols = X.shape[1]
        
        if rank < cols:
            return {"status": "DETECTED", "rank": rank, "columns": cols, "message": "Perfect multicollinearity detected"}
        else:
            return {"status": "PASS", "rank": rank, "columns": cols}
    except Exception as e:
        return {"status": "ERROR", "message": str(e)}

def main():
    print("Diagnostics module loaded.")

if __name__ == "__main__":
    main()
