import pandas as pd
import numpy as np
from scipy import stats
from scipy.stats import multitest
from statsmodels.stats.outliers_influence import variance_inflation_factor
from statsmodels.regression.linear_model import OLS
import json
import os
from typing import Dict, List, Optional, Tuple, Any

# Path constants
METRIC_FLAGS_PATH = "data/processed/metric_flags.json"
RESULTS_PATH = "data/processed/correlation_results.csv"
DATA_SOURCE_LABEL_KEY = "data_source"

def load_metric_flags() -> Dict[str, bool]:
    """
    Load zero-variance metric flags from the shared state file.
    Returns a dictionary mapping metric name -> True if flagged as non-informative.
    """
    if not os.path.exists(METRIC_FLAGS_PATH):
        return {}
    
    try:
        with open(METRIC_FLAGS_PATH, 'r') as f:
            data = json.load(f)
            # Expecting structure: {"non_informative": ["metric_name", ...]}
            return {name: True for name in data.get("non_informative", [])}
    except (json.JSONDecodeError, IOError):
        return {}

def calculate_spearman_correlations(
    df: pd.DataFrame, 
    metric_col: str, 
    target_col: str,
    flagged_metrics: Dict[str, bool]
) -> Tuple[float, float]:
    """
    Calculate Spearman correlation between a metric and entrainment strength.
    Skips calculation if the metric is flagged as non-informative (zero variance).
    
    Returns:
        Tuple (r_value, p_value)
    """
    if metric_col in flagged_metrics:
        # Return NaN to indicate no calculation performed
        return np.nan, np.nan
    
    if metric_col not in df.columns or target_col not in df.columns:
        raise ValueError(f"Columns {metric_col} or {target_col} not found in dataframe.")
    
    # Drop NaNs for calculation
    valid_data = df[[metric_col, target_col]].dropna()
    if len(valid_data) < 3:
        return np.nan, np.nan
    
    r, p = stats.spearmanr(valid_data[metric_col], valid_data[target_col])
    return r, p

def calculate_vif(df: pd.DataFrame, predictors: List[str]) -> float:
    """
    Calculate Variance Inflation Factor (VIF) for the first predictor in the list
    relative to the others.
    
    Args:
        df: DataFrame containing predictor columns
        predictors: List of predictor column names
    
    Returns:
        VIF value for the first predictor
    """
    if len(predictors) < 2:
        return 1.0
    
    # Add intercept for OLS
    X = df[predictors].dropna()
    if len(X) < len(predictors) + 1:
        return np.nan
    
    # Calculate VIF for the first predictor
    # VIF = 1 / (1 - R^2) where R^2 is from regressing predictor_0 on others
    y = X[predictors[0]]
    X_other = X[predictors[1:]]
    X_with_const = sm.add_constant(X_other)
    
    try:
        model = OLS(y, X_with_const).fit()
        r_squared = model.rsquared
        vif = 1.0 / (1.0 - r_squared)
        return vif
    except Exception:
        return np.nan

def run_correlation_analysis(
    df: pd.DataFrame, 
    metric_cols: List[str], 
    target_col: str
) -> pd.DataFrame:
    """
    Run correlation analysis for multiple metrics against the target.
    
    Args:
        df: Input dataframe with metrics and target
        metric_cols: List of metric column names
        target_col: Name of the entrainment metric column
    
    Returns:
        DataFrame with correlation results
    """
    flagged_metrics = load_metric_flags()
    results = []
    
    # Calculate VIF if we have multiple predictors
    vif_value = 1.0
    collinearity_warning = False
    
    if len(metric_cols) >= 2:
        # Clean data for VIF calculation
        clean_df = df[metric_cols].dropna()
        if len(clean_df) >= len(metric_cols) + 1:
            vif_value = calculate_vif(clean_df, metric_cols)
            collinearity_warning = vif_value > 5
    
    for metric in metric_cols:
        r, p_raw = calculate_spearman_correlations(df, metric, target_col, flagged_metrics)
        
        results.append({
            "metric": metric,
            "raw_p": p_raw,
            "r_value": r,
            "vif_value": vif_value,
            "collinearity_warning": collinearity_warning
        })
    
    return pd.DataFrame(results)

