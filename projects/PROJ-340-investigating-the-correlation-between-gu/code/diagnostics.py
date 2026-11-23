"""
Diagnostics module for collinearity detection and VIF calculation.
Implements T021f_collinearity and T113 logic.
"""
import os
import json
import numpy as np
import pandas as pd
from scipy import stats
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any

def set_diagnostics_seed(seed: int = 42) -> None:
    """Set random seed for reproducibility."""
    np.random.seed(seed)
    if hasattr(json, 'set_int_max_str_digits'):
        json.set_int_max_str_digits(10000)

def detect_perfect_multicollinearity(
    predictors: pd.DataFrame,
    output_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Detects perfect multicollinearity in the predictor matrix.
    Identifies pairs of variables with correlation coefficient of 1.0 or -1.0.
    If found, returns a report indicating the pair and that VIF should be skipped.
    
    Args:
        predictors: DataFrame containing only predictor columns (no outcomes).
        output_path: Optional path to write the JSON report.
        
    Returns:
        Dictionary with detection results.
    """
    # Ensure we have numeric data
    predictors = predictors.select_dtypes(include=[np.number])
    
    if predictors.shape[1] < 2:
        return {
            "found_perfect_multicollinearity": False,
            "collinear_pairs": [],
            "skipped_vif": False,
            "message": "Not enough predictors to check for collinearity."
        }

    # Calculate correlation matrix
    corr_matrix = predictors.corr()
    
    collinear_pairs = []
    found_perfect = False
    
    # Check for perfect correlation (1.0 or -1.0)
    # We iterate over the upper triangle to avoid duplicates and self-correlation
    cols = predictors.columns
    for i in range(len(cols)):
        for j in range(i + 1, len(cols)):
            col_i = cols[i]
            col_j = cols[j]
            corr_val = corr_matrix.loc[col_i, col_j]
            
            # Use a small tolerance for floating point comparisons
            if abs(abs(corr_val) - 1.0) < 1e-9:
                collinear_pairs.append([col_i, col_j])
                found_perfect = True

    result = {
        "found_perfect_multicollinearity": found_perfect,
        "collinear_pairs": collinear_pairs,
        "skipped_vif": found_perfect,
        "message": "Perfect multicollinearity detected" if found_perfect else "No perfect multicollinearity detected."
    }

    if output_path:
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, 'w') as f:
            json.dump(result, f, indent=2)

    return result

def calculate_vif(
    predictors: pd.DataFrame,
    excluded_pairs: Optional[List[Tuple[str, str]]] = None
) -> pd.DataFrame:
    """
    Calculate Variance Inflation Factor (VIF) for predictors.
    Skips VIF calculation if perfect multicollinearity is detected (based on excluded_pairs or re-check).
    
    Args:
        predictors: DataFrame of predictors.
        excluded_pairs: List of pairs to exclude from VIF calculation if they are collinear.
        
    Returns:
        DataFrame with VIF values.
    """
    if excluded_pairs and len(excluded_pairs) > 0:
        # If we have excluded pairs, it means we detected perfect collinearity
        # We should not calculate VIF for the whole matrix as it will be singular.
        # Instead, we return a warning or a specific report.
        # However, the task asks to "skip VIF calculation for that pair".
        # If the whole matrix is singular, we can't calculate VIF for any.
        # So we return a report indicating VIF was skipped globally.
        return pd.DataFrame({
            "variable": predictors.columns,
            "vif": [float('nan')] * len(predictors.columns),
            "note": "Skipped due to perfect multicollinearity"
        })

    # Standard VIF calculation
    vif_data = pd.DataFrame()
    vif_data["variable"] = predictors.columns
    vif_data["vif"] = [
        stats.variance_inflation_factor(predictors.values, i)
        for i in range(predictors.shape[1])
    ]
    return vif_data

def run_sensitivity_analysis(
    results_df: pd.DataFrame,
    thresholds: List[float] = [0.01, 0.05, 0.10]
) -> pd.DataFrame:
    """
    Run sensitivity analysis on p-values across different thresholds.
    """
    results = []
    for thresh in thresholds:
        count = (results_df['p_value'] < thresh).sum()
        results.append({
            "threshold": thresh,
            "significant_count": int(count)
        })
    return pd.DataFrame(results)

def calculate_power(
    n: int,
    effect_size: float,
    alpha: float = 0.05
) -> float:
    """
    Calculate statistical power for a correlation test.
    Simplified approximation.
    """
    # Approximation using non-central t-distribution or simple formula
    # For correlation: power = 1 - beta
    # Using a simple approximation for demonstration
    if n < 3:
        return 0.0
    
    # Fisher's z-transformation approximation
    # This is a placeholder for a more robust calculation
    z_alpha = stats.norm.ppf(1 - alpha/2)
    z_beta = (np.sqrt(n-3) * np.arctanh(effect_size)) - z_alpha
    power = stats.norm.cdf(z_beta)
    return float(power)

def main():
    """Entry point for diagnostics script."""
    import argparse
    parser = argparse.ArgumentParser(description="Run diagnostics on data.")
    parser.add_argument("--input", type=str, required=True, help="Input CSV file.")
    parser.add_argument("--output", type=str, required=True, help="Output directory.")
    args = parser.parse_args()

    df = pd.read_csv(args.input)
    
    # Assume predictors are columns not ending in 'outcome' or 'sleep'
    # For this script, we assume specific column names or user input
    # Let's assume all numeric columns except 'subject_id' and 'sleep_duration' are predictors
    predictors = df.select_dtypes(include=[np.number]).drop(columns=['subject_id', 'sleep_duration'], errors='ignore')
    
    if predictors.empty:
        print("No predictor columns found.")
        return

    # Detect collinearity
    report = detect_perfect_multicollinearity(predictors, output_path=os.path.join(args.output, "collinearity_report.json"))
    print(json.dumps(report, indent=2))

if __name__ == '__main__':
    main()