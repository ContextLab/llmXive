"""
Diagnostics Module.

Implements sensitivity analysis, power analysis, and collinearity detection.
"""
import os
import json
import numpy as np
import pandas as pd
from scipy import stats
import json
from pathlib import Path
from typing import Dict, Any, Optional, List

# Seed management for reproducibility
DIAGNOSTICS_SEED = 42

def set_diagnostics_seed(seed: int = DIAGNOSTICS_SEED) -> None:
    """Set the random seed for diagnostics operations."""
    random.seed(seed)
    np.random.seed(seed)

def calculate_vif(data: pd.DataFrame, predictors: List[str]) -> Dict[str, float]:
    """
    Calculate Variance Inflation Factor (VIF) for a list of predictors.
    
    Args:
        data: DataFrame containing the predictor variables.
        predictors: List of column names to calculate VIF for.
        
    Returns:
        Dictionary mapping predictor names to their VIF values.
    """
    if not predictors:
        return {}
        
    vif_data = {}
    # Ensure we only use columns that exist
    valid_predictors = [p for p in predictors if p in data.columns]
    
    if len(valid_predictors) < 2:
        # Cannot calculate VIF with fewer than 2 predictors
        return {p: 0.0 for p in valid_predictors}
        
    X = data[valid_predictors].dropna()
    if X.empty:
        return {p: 0.0 for p in valid_predictors}
        
    # Add intercept
    X_with_intercept = sm.add_constant(X)
    
    for i, col in enumerate(valid_predictors):
        if col == 'const':
            continue
        # Regress this variable against all others
        y = X[col]
        X_other = X_with_intercept.drop(columns=[col])
        if X_other.empty:
            vif_data[col] = 1.0
            continue
            
        try:
            model = sm.OLS(y, X_other).fit()
            r_squared = model.rsquared
            vif = 1.0 / (1.0 - r_squared) if (1.0 - r_squared) != 0 else float('inf')
            vif_data[col] = vif
        except Exception:
            vif_data[col] = float('inf')
            
    return vif_data

def detect_perfect_multicollinearity(data: pd.DataFrame, predictors: List[str]) -> List[List[str]]:
    """
    Detect perfect multicollinearity using matrix rank check.
    
    Args:
        data: DataFrame containing predictor variables.
        predictors: List of column names to check.
        
    Returns:
        List of pairs flagged as perfectly collinear.
    """
    valid_predictors = [p for p in predictors if p in data.columns]
    if len(valid_predictors) < 2:
        return []
        
    X = data[valid_predictors].dropna()
    if X.empty:
        return []
        
    # Convert to numpy array
    matrix = X.values
    
    # Calculate rank
    rank = np.linalg.matrix_rank(matrix)
    expected_rank = matrix.shape[1]
    
    if rank < expected_rank:
        # Linear dependence detected - identify pairs
        # Simple approach: check pairwise correlation of 1.0 or -1.0
        collinear_pairs = []
        for i in range(len(valid_predictors)):
            for j in range(i + 1, len(valid_predictors)):
                col_i = valid_predictors[i]
                col_j = valid_predictors[j]
                corr = data[col_i].corr(data[col_j])
                if abs(corr) == 1.0:
                    collinear_pairs.append([col_i, col_j])
        return collinear_pairs
        
    return []

def run_sensitivity_analysis(correlation_results: Dict[str, Any], thresholds: List[float] = [0.01, 0.05, 0.10]) -> Dict[str, Any]:
    """
    Run sensitivity analysis by re-evaluating significance at different thresholds.
    
    Args:
        correlation_results: Dictionary containing correlation results with p-values.
        thresholds: List of p-value thresholds to test.
        
    Returns:
        Dictionary with sensitivity analysis results.
    """
    base_threshold = 0.05
    base_significant = 0
    results = {}
    
    # Extract p-values and significance
    pairs = correlation_results.get('pairs', [])
    p_values = correlation_results.get('p_values', [])
    
    if not pairs or not p_values:
        return {"status": "NO_DATA", "results": {}}
        
    # Count base significant findings
    for p in p_values:
        if p <= base_threshold:
            base_significant += 1
            
    total_tests = len(p_values)
    
    for threshold in thresholds:
        significant_count = sum(1 for p in p_values if p <= threshold)
        if base_significant == 0:
            pct_change = 0.0 if significant_count == 0 else 100.0
        else:
            pct_change = ((significant_count - base_significant) / base_significant) * 100
            
        results[f"p_{threshold}"] = {
            "significant_count": significant_count,
            "percentage_change": pct_change
        }
        
    # Determine stability
    max_change = max(abs(r["percentage_change"]) for r in results.values()) if results else 0
    stability_status = "STABLE" if max_change < 10 else "UNSTABLE"
    
    return {
        "base_threshold": base_threshold,
        "base_significant": base_significant,
        "total_tests": total_tests,
        "results": results,
        "stability_status": stability_status
    }

