import os
import sys
import json
import pandas as pd
import numpy as np
from pathlib import Path
from statsmodels.stats.outliers_influence import variance_inflation_factor
from sklearn.linear_model import LassoCV
from scipy import stats
from config import INPUT_PATHS, RANDOM_SEED, SAMPLE_LIMIT, DQS_REQUIRED
from logging_config import get_logger, log_operation, log_pipeline_start, log_pipeline_end, log_provenance, log_warning
import logging

# Setup logging for this module
logger = get_logger("analysis")

def load_processed_data():
    """Load the cleaned dataset from data/processed/cleaned_data.csv."""
    path = Path("data/processed/cleaned_data.csv")
    if not path.exists():
        raise FileNotFoundError(f"Processed data not found at {path}. Run data ingestion first.")
    return pd.read_csv(path)

def check_zero_variance(df):
    """Check for columns with zero variance (constant values)."""
    zero_var_cols = []
    for col in df.select_dtypes(include=[np.number]).columns:
        if df[col].nunique() == 1:
            zero_var_cols.append(col)
    return zero_var_cols

def log_zero_variance_warning(cols):
    """Log a warning for columns with zero variance."""
    if cols:
        log_warning(f"Columns with zero variance detected: {cols}")

@log_operation
def calculate_vif(df, exclude_cols=None):
    """
    Calculate Variance Inflation Factor (VIF) for numeric columns.
    
    Args:
        df: DataFrame containing numeric predictors.
        exclude_cols: List of column names to exclude from VIF calculation.
        
    Returns:
        dict: Mapping of column name to VIF value.
    """
    if exclude_cols is None:
        exclude_cols = []
        
    # Select only numeric columns not in exclude list
    numeric_df = df.select_dtypes(include=[np.number])
    features = [c for c in numeric_df.columns if c not in exclude_cols]
    
    if len(features) == 0:
        return {}
        
    # Drop rows with NaN in selected features
    valid_df = numeric_df[features].dropna()
    
    if valid_df.shape[0] < 2:
        log_warning("Not enough valid rows to calculate VIF.")
        return {}
        
    vif_results = {}
    for i, feature in enumerate(features):
        # Calculate VIF for this feature
        X = valid_df[features].values
        try:
            vif_val = variance_inflation_factor(X, i)
            vif_results[feature] = float(vif_val)
        except Exception as e:
            log_warning(f"Could not calculate VIF for {feature}: {e}")
            vif_results[feature] = float('nan')
            
    return vif_results

@log_operation
def save_vif_results(vif_dict, output_path="data/processed/vif_results.json"):
    """Save VIF results to a JSON file."""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(vif_dict, f, indent=2)
    log_provenance(f"VIF results saved to {output_path}")

@log_operation
def compute_spearman_correlation(df, x_col, y_col):
    """
    Compute Spearman rank correlation between two columns.
    
    Args:
        df: DataFrame.
        x_col: Name of the first column.
        y_col: Name of the second column.
        
    Returns:
        tuple: (r_value, p_value, n_obs)
    """
    # Drop NaNs for the specific columns
    valid_data = df[[x_col, y_col]].dropna()
    if len(valid_data) < 2:
        raise ValueError("Not enough valid data points to compute correlation.")
        
    r, p = stats.spearmanr(valid_data[x_col], valid_data[y_col])
    return float(r), float(p), len(valid_data)

@log_operation
def save_correlation_results(r, p, n_obs, output_path="data/processed/correlation_results.csv"):
    """Save correlation results to a CSV file."""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    result_df = pd.DataFrame({
        "r_value": [r],
        "p_value": [p],
        "n_obs": [n_obs]
    })
    result_df.to_csv(output_path, index=False)
    log_provenance(f"Correlation results saved to {output_path}")

@log_operation
def run_multivariate_regression(df, target_col, feature_cols):
    """
    Run multivariate linear regression using statsmodels.
    
    Args:
        df: DataFrame.
        target_col: Name of the target column.
        feature_cols: List of feature column names.
        
    Returns:
        dict: Regression results (coefficients, std_err, p_values).
    """
    import statsmodels.api as sm
    
    X = df[feature_cols].dropna(axis=0, how='any')
    y = df.loc[X.index, target_col]
    
    if len(X) < 2:
        raise ValueError("Not enough data points for regression.")
        
    X = sm.add_constant(X)
    model = sm.OLS(y, X).fit()
    
    results = {
        "coefficients": {},
        "std_err": {},
        "p_values": {}
    }
    
    for i, col in enumerate(X.columns):
        results["coefficients"][col] = float(model.params[i])
        results["std_err"][col] = float(model.bse[i])
        results["p_values"][col] = float(model.pvalues[i])
        
    return results

@log_operation
def save_regression_results(results, output_path="data/processed/regression_results.csv"):
    """Save regression results to a CSV file."""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    rows = []
    for feature in results["coefficients"].keys():
        rows.append({
            "feature": feature,
            "coefficient": results["coefficients"][feature],
            "std_err": results["std_err"][feature],
            "p_value": results["p_values"][feature]
        })
        
    df = pd.DataFrame(rows)
    df.to_csv(output_path, index=False)
    log_provenance(f"Regression results saved to {output_path}")

