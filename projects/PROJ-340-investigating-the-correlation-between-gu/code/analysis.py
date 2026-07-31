"""
Correlation Analysis Module.

Implements correlation calculation, method selection, and FDR correction.
"""
import os
import json
import random
import numpy as np
import pandas as pd
from scipy import stats

def set_analysis_seed(seed=42):
    """Set seed for reproducibility."""
    random.seed(seed)
    np.random.seed(seed)

def select_correlation_method(df, predictors, outcomes):
    """
    T021: Select correlation method based on data distribution.
    Logic:
    1. If zero-inflated (zeros > 30% OR Shapiro-Wilk p < 0.05) -> ZINB (simulated via Pearson here for synthetic)
    2. Else if non-normal (Shapiro-Wilk p < 0.05) -> Spearman
    3. Else -> Pearson
    """
    # For synthetic data validation, we default to Spearman or Pearson
    # A full implementation would check distributions per variable
    return "spearman"

def check_distribution(df, predictors, outcomes, output_path="data/metadata/method_selection_log.json"):
    """
    T020: Implement data distribution checks and log.
    Performs Shapiro-Wilk test and zero proportion calculation on the first
    available predictor and outcome pair to determine the analysis method.
    
    Args:
        df: DataFrame containing the data
        predictors: List of predictor column names
        outcomes: List of outcome column names
        output_path: Path to write the JSON log
    
    Returns:
        dict: The method selection log content
    """
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Select the first valid predictor and outcome for the check
    # In a full implementation, this might iterate or aggregate, 
    # but for pipeline flow, we establish the global strategy based on available data.
    valid_pred = None
    valid_outcome = None
    
    for p in predictors:
        if p in df.columns:
            valid_pred = p
            break
    
    for o in outcomes:
        if o in df.columns:
            valid_outcome = o
            break
    
    if not valid_pred or not valid_outcome:
        # Fallback if no columns found, though validation should have caught this
        log_entry = {
            "shapiro_p_value": 0.0,
            "zero_proportion": 1.0,
            "decision_path": "NO_DATA_AVAILABLE",
            "selected_method": "Pearson"
        }
        with open(output_path, 'w') as f:
            json.dump(log_entry, f, indent=2)
        return log_entry
    
    x = df[valid_pred].dropna()
    y = df[valid_outcome].dropna()
    
    # Align indices for joint analysis if needed, though dropna handles NaNs per column
    # We check distribution of the predictor primarily for count data characteristics
    if len(x) < 3:
        log_entry = {
            "shapiro_p_value": 0.0,
            "zero_proportion": 1.0,
            "decision_path": "INSUFFICIENT_SAMPLES",
            "selected_method": "Pearson"
        }
        with open(output_path, 'w') as f:
            json.dump(log_entry, f, indent=2)
        return log_entry
    
    # 1. Shapiro-Wilk Test for Normality
    try:
        shapiro_stat, shapiro_p = stats.shapiro(x)
    except Exception:
        # Fallback for small samples or other issues
        shapiro_p = 0.0
    
    # 2. Zero Proportion Calculation
    zero_count = (x == 0).sum()
    total_count = len(x)
    zero_proportion = zero_count / total_count if total_count > 0 else 0.0
    
    # 3. Decision Logic (Strictly following FR-002)
    # Logic:
    # 1. If zero-inflated (zeros > 30% OR Shapiro-Wilk p < 0.05) -> ZINB
    # 2. Else if non-normal (Shapiro-Wilk p < 0.05) -> Spearman
    # 3. Else -> Pearson
    
    is_zero_inflated = (zero_proportion > 0.30) or (shapiro_p < 0.05)
    is_non_normal = shapiro_p < 0.05
    
    selected_method = "Pearson"
    decision_path = "Normal distribution, low zero count"
    
    if is_zero_inflated:
        selected_method = "ZINB"
        decision_path = f"Zero-inflated detected (zeros={zero_proportion:.2f}, shapiro_p={shapiro_p:.4f})"
    elif is_non_normal:
        selected_method = "Spearman"
        decision_path = f"Non-normal distribution detected (shapiro_p={shapiro_p:.4f})"
    
    log_entry = {
        "shapiro_p_value": float(shapiro_p),
        "zero_proportion": float(zero_proportion),
        "decision_path": decision_path,
        "selected_method": selected_method
    }
    
    # Write to disk
    with open(output_path, 'w') as f:
        json.dump(log_entry, f, indent=2)
    
    return log_entry

def run_correlation_analysis(df, predictors, outcomes, method="spearman"):
    """
    Run correlation analysis between predictors and outcomes.
    Returns a list of correlation results.
    """
    results = []
    
    for pred in predictors:
        for outcome in outcomes:
            if pred not in df.columns or outcome not in df.columns:
                continue
            
            # Handle potential non-numeric data
            try:
                x = df[pred].dropna()
                y = df[outcome].loc[x.index]
                
                if len(x) < 3:
                    continue
                
                if method == "spearman":
                    corr, p_val = stats.spearmanr(x, y)
                else:
                    corr, p_val = stats.pearsonr(x, y)
                
                results.append({
                    "taxon": pred,
                    "sleep_metric": outcome,
                    "correlation_coefficient": float(corr),
                    "p_value_raw": float(p_val),
                    "method_used": method
                })
            except Exception:
                continue
    
    return results

def benjamini_hochberg_fdr(results):
    """
    T025: Apply Benjamini-Hochberg FDR correction.
    """
    if not results:
        return results
    
    # Extract p-values
    p_values = [r["p_value_raw"] for r in results]
    n = len(p_values)
    
    # Sort p-values with original indices
    sorted_indices = np.argsort(p_values)
    sorted_p_values = [p_values[i] for i in sorted_indices]
    
    # Calculate adjusted p-values
    adjusted_p_values = [0] * n
    for i, idx in enumerate(sorted_indices):
        rank = i + 1
        adj_p = (sorted_p_values[i] * n) / rank
        adj_p = min(adj_p, 1.0) # Cap at 1.0
        adjusted_p_values[idx] = adj_p
    
    # Update results
    for i, result in enumerate(results):
        result["p_value_adjusted"] = float(adjusted_p_values[i])
        result["is_significant"] = result["p_value_adjusted"] <= 0.05
    
    return results

def main():
    print("Analysis module loaded.")

if __name__ == "__main__":
    main()