def calculate_power(observed_n: int, target_r: float = 0.3, target_power: float = 0.80, alpha: float = 0.05) -> Dict[str, Any]:
    """
    Calculate power analysis metrics for correlation studies.
    
    This function calculates the required sample size to detect a correlation
    of magnitude `target_r` with `target_power` at significance level `alpha`,
    and compares it to the `observed_n` sample size.
    
    Args:
        observed_n: The actual sample size used in the study.
        target_r: The target correlation coefficient to detect.
        target_power: The desired statistical power (default 0.80).
        alpha: Significance level (default 0.05).
        
    Returns:
        Dictionary containing power analysis results.
    """
    # Calculate required sample size for correlation test
    # Using Fisher's z-transformation approximation
    # r = correlation coefficient
    # z = 0.5 * ln((1+r)/(1-r))
    # SE = 1 / sqrt(n-3)
    # For power analysis, we use the approximation:
    # n = ((z_alpha + z_beta) / (0.5 * ln((1+r)/(1-r))))^2 + 3
    
    if target_r == 0:
        return {
            "observed_n": observed_n,
            "required_n": float('inf'),
            "observed_power": 0.0,
            "underpowered": True,
            "message": "Cannot calculate power for zero correlation."
        }
        
    # Z-scores for alpha and power
    z_alpha = stats.norm.ppf(1 - alpha / 2)
    z_beta = stats.norm.ppf(target_power)
    
    # Fisher transformation
    z_r = 0.5 * np.log((1 + target_r) / (1 - target_r))
    
    # Calculate required n
    # n = ((z_alpha + z_beta) / z_r)^2 + 3
    required_n = int(((z_alpha + z_beta) / z_r) ** 2 + 3)
    
    # Calculate observed power given observed_n
    # SE_obs = 1 / sqrt(observed_n - 3)
    # z_obs = z_r / SE_obs
    # power = Phi(z_obs - z_alpha)
    if observed_n <= 3:
        observed_power = 0.0
    else:
        se_obs = 1.0 / np.sqrt(observed_n - 3)
        z_obs = z_r / se_obs
        observed_power = stats.norm.cdf(z_obs - z_alpha)
        
    underpowered = observed_n < required_n
    
    return {
        "observed_n": observed_n,
        "required_n": required_n,
        "observed_power": float(observed_power),
        "target_power": target_power,
        "target_r": target_r,
        "alpha": alpha,
        "underpowered": underpowered,
        "message": "Underpowered" if underpowered else "Adequately powered"
    }

def run_collinearity_diagnostics(data: pd.DataFrame, predictors: List[str], collinearity_map_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Run collinearity diagnostics including VIF and perfect multicollinearity checks.
    
    Args:
        data: DataFrame with predictor variables.
        predictors: List of predictor column names.
        collinearity_map_path: Path to existing collinearity map JSON (optional).
        
    Returns:
        Dictionary with collinearity diagnostics results.
    """
    # Detect perfect multicollinearity
    perfect_collinear_pairs = detect_perfect_multicollinearity(data, predictors)
    
    # Filter out collinear pairs for VIF calculation
    cols_to_exclude = set()
    for pair in perfect_collinear_pairs:
        cols_to_exclude.update(pair)
        
    valid_predictors = [p for p in predictors if p not in cols_to_exclude and p in data.columns]
    
    # Calculate VIF
    vif_results = calculate_vif(data, valid_predictors)
    
    # Flag high VIF
    high_vif = {k: v for k, v in vif_results.items() if v > 5}
    
    return {
        "perfect_multicollinearity_detected": len(perfect_collinear_pairs) > 0,
        "collinear_pairs": perfect_collinear_pairs,
        "excluded_columns": list(cols_to_exclude),
        "vif_values": vif_results,
        "high_vif_flags": high_vif,
        "max_vif": max(vif_results.values()) if vif_results else 0
    }

def generate_diagnostics_report(data: pd.DataFrame, predictors: List[str], 
                                correlation_results: Dict[str, Any],
                                collinearity_map_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Generate a comprehensive diagnostics report.
    
    Args:
        data: DataFrame with processed data.
        predictors: List of predictor variable names.
        correlation_results: Results from correlation analysis.
        collinearity_map_path: Path to static collinearity map (optional).
        
    Returns:
        Dictionary containing the full diagnostics report.
    """
    # Run collinearity diagnostics
    collinearity_report = run_collinearity_diagnostics(data, predictors, collinearity_map_path)
    
    # Run sensitivity analysis
    sensitivity_report = run_sensitivity_analysis(correlation_results)
    
    # Calculate power analysis
    observed_n = len(data)
    power_report = calculate_power(observed_n)
    
    return {
        "collinearity": collinearity_report,
        "sensitivity": sensitivity_report,
        "power": power_report,
        "sample_size": observed_n,
        "n_predictors": len(predictors)
    }

def main():
    """Main entry point for diagnostics module."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run diagnostics on correlation analysis results.")
    parser.add_argument("--data", type=str, required=True, help="Path to processed data parquet file")
    parser.add_argument("--correlation-results", type=str, required=True, help="Path to correlation results JSON")
    parser.add_argument("--output", type=str, required=True, help="Path to output diagnostics report JSON")
    parser.add_argument("--collinearity-map", type=str, default=None, help="Path to static collinearity map JSON")
    
    args = parser.parse_args()
    
    # Load data
    data = pd.read_parquet(args.data)
    
    # Load correlation results
    with open(args.correlation_results, 'r') as f:
        correlation_results = json.load(f)
        
    # Get predictors from data (exclude non-predictor columns if any)
    # Assuming predictors are numeric columns not in standard metadata
    predictors = [col for col in data.select_dtypes(include=[np.number]).columns]
    
    # Generate report
    report = generate_diagnostics_report(data, predictors, correlation_results, args.collinearity_map)
    
    # Save report
    os.makedirs(os.path.dirname(args.output), exist_ok=True)
    with open(args.output, 'w') as f:
        json.dump(report, f, indent=2)
        
    print(f"Diagnostics report saved to {args.output}")
    print(f"Power Analysis: N={report['power']['observed_n']}, Required N={report['power']['required_n']}, Status={report['power']['message']}")

if __name__ == "__main__":
    main()
