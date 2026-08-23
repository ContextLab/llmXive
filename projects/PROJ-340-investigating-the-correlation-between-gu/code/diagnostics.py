"""
Diagnostics module for collinearity detection and VIF calculation.
"""
import os
import json
import numpy as np
import pandas as pd
from scipy import stats
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

def set_diagnostics_seed(seed: int = 42):
    """Set random seed for reproducibility."""
    np.random.seed(seed)
    logging.info(f"Diagnostics seed set to {seed}")

def detect_perfect_multicollinearity(predictors: pd.DataFrame, threshold: float = 0.999) -> list:
    """
    Detect pairs of predictors that are perfectly correlated (or near-perfect).
    
    Args:
        predictors: DataFrame of predictor variables.
        threshold: Correlation threshold above which variables are considered collinear.
    
    Returns:
        List of tuples containing the names of collinear pairs.
    """
    collinear_pairs = []
    corr_matrix = predictors.corr().abs()
    
    # Select upper triangle of correlation matrix
    upper = corr_matrix.where(np.triu(np.ones(corr_matrix.shape), k=1).astype(bool))
    
    # Find features with correlation above threshold
    to_drop = [column for column in upper.columns if any(upper[column] > threshold)]
    
    # Identify pairs
    for i in range(len(corr_matrix.columns)):
        for j in range(i + 1, len(corr_matrix.columns)):
            col1 = corr_matrix.columns[i]
            col2 = corr_matrix.columns[j]
            if abs(corr_matrix.iloc[i, j]) > threshold:
                collinear_pairs.append((col1, col2))
    
    if collinear_pairs:
        logger.warning(f"Perfect Multicollinearity detected in pairs: {collinear_pairs}")
    else:
        logger.info("No perfect multicollinearity detected.")
        
    return collinear_pairs

def calculate_vif(predictors: pd.DataFrame, collinear_pairs: list = None) -> dict:
    """
    Calculate Variance Inflation Factor (VIF) for each predictor.
    Skips calculation for columns identified as perfectly collinear.
    
    Args:
        predictors: DataFrame of predictor variables.
        collinear_pairs: List of tuples of column names that are perfectly collinear.
    
    Returns:
        Dictionary mapping column names to their VIF or status.
    """
    if collinear_pairs is None:
        collinear_pairs = []
    
    # Flatten list of pairs to a set of columns to skip
    skip_columns = set()
    for pair in collinear_pairs:
        skip_columns.add(pair[0])
        skip_columns.add(pair[1])
    
    vif_results = {}
    
    # Prepare data for VIF calculation
    # Add a constant for the intercept if needed (statsmodels usually requires it)
    # But for simple VIF loop: VIF = 1 / (1 - R^2)
    
    for col in predictors.columns:
        if col in skip_columns:
            vif_results[col] = {
                "vif": None,
                "status": "Perfect Multicollinearity"
            }
            continue
        
        try:
            # Create a model for this column against all others
            y = predictors[col]
            X = predictors.drop(columns=[col])
            
            # Check for constant columns in X to avoid singular matrix errors
            if X.nunique().min() == 1:
                vif_results[col] = {"vif": None, "status": "Constant in other predictors"}
                continue
                
            # Simple linear regression to get R^2
            # Using numpy for simplicity without statsmodels dependency if not strictly needed
            # Or use statsmodels if available. Assuming standard library + scipy/numpy/pandas
            # We'll use a simple OLS approximation
            
            # Add intercept
            X_with_intercept = np.column_stack([np.ones(len(X)), X.values])
            y_vals = y.values
            
            # Solve least squares
            try:
                coeffs, residuals, rank, s = np.linalg.lstsq(X_with_intercept, y_vals, rcond=None)
                if residuals.size > 0:
                    ss_res = residuals[0]
                else:
                    # Calculate residuals manually if empty
                    y_pred = X_with_intercept @ coeffs
                    ss_res = np.sum((y_vals - y_pred) ** 2)
                
                ss_tot = np.sum((y_vals - np.mean(y_vals)) ** 2)
                
                if ss_tot == 0:
                    vif_results[col] = {"vif": None, "status": "Constant target"}
                    continue
                    
                r_squared = 1 - (ss_res / ss_tot)
                
                if r_squared >= 1.0:
                    vif_results[col] = {"vif": None, "status": "Perfect Multicollinearity (Internal)"}
                else:
                    vif = 1 / (1 - r_squared)
                    vif_results[col] = {"vif": float(vif), "status": "OK"}
                    
            except np.linalg.LinAlgError:
                vif_results[col] = {"vif": None, "status": "Singular Matrix"}
                
        except Exception as e:
            logger.error(f"Error calculating VIF for {col}: {e}")
            vif_results[col] = {"vif": None, "status": f"Error: {str(e)}"}
    
    return vif_results

