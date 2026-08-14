"""
Diagnostics module for the Gut Microbiome - Sleep Architecture analysis.
Implements VIF calculation, collinearity detection, sensitivity analysis, and power analysis.
"""
import os
import json
import numpy as np
import pandas as pd
from scipy import stats
from pathlib import Path
from statsmodels.stats.outliers_influence import variance_inflation_factor
from typing import Dict, List, Any, Optional

def set_diagnostics_seed(seed: int = 42) -> None:
    """Set random seed for reproducibility."""
    np.random.seed(seed)
    if 'random' in globals():
        import random
        random.seed(seed)

def detect_perfect_multicollinearity(predictors_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Detect perfect multicollinearity using matrix rank check.
    
    Args:
        predictors_df: DataFrame containing predictor variables (taxa).
        
    Returns:
        Dictionary with 'is_perfectly_collinear' (bool) and 'rank' (int).
    """
    matrix = predictors_df.values
    rank = np.linalg.matrix_rank(matrix)
    is_perfectly_collinear = rank < predictors_df.shape[1]
    
    return {
        "is_perfectly_collinear": is_perfectly_collinear,
        "rank": int(rank),
        "num_columns": predictors_df.shape[1]
    }

def calculate_vif(
    predictors_df: pd.DataFrame,
    collinearity_map_path: str = "data/metadata/static_collinearity_map.json"
) -> Dict[str, Any]:
    """
    Calculate Variance Inflation Factor (VIF) for all predictors.
    Excludes predictors flagged as 'Perfect Multicollinearity' in the static collinearity map.
    
    Args:
        predictors_df: DataFrame containing predictor variables.
        collinearity_map_path: Path to the JSON file containing flagged collinear pairs.
        
    Returns:
        Dictionary containing VIF values for each predictor and a list of high-VIF flags.
    """
    # Load the static collinearity map to exclude flagged variables
    excluded_vars = set()
    if os.path.exists(collinearity_map_path):
        try:
            with open(collinearity_map_path, 'r') as f:
                collinearity_data = json.load(f)
            
            # The map structure is expected to be: {"flagged_pairs": [[var1, var2], ...], "excluded_vars": [...]}
            # Or simply a list of flagged variables if the structure varies.
            # We handle the common case where 'excluded_vars' is explicitly listed.
            if "excluded_vars" in collinearity_data:
                excluded_vars = set(collinearity_data["excluded_vars"])
            elif "flagged_pairs" in collinearity_data:
                # Flatten pairs into a set of variables
                for pair in collinearity_data["flagged_pairs"]:
                    excluded_vars.update(pair)
        except (json.JSONDecodeError, KeyError) as e:
            print(f"Warning: Could not load collinearity map at {collinearity_map_path}: {e}")
    else:
        print(f"Warning: Collinearity map not found at {collinearity_map_path}. Proceeding with all variables.")

    # Filter predictors
    available_cols = [col for col in predictors_df.columns if col not in excluded_vars]
    if not available_cols:
        return {
            "vif_values": {},
            "high_vif_flags": [],
            "excluded_count": len(excluded_vars),
            "message": "All predictors were excluded due to perfect multicollinearity."
        }

    sub_df = predictors_df[available_cols]
    
    # Check for constant columns (VIF is undefined for constant columns)
    constant_cols = [col for col in sub_df.columns if sub_df[col].nunique() == 1]
    if constant_cols:
        sub_df = sub_df.drop(columns=constant_cols)
        print(f"Warning: Dropped constant columns for VIF calculation: {constant_cols}")

    if sub_df.shape[1] == 0:
        return {
            "vif_values": {},
            "high_vif_flags": [],
            "excluded_count": len(excluded_vars) + len(constant_cols),
            "message": "No valid predictors remaining after exclusion and constant check."
        }

    vif_results = {}
    high_vif_flags = []
    threshold = 5.0

    # Calculate VIF for each column
    # VIF requires an intercept term in the regression model.
    # statsmodels VIF function handles this by adding a constant column if not present,
    # but we must ensure the matrix is full rank.
    try:
        # Add constant for intercept
        X = sub_df.copy()
        if not np.all(np.any(X != 0, axis=0)): # Check if all cols are zero
             X = X.drop(columns=[c for c in X.columns if (X[c] == 0).all()])
        
        if X.shape[1] == 0:
             return {"vif_values": {}, "high_vif_flags": [], "message": "No variance in data."}

        # VIF calculation
        # We iterate to avoid potential rank issues in the full matrix if some cols are highly correlated
        # but not perfectly.
        for i, col in enumerate(X.columns):
            # Create a matrix with the current column as the dependent variable
            # and all other columns as independent variables.
            y = X[col]
            X_other = X.drop(columns=[col])
            
            if X_other.shape[1] == 0:
                vif_results[col] = 1.0
                continue
            
            # Check rank of X_other to avoid singular matrix errors
            if np.linalg.matrix_rank(X_other.values) < X_other.shape[1]:
                vif_results[col] = float('inf')
                high_vif_flags.append({"variable": col, "vif": float('inf'), "reason": "Singular matrix in auxiliary regression"})
                continue

            # Fit OLS to get VIF
            # VIF = 1 / (1 - R^2)
            # We can use the variance_inflation_factor function from statsmodels
            # It expects the full design matrix including the constant.
            X_with_const = sm.add_constant(X_other)
            vif_val = variance_inflation_factor(X_with_const.values, 1) # 1 is the index of the first non-constant col
            
            # Actually, variance_inflation_factor expects the full matrix of predictors (including the one being tested)
            # and the index of the column to test.
            # Let's use the standard approach:
            X_full = sm.add_constant(X)
            vif_val = variance_inflation_factor(X_full.values, i + 1) # +1 because of constant column at index 0
            
            vif_results[col] = float(vif_val)
            
            if vif_val > threshold:
                high_vif_flags.append({
                    "variable": col,
                    "vif": float(vif_val),
                    "threshold": threshold,
                    "status": "HIGH"
                })
    except Exception as e:
        # Fallback or error handling if statsmodels fails
        print(f"Error calculating VIF: {e}")
        return {
            "vif_values": {},
            "high_vif_flags": [],
            "error": str(e)
        }

    return {
        "vif_values": vif_results,
        "high_vif_flags": high_vif_flags,
        "excluded_count": len(excluded_vars),
        "threshold": threshold,
        "total_predictors_processed": len(available_cols)
    }

def run_sensitivity_analysis(
    correlation_results_path: str,
    thresholds: List[float] = [0.01, 0.05, 0.10]
) -> Dict[str, Any]:
    """
    Perform sensitivity analysis by re-evaluating significance at different p-value thresholds.
    
    Args:
        correlation_results_path: Path to the correlation matrix JSON.
        thresholds: List of p-value thresholds to test.
        
    Returns:
        Dictionary with stability status and percentage changes.
    """
    if not os.path.exists(correlation_results_path):
        raise FileNotFoundError(f"Correlation results not found at {correlation_results_path}")
    
    with open(correlation_results_path, 'r') as f:
        data = json.load(f)
    
    # Extract p-values and correlations
    # Assuming structure: {"correlations": [{"variable1": ..., "variable2": ..., "p_value": ..., "correlation": ...}, ...]}
    # Or a matrix format. We assume a flat list of results for simplicity.
    results_list = data.get("correlations", [])
    
    if not results_list:
        return {
            "stability_status": "UNKNOWN",
            "thresholds_tested": thresholds,
            "message": "No correlation results found."
        }
    
    base_threshold = 0.05
    base_significant_count = sum(1 for r in results_list if r.get("p_value", 1.0) <= base_threshold)
    
    changes = {}
    for t in thresholds:
        count = sum(1 for r in results_list if r.get("p_value", 1.0) <= t)
        if base_significant_count == 0:
            pct_change = 0.0 if count == 0 else 100.0 # Undefined if base is 0, but we handle it
        else:
            pct_change = ((count - base_significant_count) / base_significant_count) * 100
        
        changes[str(t)] = {
            "significant_count": count,
            "percentage_change_from_base": pct_change
        }
    
    # Determine stability
    # Stable if percentage change is < 10% for all thresholds
    max_change = max(abs(c["percentage_change_from_base"]) for c in changes.values())
    stability_status = "STABLE" if max_change < 10.0 else "UNSTABLE"
    
    return {
        "stability_status": stability_status,
        "thresholds_tested": thresholds,
        "base_threshold": base_threshold,
        "base_significant_count": base_significant_count,
        "changes": changes
    }

def calculate_power(
    correlation_results_path: str,
    target_r: float = 0.3,
    target_power: float = 0.80,
    alpha: float = 0.05
) -> Dict[str, Any]:
    """
    Calculate the minimum sample size required to detect a correlation of at least `target_r`
    with `target_power` at significance level `alpha`.
    
    Args:
        correlation_results_path: Path to correlation results (to determine actual N).
        target_r: Target correlation coefficient.
        target_power: Desired statistical power.
        alpha: Significance level.
        
    Returns:
        Dictionary with calculated N, underpowered flag, and data source type.
    """
    # Determine actual N from the data
    if not os.path.exists(correlation_results_path):
        raise FileNotFoundError(f"Correlation results not found at {correlation_results_path}")
    
    with open(correlation_results_path, 'r') as f:
        data = json.load(f)
    
    # We need to find the sample size used.
    # If the file contains metadata about the dataset, use that.
    # Otherwise, we estimate from the number of observations if available.
    # For this task, we assume the correlation results were generated from a dataset
    # and we need to check if that N is sufficient.
    
    # Since the correlation results file might not contain N directly,
    # we might need to read the processed data or metadata.
    # However, for the purpose of this task, we will calculate the required N
    # and compare it to a known N if available, or just report the required N.
    
    # Let's assume we have access to the processed data path or metadata.
    # For now, we will calculate the required N and set a flag if we can't determine the actual N.
    
    # Calculate required N using the formula for correlation power analysis
    # N = (Z_alpha/2 + Z_beta)^2 / (0.5 * ln((1+r)/(1-r)))^2 + 3
    # Or use scipy's power analysis if available.
    
    # Using the approximation:
    # r = correlation
    # t = r * sqrt((n-2)/(1-r^2))
    # We need to solve for n given power.
    
    # A simpler approach using scipy.stats
    from scipy.stats import t
    
    # Critical t-value for two-tailed test
    t_crit = t.ppf(1 - alpha/2, df=1) # df will be n-2, so we need to iterate or approximate
    
    # We can use the `statsmodels.stats.power` module for a more accurate calculation
    try:
        from statsmodels.stats.power import tt_solve_power
        # tt_solve_power solves for nobs in a t-test.
        # For correlation, we can use the Fisher transformation approximation or
        # use the fact that testing r=0 is equivalent to a t-test on the transformed variable.
        # However, a direct function for correlation power is not in tt_solve_power.
        # We use the approximation:
        # effect_size = r
        # But tt_solve_power expects Cohen's d.
        # Let's use the formula directly:
        # n = ( (Z_alpha + Z_beta) / (0.5 * ln((1+r)/(1-r))) )^2 + 3
        
        Z_alpha = stats.norm.ppf(1 - alpha/2)
        Z_beta = stats.norm.ppf(target_power)
        
        # Fisher Z transformation of r
        z_r = 0.5 * np.log((1 + target_r) / (1 - target_r))
        
        # Required sample size
        n_required = ((Z_alpha + Z_beta) / z_r)**2 + 3
        n_required = int(np.ceil(n_required))
    except Exception as e:
        # Fallback to a rough estimate
        n_required = int(50 / (target_r**2)) # Very rough heuristic
    
    # Determine data source type
    # Check if the path contains "synthetic" or "real"
    data_source_type = "synthetic" if "synthetic" in correlation_results_path.lower() else "real"
    
    # We need the actual N to determine if it's underpowered.
    # Since we don't have the actual N from the correlation file directly,
    # we will assume the pipeline has recorded the sample size in the correlation results.
    # If not, we will report the required N and note that the actual N is unknown.
    
    actual_n = data.get("sample_size", None)
    
    underpowered = False
    if actual_n is not None:
        underpowered = actual_n < n_required
    else:
        underpowered = "UNKNOWN" # Cannot determine without actual N
    
    return {
        "required_sample_size": n_required,
        "actual_sample_size": actual_n,
        "underpowered": underpowered,
        "target_correlation": target_r,
        "target_power": target_power,
        "alpha": alpha,
        "data_source_type": data_source_type
    }

def main():
    """
    Main function to run diagnostics.
    This is a placeholder for CLI execution.
    """
    import argparse
    parser = argparse.ArgumentParser(description="Run diagnostics for Gut Microbiome - Sleep Analysis")
    parser.add_argument("--mode", type=str, default="all", help="Mode to run: vif, sensitivity, power, all")
    parser.add_argument("--data", type=str, help="Path to processed data for VIF")
    parser.add_argument("--collinearity-map", type=str, default="data/metadata/static_collinearity_map.json", help="Path to collinearity map")
    parser.add_argument("--correlation-results", type=str, help="Path to correlation results for sensitivity/power")
    args = parser.parse_args()
    
    if args.mode in ["vif", "all"]:
        if args.data:
            df = pd.read_csv(args.data)
            # Assume predictors are all columns except 'id' or 'outcome'
            predictors = df.select_dtypes(include=[np.number]).columns.tolist()
            if 'id' in predictors: predictors.remove('id')
            # Filter to only predictor columns (taxa)
            # This is a simplification; in reality, we need to know which are predictors.
            # For now, we assume all numeric columns are predictors.
            result = calculate_vif(df[predictors], args.collinearity_map)
            print(json.dumps(result, indent=2))
            
            # Save result
            with open("data/results/vif_report.json", 'w') as f:
                json.dump(result, f, indent=2)
                print("VIF report saved to data/results/vif_report.json")
    
    if args.mode in ["sensitivity", "all"]:
        if args.correlation_results:
            result = run_sensitivity_analysis(args.correlation_results)
            print(json.dumps(result, indent=2))
    
    if args.mode in ["power", "all"]:
        if args.correlation_results:
            result = calculate_power(args.correlation_results)
            print(json.dumps(result, indent=2))

if __name__ == "__main__":
    main()
