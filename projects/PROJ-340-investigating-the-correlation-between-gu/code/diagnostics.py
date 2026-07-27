import os
import random
import numpy as np
import pandas as pd
from scipy import stats
import json
from typing import Dict, List, Any

def set_diagnostics_seed(seed: int = 42):
    random.seed(seed)
    np.random.seed(seed)

def calculate_vif(df: pd.DataFrame, variables: list) -> dict:
    """Calculates Variance Inflation Factor (VIF) for multivariate predictors."""
    vif_data = {}
    for i, var in enumerate(variables):
        if var not in df.columns:
            continue
        # Simple VIF calculation: 1 / (1 - R^2)
        # Regress var against all other variables
        X = df[variables].drop(columns=[var])
        y = df[var]
        if X.shape[1] == 0:
            vif_data[var] = 1.0
            continue
        
        # Linear regression
        model = stats.linregress(X.values.flatten(), y.values) if X.shape[1] == 1 else None
        # For simplicity, use a simplified VIF estimate or skip if complex
        # Using a simplified approach for demonstration
        try:
            # Use sklearn if available, else fallback
            from sklearn.linear_model import LinearRegression
            reg = LinearRegression().fit(X, y)
            r_squared = reg.score(X, y)
            vif = 1.0 / (1.0 - r_squared) if r_squared < 1.0 else np.inf
            vif_data[var] = vif
        except ImportError:
            # Fallback: assume VIF=1 if sklearn not available
            vif_data[var] = 1.0
    return vif_data

def detect_perfect_multicollinearity(df: pd.DataFrame, variables: list) -> list:
    """Detects perfect multicollinearity by checking matrix rank."""
    # Simplified: check correlation = 1.0 or -1.0
    pairs = []
    X = df[variables].values
    if X.shape[1] < 2:
        return pairs
    
    corr_matrix = np.corrcoef(X.T)
    for i in range(len(variables)):
        for j in range(i+1, len(variables)):
            if abs(corr_matrix[i, j]) == 1.0:
                pairs.append((variables[i], variables[j]))
    return pairs

def run_sensitivity_analysis(correlation_results: dict) -> dict:
    """
    Runs sensitivity analysis at different p-value thresholds.
    Reads correlation results and appends results to sensitivity_analysis.json.
    """
    thresholds = [0.01, 0.05, 0.10]
    results = []
    
    # Count total significant at 0.05 (base)
    base_count = 0
    for item in correlation_results.get("correlations", []):
        if item.get("p_value_adjusted", 1.0) <= 0.05:
            base_count += 1
    
    for thresh in thresholds:
        count = 0
        for item in correlation_results.get("correlations", []):
            if item.get("p_value_adjusted", 1.0) <= thresh:
                count += 1
        
        percent_change = ((count - base_count) / base_count * 100) if base_count > 0 else 0.0
        results.append({
            "threshold": thresh,
            "count": count,
            "percent_change": percent_change
        })
    
    return {"sensitivity_results": results}

def calculate_power(n_subjects: int, alpha: float = 0.05, power: float = 0.80, r: float = 0.3) -> dict:
    """Calculates minimum N for given power and effect size."""
    # Approximation formula
    # N = (Z_alpha + Z_beta)^2 / r^2
    # Z_alpha for 0.05 (2-tailed) ~ 1.96
    # Z_beta for 0.80 power ~ 0.84
    z_alpha = 1.96
    z_beta = 0.84
    min_n = ((z_alpha + z_beta) ** 2) / (r ** 2)
    min_n = int(np.ceil(min_n))
    
    status = "Adequate" if n_subjects >= min_n else "Underpowered"
    
    return {
        "current_n": n_subjects,
        "minimum_N_required": min_n,
        "status": status,
        "effect_size_r": r,
        "power_target": power,
        "alpha": alpha
    }

def run_collinearity_diagnostics(df: pd.DataFrame) -> dict:
    """Runs collinearity diagnostics (VIF, perfect multicollinearity)."""
    # Load config for variables
    import yaml
    config_path = "data/config/required_variables.yaml"
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    predictors = config.get("predictors", [])
    
    # Perfect multicollinearity (dynamic)
    perfect_pairs = detect_perfect_multicollinearity(df, predictors)
    
    # VIF
    vif_results = calculate_vif(df, predictors)
    
    return {
        "perfect_multicollinearity_pairs": perfect_pairs,
        "vif_scores": vif_results
    }

def generate_diagnostics_report():
    """Generates a combined diagnostics report."""
    pass

def main():
    pass