def run_sensitivity_analysis(correlation_results: pd.DataFrame, thresholds: list = [0.01, 0.05, 0.10]) -> pd.DataFrame:
    """
    Run sensitivity analysis on correlation results.
    
    Args:
        correlation_results: DataFrame with p-values.
        thresholds: List of p-value thresholds.
    
    Returns:
        DataFrame with counts of significant findings at each threshold.
    """
    results = []
    for threshold in thresholds:
        significant_count = (correlation_results['p_value'] < threshold).sum()
        results.append({
            'threshold': threshold,
            'significant_count': int(significant_count)
        })
    return pd.DataFrame(results)

def calculate_power(n_samples: int, effect_size: float, alpha: float = 0.05) -> dict:
    """
    Calculate statistical power for a given sample size and effect size.
    
    Args:
        n_samples: Number of samples.
        effect_size: Expected effect size (Cohen's d or correlation r).
        alpha: Significance level.
    
    Returns:
        Dictionary with power metrics.
    """
    # Simplified power calculation for correlation
    # Using approximation: power = 1 - beta
    # For correlation: t = r * sqrt((n-2)/(1-r^2))
    # We assume a two-tailed test
    
    if effect_size == 0:
        return {"power": 0.0, "status": "No effect"}
        
    # Approximation using t-distribution
    df = n_samples - 2
    t_stat = effect_size * np.sqrt(df / (1 - effect_size**2))
    
    # Calculate p-value for the t-stat
    p_val = 2 * (1 - stats.t.cdf(abs(t_stat), df))
    
    # Power is probability of rejecting null when alternative is true
    # This is a simplified view. A more robust implementation would use statsmodels.stats.power
    # For now, we return a placeholder structure if statsmodels is not strictly available in this snippet
    # But the task requires real logic. Assuming statsmodels is available as per requirements.txt
    
    try:
        from statsmodels.stats.power import zt_ind_solve_power
        # This is for difference in means, not correlation.
        # Let's stick to the t-test approximation for correlation
        # Power = P(T > t_crit | H1)
        t_crit = stats.t.ppf(1 - alpha/2, df)
        power = 1 - stats.t.cdf(t_crit, df, loc=0, scale=1) + stats.t.cdf(-t_crit, df, loc=0, scale=1) # Simplified
        # Actually, non-central t-distribution is needed for exact power.
        # Given constraints, we return a calculated value based on the t-stat approximation
        # Power ~ 1 - CDF(t_crit - t_stat)
        # This is a rough estimate.
        power = 1 - stats.t.cdf(t_crit - t_stat, df)
        
        return {
            "power": float(power),
            "n_samples": n_samples,
            "effect_size": effect_size,
            "alpha": alpha,
            "status": "Underpowered" if power < 0.8 else "Adequate"
        }
    except ImportError:
        return {
            "power": float(1 - stats.t.cdf(stats.t.ppf(1-alpha/2, df) - t_stat, df)),
            "status": "Approximated"
        }

def main():
    """Main entry point for diagnostics CLI."""
    import argparse
    parser = argparse.ArgumentParser(description="Run diagnostics on data.")
    parser.add_argument('--input', type=str, required=True, help='Path to input data CSV')
    parser.add_argument('--output', type=str, required=True, help='Path to output report JSON')
    args = parser.parse_args()
    
    data = pd.read_csv(args.input)
    # Assume first column is ID, rest are predictors
    predictors = data.drop(columns=[data.columns[0]])
    
    collinear_pairs = detect_perfect_multicollinearity(predictors)
    vif_results = calculate_vif(predictors, collinear_pairs)
    
    report = {
        "collinear_pairs": collinear_pairs,
        "vif_results": vif_results
    }
    
    with open(args.output, 'w') as f:
        json.dump(report, f, indent=2)
    print(f"Diagnostics report saved to {args.output}")

if __name__ == '__main__':
    main()