@log_operation
def run_lasso_regression(df, target_col, feature_cols, alpha=0.1):
    """
    Run Lasso regression.
    
    Args:
        df: DataFrame.
        target_col: Name of the target column.
        feature_cols: List of feature column names.
        alpha: Regularization strength.
        
    Returns:
        dict: Lasso results (coefficients, non-zero count, cv_score).
    """
    X = df[feature_cols].dropna(axis=0, how='any')
    y = df.loc[X.index, target_col]
    
    if len(X) < 2:
        raise ValueError("Not enough data points for Lasso.")
        
    lasso = LassoCV(cv=5, random_state=RANDOM_SEED)
    lasso.fit(X, y)
    
    coeffs = dict(zip(feature_cols, lasso.coef_))
    non_zero = sum(1 for c in coeffs.values() if c != 0)
    
    return {
        "coefficients": coeffs,
        "non_zero_features": non_zero,
        "cv_score": float(lasso.score(X, y)),
        "alpha": float(lasso.alpha_)
    }

@log_operation
def save_lasso_results(lasso_results, output_path="data/processed/lasso_results.csv"):
    """Save Lasso results to a CSV file."""
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    rows = []
    for feature, coef in lasso_results["coefficients"].items():
        rows.append({
            "feature": feature,
            "coefficient": coef,
            "is_selected": 1 if coef != 0 else 0
        })
        
    df = pd.DataFrame(rows)
    df.to_csv(output_path, index=False)
    
    # Also save summary metrics
    summary = {
        "non_zero_features": lasso_results["non_zero_features"],
        "cv_score": lasso_results["cv_score"],
        "alpha": lasso_results["alpha"]
    }
    summary_path = output_path.replace(".csv", "_summary.json")
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)
        
    log_provenance(f"Lasso results saved to {output_path}")

@log_operation
def perform_residual_normality_validation(residuals):
    """
    Perform Shapiro-Wilk test for residual normality.
    
    Args:
        residuals: Array-like of residuals.
        
    Returns:
        dict: Validation results (shapiro_statistic, shapiro_p_value).
    """
    stat, p = stats.shapiro(residuals)
    return {
        "shapiro_statistic": float(stat),
        "shapiro_p_value": float(p)
    }

def run_analysis_pipeline():
    """
    Main pipeline to run correlation, regression, and VIF diagnostics.
    This function orchestrates the analysis steps and saves all required outputs.
    """
    log_pipeline_start("Analysis Pipeline")
    
    try:
        # 1. Load cleaned data
        df = load_processed_data()
        
        # 2. Check for zero variance
        zero_var_cols = check_zero_variance(df)
        log_zero_variance_warning(zero_var_cols)
        
        # 3. Compute Spearman correlation (Shannon vs Fluid Intelligence)
        # Assuming columns 'shannon_index' and 'fluid_intelligence_score' exist
        if 'shannon_index' in df.columns and 'fluid_intelligence_score' in df.columns:
            r, p, n = compute_spearman_correlation(df, 'shannon_index', 'fluid_intelligence_score')
            save_correlation_results(r, p, n)
        else:
            log_warning("Required columns for correlation analysis not found.")
        
        # 4. Prepare features for regression
        # Exclude target and ID columns
        exclude_from_features = ['participant_id', 'fluid_intelligence_score', 'shannon_index']
        if not DQS_REQUIRED and 'dietary_quality_score' in df.columns:
            exclude_from_features.append('dietary_quality_score')
            
        feature_cols = [c for c in df.select_dtypes(include=[np.number]).columns 
                        if c not in exclude_from_features]
        
        if not feature_cols:
            log_warning("No features available for regression.")
            feature_cols = []
        
        # 5. Run Multivariate Regression
        if feature_cols and 'fluid_intelligence_score' in df.columns:
            try:
                reg_results = run_multivariate_regression(df, 'fluid_intelligence_score', feature_cols)
                save_regression_results(reg_results)
            except Exception as e:
                log_warning(f"Regression failed: {e}")
        
        # 6. Run Lasso Regression
        if feature_cols and 'fluid_intelligence_score' in df.columns:
            try:
                lasso_results = run_lasso_regression(df, 'fluid_intelligence_score', feature_cols)
                save_lasso_results(lasso_results)
            except Exception as e:
                log_warning(f"Lasso failed: {e}")
        
        # 7. Calculate VIF (Multicollinearity Diagnostics) - T024b
        # We use the same feature set as regression
        if feature_cols:
            vif_dict = calculate_vif(df, exclude_cols=exclude_from_features)
            save_vif_results(vif_dict)
        else:
            log_warning("Skipping VIF calculation: no features available.")
            save_vif_results({})
            
        log_pipeline_end("Analysis Pipeline completed successfully.")
        
    except Exception as e:
        log_pipeline_end("Analysis Pipeline failed.", error=str(e))
        raise

def main():
    """Entry point for the analysis script."""
    run_analysis_pipeline()

if __name__ == "__main__":
    main()
