import os
import json
import logging
from typing import Dict, Any, Optional, Tuple
import numpy as np
import pandas as pd
from scipy import stats

from code.config import get_config
from code.data.paths import get_processed_path, get_results_path, ensure_dir
from code.analysis.permutation import run_permutation_test
from code.analysis.p_value_formatter import format_p_value

logger = logging.getLogger(__name__)

def load_regression_dataset() -> pd.DataFrame:
    """
    Load the merged dataset containing variability metrics and behavioral scores.
    
    Returns:
        DataFrame with columns: Subject_ID, Variability_Metric, Flexibility_Score, 
        Age, Sex, Mean_FD, Total_Scan_Time
    """
    metrics_path = os.path.join(get_processed_path(), "metrics.csv")
    behavioral_path = os.path.join(get_processed_path(), "merged_behavioral.csv")
    
    if not os.path.exists(metrics_path):
        raise FileNotFoundError(f"Metrics file not found: {metrics_path}")
    if not os.path.exists(behavioral_path):
        raise FileNotFoundError(f"Behavioral file not found: {behavioral_path}")
        
    df_metrics = pd.read_csv(metrics_path)
    df_behavioral = pd.read_csv(behavioral_path)
    
    # Merge on Subject_ID
    df = pd.merge(df_metrics, df_behavioral, on="Subject_ID", how="inner")
    
    # Drop rows with any missing values in key columns
    key_cols = ["Variability_Metric", "Flexibility_Score", "Age", "Sex", "Mean_FD", "Total_Scan_Time"]
    df = df.dropna(subset=key_cols)
    
    return df

def encode_sex(sex_series: pd.Series) -> pd.Series:
    """
    Encode Sex column as binary (0=Female, 1=Male).
    
    Args:
        sex_series: Series containing 'M'/'F' or 'Male'/'Female' strings.
        
    Returns:
        Series of integers (0 or 1).
    """
    sex_clean = sex_series.str.lower().str.strip()
    return sex_clean.map({"f": 0, "female": 0, "m": 1, "male": 1})

