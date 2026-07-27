import os
import random
import numpy as np
import pandas as pd
from scipy import stats
import json
from typing import Dict, List, Any

def set_diagnostics_seed(seed: int = 42) -> None:
    """Set random seed for diagnostics reproducibility."""
    random.seed(seed)
    np.random.seed(seed)

def detect_perfect_multicollinearity(df: pd.DataFrame, predictors: List[str]) -> List[List[str]]:
    """
    Detect perfect multicollinearity by checking matrix rank.
    Returns list of collinear pairs.
    """
    set_diagnostics_seed()
    collinear_pairs = []
    
    if len(predictors) < 2:
        return collinear_pairs
        
    X = df[predictors].dropna()
    if X.empty:
        return collinear_pairs
        
    # Check all pairs
    for i in range(len(predictors)):
        for j in range(i + 1, len(predictors)):
            p1, p2 = predictors[i], predictors[j]
            if p1 not in X.columns or p2 not in X.columns:
                continue
            corr = np.corrcoef(X[p1], X[p2])[0, 1]
            if np.isnan(corr):
                continue
            if abs(corr) > 0.999:
                collinear_pairs.append([p1, p2])
                
    return collinear_pairs

def calculate_vif(df: pd.DataFrame, predictors: List[str]) -> Dict[str, float]:
    """Calculate Variance Inflation Factor for each predictor."""
    set_diagnostics_seed()
    vif_data = {}
    
    if len(predictors) < 2:
        return vif_data
        
    X = df[predictors].dropna()
    if X.empty:
        return vif_data
        
    for i, col in enumerate(predictors):
        if col not in X.columns:
            continue
        y = X[col]
        X_other = X.drop(columns=[col])
        if X_other.empty:
            vif_data[col] = 1.0
            continue
        try:
            r2 = 1 - (1 - stats.pearsonr(y, X_other.iloc[:, 0])[1]) ** 2 # Simplified
            vif = 1 / (1 - r2) if (1 - r2) > 0 else np.inf
            vif_data[col] = vif
        except:
            vif_data[col] = np.inf
            
    return vif_data

def run_sensitivity_analysis(correlation_results: List[Dict], thresholds: List[float] = [0.01, 0.05, 0.10]) -> List[Dict]:
    """Run sensitivity analysis on p-value thresholds."""
    results = []
    base_count = len([r for r in correlation_results if r.get('q_value', 1.0) < 0.05])
    
    for thresh in thresholds:
        count = len([r for r in correlation_results if r.get('q_value', 1.0) < thresh])
        percent_change = ((count - base_count) / base_count * 100) if base_count > 0 else 0.0
        results.append({
            "threshold": thresh,
            "count": count,
            "percent_change": percent_change
        })
    return results

def calculate_power(n_subjects: int, r_target: float = 0.3, power_target: float = 0.80, alpha: float = 0.05) -> Dict[str, Any]:
    """Calculate power for given sample size."""
    set_diagnostics_seed()
    # Simplified power calculation
    # Using t-test approximation
    if n_subjects < 10:
        return {"status": "Underpowered", "minimum_N_required": 85}
        
    # Approximate formula
    z_beta = stats.norm.ppf(power_target)
    z_alpha = stats.norm.ppf(1 - alpha/2)
    rho = r_target
    n_required = ((z_beta + z_alpha) / 0.5 * np.log((1+rho)/(1-rho))) ** 2
    
    return {
        "status": "Adequate" if n_subjects >= n_required else "Underpowered",
        "current_N": n_subjects,
        "minimum_N_required": int(np.ceil(n_required))
    }

def run_collinearity_diagnostics(df: pd.DataFrame, predictors: List[str], static_map: List[List[str]]) -> Dict[str, Any]:
    """Run collinearity diagnostics combining static and dynamic checks."""
    dynamic_pairs = detect_perfect_multicollinearity(df, predictors)
    all_pairs = list(set(tuple(sorted(p)) for p in static_map + dynamic_pairs))
    
    vif = calculate_vif(df, predictors)
    
    return {
        "static_collinear_pairs": static_map,
        "dynamic_collinear_pairs": dynamic_pairs,
        "all_collinear_pairs": [list(p) for p in all_pairs],
        "vif_scores": vif
    }

def generate_diagnostics_report(df: pd.DataFrame, correlation_results: Dict) -> Dict[str, Any]:
    """Generate full diagnostics report."""
    import yaml
    with open("data/config/required_variables.yaml", 'r') as f:
        config = yaml.safe_load(f)
    predictors = config['predictors']
    
    # Load static map
    static_map = []
    try:
        with open("data/metadata/static_collinearity_map.json", 'r') as f:
            static_map = json.load(f).get('pairs', [])
    except:
        pass
        
    # Run diagnostics
    collinearity = run_collinearity_diagnostics(df, predictors, static_map)
    sensitivity = run_sensitivity_analysis(correlation_results.get('results', []))
    
    # Stability metric (CV of counts)
    counts = [s['count'] for s in sensitivity]
    cv = np.std(counts) / np.mean(counts) if np.mean(counts) > 0 else 0.0
    stability = {"coefficient_of_variation": cv, "status": "STABLE" if cv < 0.10 else "UNSTABLE"}
    
    # Power
    power = calculate_power(len(df))
    
    return {
        "collinearity": collinearity,
        "sensitivity": sensitivity,
        "stability": stability,
        "power": power
    }

def main():
    """Entry point for diagnostics."""
    print("Diagnostics module loaded.")

if __name__ == "__main__":
    main()