def generate_correlation_results_csv(
    df: pd.DataFrame,
    metric_cols: List[str],
    target_col: str,
    data_source: str = "Simulated"
) -> None:
    """
    Generate the final correlation results CSV with Holm-Bonferroni correction.
    
    This function:
    1. Calculates Spearman correlations
    2. Calculates VIF
    3. Applies Holm-Bonferroni correction
    4. Determines significance
    5. Saves to data/processed/correlation_results.csv
    
    Args:
        df: Input dataframe
        metric_cols: List of metric column names
        target_col: Target column name
        data_source: Label for the data source ("Real" or "Simulated")
    """
    # Run initial analysis
    analysis_df = run_correlation_analysis(df, metric_cols, target_col)
    
    # Filter out NaN p-values for correction calculation
    valid_p_values = analysis_df["raw_p"].dropna()
    
    if len(valid_p_values) > 0:
        # Apply Holm-Bonferroni correction
        # We need to map the corrected p-values back to the original rows
        # multitest.multipletests returns (reject, p_corrected, p_raw, alphacSidak)
        # We only need p_corrected
        _, p_corrected, _, _ = multitest.multipletests(
            valid_p_values, 
            method='holm', 
            alpha=0.05
        )
        
        # Create a mapping from index to corrected p-value
        valid_indices = valid_p_values.index
        corrected_map = dict(zip(valid_indices, p_corrected))
        
        # Apply corrected p-values to the dataframe
        analysis_df["adjusted_p_value"] = analysis_df["raw_p"].apply(
            lambda x: corrected_map.get(x.name) if pd.notna(x) and x.name in corrected_map else np.nan
        )
    else:
        analysis_df["adjusted_p_value"] = np.nan
    
    # Determine significance based on adjusted p-values
    analysis_df["is_significant"] = analysis_df["adjusted_p_value"] < 0.05
    
    # Ensure collinearity_warning is boolean
    analysis_df["collinearity_warning"] = analysis_df["collinearity_warning"].astype(bool)
    
    # Add data source label
    analysis_df["data_source"] = data_source
    
    # Reorder columns to match acceptance criteria
    final_columns = [
        "metric", "data_source", "r_value", "raw_p", "adjusted_p_value", 
        "is_significant", "vif_value", "collinearity_warning"
    ]
    
    # Ensure all columns exist
    for col in final_columns:
        if col not in analysis_df.columns:
            analysis_df[col] = np.nan
    
    output_df = analysis_df[final_columns]
    
    # Ensure correct directory exists
    os.makedirs(os.path.dirname(RESULTS_PATH), exist_ok=True)
    
    # Save to CSV
    output_df.to_csv(RESULTS_PATH, index=False)
    
    print(f"Correlation results saved to {RESULTS_PATH}")
    return output_df

def main():
    """
    Main entry point for running the correlation analysis.
    This is typically called by main.py orchestration.
    """
    # Example usage for testing purposes
    print("Analysis module loaded. Call generate_correlation_results_csv with data.")

# Import sm for VIF calculation if not already available
try:
    from statsmodels.regression.linear_model import OLS
    from statsmodels.tools import add_constant as sm_add_const
    import statsmodels.api as sm
except ImportError:
    # Fallback if statsmodels is not fully available (should not happen in prod)
    sm = None

# Re-define calculate_vif to handle imports properly
def calculate_vif(df: pd.DataFrame, predictors: List[str]) -> float:
    """
    Calculate Variance Inflation Factor (VIF) for the first predictor in the list
    relative to the others.
    """
    if len(predictors) < 2:
        return 1.0
    
    X = df[predictors].dropna()
    if len(X) < len(predictors) + 1:
        return np.nan
    
    y = X[predictors[0]]
    X_other = X[predictors[1:]]
    
    try:
        X_with_const = sm.add_constant(X_other)
        model = OLS(y, X_with_const).fit()
        r_squared = model.rsquared
        vif = 1.0 / (1.0 - r_squared)
        return vif
    except Exception:
        return np.nan