def run_linear_regression(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Run linear regression: Flexibility_Score ~ Variability_Metric + Age + Sex + Mean_FD + Total_Scan_Time
    
    Args:
        df: DataFrame with all required columns.
        
    Returns:
        Dictionary with regression results (coefficients, p-values, R-squared).
    """
    # Prepare features
    X = df[["Variability_Metric", "Age", "Sex", "Mean_FD", "Total_Scan_Time"]].copy()
    X["Sex"] = encode_sex(df["Sex"])
    X = X.values
    
    y = df["Flexibility_Score"].values
    
    # Add intercept
    X_with_intercept = np.column_stack([np.ones(X.shape[0]), X])
    
    # Solve using least squares
    try:
        coeffs, residuals, rank, s = np.linalg.lstsq(X_with_intercept, y, rcond=None)
    except np.linalg.LinAlgError as e:
        logger.error(f"Linear algebra error during regression: {e}")
        raise
    
    # Calculate predictions and residuals
    y_pred = X_with_intercept @ coeffs
    residuals_calc = y - y_pred
    
    # Calculate R-squared
    ss_res = np.sum(residuals_calc ** 2)
    ss_tot = np.sum((y - np.mean(y)) ** 2)
    r_squared = 1 - (ss_res / ss_tot)
    
    # Calculate standard errors and p-values for coefficients
    # Covariance matrix of coefficients: sigma^2 * (X^T X)^-1
    n = len(y)
    p = X_with_intercept.shape[1]
    sigma_squared = ss_res / (n - p)
    
    try:
        XtX_inv = np.linalg.inv(X_with_intercept.T @ X_with_intercept)
    except np.linalg.LinAlgError:
        logger.warning("X^T X is singular. Setting SEs to NaN.")
        se = np.full(p, np.nan)
        p_values = np.full(p, np.nan)
    else:
        se = np.sqrt(sigma_squared * np.diag(XtX_inv))
        
        # t-statistics
        t_stats = coeffs / se
        
        # p-values (two-tailed)
        p_values = 2 * (1 - stats.t.cdf(np.abs(t_stats), df=n-p))
    
    # Format results
    results = {
        "intercept": float(coeffs[0]),
        "intercept_se": float(se[0]) if not np.isnan(se[0]) else None,
        "intercept_p": float(p_values[0]) if not np.isnan(p_values[0]) else None,
        "coefficients": {
            "Variability_Metric": {
                "beta": float(coeffs[1]),
                "se": float(se[1]) if not np.isnan(se[1]) else None,
                "p_value": float(p_values[1]) if not np.isnan(p_values[1]) else None
            },
            "Age": {
                "beta": float(coeffs[2]),
                "se": float(se[2]) if not np.isnan(se[2]) else None,
                "p_value": float(p_values[2]) if not np.isnan(p_values[2]) else None
            },
            "Sex": {
                "beta": float(coeffs[3]),
                "se": float(se[3]) if not np.isnan(se[3]) else None,
                "p_value": float(p_values[3]) if not np.isnan(p_values[3]) else None
            },
            "Mean_FD": {
                "beta": float(coeffs[4]),
                "se": float(se[4]) if not np.isnan(se[4]) else None,
                "p_value": float(p_values[4]) if not np.isnan(p_values[4]) else None
            },
            "Total_Scan_Time": {
                "beta": float(coeffs[5]),
                "se": float(se[5]) if not np.isnan(se[5]) else None,
                "p_value": float(p_values[5]) if not np.isnan(p_values[5]) else None
            }
        },
        "r_squared": float(r_squared),
        "n_subjects": int(n)
    }
    
    return results

def save_regression_summary(results: Dict[str, Any], output_path: Optional[str] = None) -> str:
    """
    Save regression results to JSON, formatting p-values per T032.
    
    Args:
        results: Dictionary of regression results.
        output_path: Optional path to save JSON. Defaults to results directory.
        
    Returns:
        Path to the saved JSON file.
    """
    if output_path is None:
        output_path = os.path.join(get_results_path(), "regression_summary.json")
        
    ensure_dir(os.path.dirname(output_path))
    
    # Format p-values for human readability (T032 requirement)
    formatted_results = results.copy()
    
    # Format intercept p-value
    if formatted_results["intercept_p"] is not None:
        formatted_results["intercept_p_str"] = format_p_value(formatted_results["intercept_p"])
        
    # Format coefficient p-values
    for key in formatted_results["coefficients"]:
        p_val = formatted_results["coefficients"][key]["p_value"]
        if p_val is not None:
            formatted_results["coefficients"][key]["p_value_str"] = format_p_value(p_val)
            
    with open(output_path, 'w') as f:
        json.dump(formatted_results, f, indent=2)
        
    logger.info(f"Regression summary saved to {output_path}")
    return output_path

def run_regression_pipeline() -> str:
    """
    Run the full regression pipeline: load data, fit model, save results.
    
    Returns:
        Path to the saved regression summary JSON.
    """
    logger.info("Starting regression pipeline")
    df = load_regression_dataset()
    logger.info(f"Loaded {len(df)} subjects for regression")
    
    results = run_linear_regression(df)
    logger.info(f"Regression completed. R^2 = {results['r_squared']:.4f}")
    
    # Run permutation test for Variability_Metric significance
    # Extract the specific variable for permutation
    X_perm = df[["Variability_Metric", "Age", "Sex", "Mean_FD", "Total_Scan_Time"]].copy()
    X_perm["Sex"] = encode_sex(df["Sex"])
    y_perm = df["Flexibility_Score"].values
    
    # We need to test the coefficient of Variability_Metric
    # Permutation test: shuffle y and re-fit to get null distribution of the coefficient
    logger.info("Running permutation test for Variability_Metric significance...")
    
    # Run permutation test (10,000 iterations as per T031)
    # We pass the data and the index of the coefficient we care about (1 for Variability_Metric)
    perm_p_value = run_permutation_test(
        X=X_perm.values, 
        y=y_perm, 
        target_coef_idx=1, 
        n_permutations=10000
    )
    
    logger.info(f"Permutation test p-value: {perm_p_value}")
    
    # Update the Variability_Metric p-value with the permutation result
    results["coefficients"]["Variability_Metric"]["p_value"] = perm_p_value
    results["coefficients"]["Variability_Metric"]["p_value_str"] = format_p_value(perm_p_value)
    results["permutation_iterations"] = 10000
    
    # Save results
    output_path = save_regression_summary(results)
    logger.info("Regression pipeline completed successfully")
    
    return output_path

def main():
    """Entry point for regression analysis."""
    logging.basicConfig(level=logging.INFO)
    run_regression_pipeline()

if __name__ == "__main__":
    main()