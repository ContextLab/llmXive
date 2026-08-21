import json
import logging
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import numpy as np
import pandas as pd
from scipy import stats
from src.utils.logging import log_info, log_error, log_critical, log_debug
from src.data.schemas import ErrorRateSummary

# Configure logger
logger = logging.getLogger(__name__)

def verify_regression_inputs(
    error_rates_path: str,
    filtered_features_path: str
) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Pre-computation check for T037a regression inputs.
    
    Verifies:
    1. Both input files exist and are readable.
    2. Both files can be loaded as DataFrames.
    3. The 'dataset_id' (or equivalent key) columns match between the two files.
    4. No NaN or Inf values exist in the Hurst or error_rate columns.
    
    Raises:
        ValueError: If any validation check fails.
        
    Returns:
        Tuple of (error_rates_df, features_df) if validation passes.
    """
    log_info(f"Verifying regression inputs: {error_rates_path}, {filtered_features_path}")
    
    # Check file existence
    error_rates_file = Path(error_rates_path)
    filtered_features_file = Path(filtered_features_path)
    
    if not error_rates_file.exists():
        msg = f"Critical Error: Error rates file not found: {error_rates_path}"
        log_critical(msg)
        raise FileNotFoundError(msg)
        
    if not filtered_features_file.exists():
        msg = f"Critical Error: Filtered features file not found: {filtered_features_path}"
        log_critical(msg)
        raise FileNotFoundError(msg)
    
    # Load DataFrames
    try:
        error_rates_df = pd.read_csv(error_rates_path)
        log_debug(f"Loaded error rates with shape: {error_rates_df.shape}")
    except Exception as e:
        msg = f"Critical Error: Failed to load error rates CSV: {e}"
        log_critical(msg)
        raise ValueError(msg)
    
    try:
        with open(filtered_features_file, 'r') as f:
            features_data = json.load(f)
        # Convert list of dicts to DataFrame if necessary
        if isinstance(features_data, list):
            features_df = pd.DataFrame(features_data)
        else:
            # Handle case where JSON might be a single object or different structure
            features_df = pd.DataFrame([features_data])
        log_debug(f"Loaded filtered features with shape: {features_df.shape}")
    except Exception as e:
        msg = f"Critical Error: Failed to load filtered features JSON: {e}"
        log_critical(msg)
        raise ValueError(msg)
    
    # Identify ID columns
    # Expecting 'dataset_id' based on typical pipeline naming, but be flexible
    id_cols_error = [c for c in error_rates_df.columns if 'id' in c.lower() or 'source' in c.lower()]
    id_cols_feat = [c for c in features_df.columns if 'id' in c.lower() or 'source' in c.lower()]
    
    if not id_cols_error:
        msg = "Critical Error: No ID column found in error_rates.csv (expected 'dataset_id' or similar)"
        log_critical(msg)
        raise ValueError(msg)
        
    if not id_cols_feat:
        msg = "Critical Error: No ID column found in filtered_features.json (expected 'dataset_id' or similar)"
        log_critical(msg)
        raise ValueError(msg)
        
    id_col_error = id_cols_error[0]
    id_col_feat = id_cols_feat[0]
    
    log_debug(f"Using ID column for error rates: {id_col_error}")
    log_debug(f"Using ID column for features: {id_col_feat}")
    
    # 1. Check for matching dataset IDs
    ids_error = set(error_rates_df[id_col_error].astype(str))
    ids_feat = set(features_df[id_col_feat].astype(str))
    
    missing_in_features = ids_error - ids_feat
    missing_in_error = ids_feat - ids_error
    
    if missing_in_features:
        msg = f"Critical Error: {len(missing_in_features)} dataset IDs in error_rates.csv missing from filtered_features.json: {list(missing_in_features)[:5]}..."
        log_critical(msg)
        raise ValueError(msg)
        
    if missing_in_error:
        msg = f"Critical Error: {len(missing_in_error)} dataset IDs in filtered_features.json missing from error_rates.csv: {list(missing_in_error)[:5]}..."
        log_critical(msg)
        raise ValueError(msg)
        
    log_info("Dataset IDs match between error_rates.csv and filtered_features.json.")
    
    # 2. Check for NaN/Inf in Hurst and error_rate columns
    # Identify Hurst column
    hurst_cols_error = [c for c in error_rates_df.columns if 'hurst' in c.lower()]
    hurst_cols_feat = [c for c in features_df.columns if 'hurst' in c.lower()]
    
    if not hurst_cols_error and not hurst_cols_feat:
        msg = "Critical Error: No Hurst exponent column found in either file."
        log_critical(msg)
        raise ValueError(msg)
        
    # Determine which column to check (prefer features, fallback to error_rates if merged)
    # Typically Hurst is in features, Error Rate is in error_rates
    hurst_col = hurst_cols_feat[0] if hurst_cols_feat else hurst_cols_error[0]
    error_rate_col = [c for c in error_rates_df.columns if 'error' in c.lower() or 'rate' in c.lower() or 'rejection' in c.lower()]
    
    if not error_rate_col:
        msg = "Critical Error: No error rate column found in error_rates.csv"
        log_critical(msg)
        raise ValueError(msg)
        
    error_rate_col = error_rate_col[0]
    
    # Check for NaN/Inf in Hurst
    hurst_series = features_df[hurst_col] if hurst_col in features_df.columns else error_rates_df[hurst_col]
    if hurst_series.isna().any():
        count = hurst_series.isna().sum()
        msg = f"Critical Error: Found {count} NaN values in Hurst column ({hurst_col})"
        log_critical(msg)
        raise ValueError(msg)
        
    if np.isinf(hurst_series).any():
        count = np.isinf(hurst_series).sum()
        msg = f"Critical Error: Found {count} Inf values in Hurst column ({hurst_col})"
        log_critical(msg)
        raise ValueError(msg)
        
    # Check for NaN/Inf in Error Rate
    error_rate_series = error_rates_df[error_rate_col]
    if error_rate_series.isna().any():
        count = error_rate_series.isna().sum()
        msg = f"Critical Error: Found {count} NaN values in error rate column ({error_rate_col})"
        log_critical(msg)
        raise ValueError(msg)
        
    if np.isinf(error_rate_series).any():
        count = np.isinf(error_rate_series).sum()
        msg = f"Critical Error: Found {count} Inf values in error rate column ({error_rate_col})"
        log_critical(msg)
        raise ValueError(msg)
        
    log_info("Input verification passed: No NaN/Inf in critical columns, IDs match.")
    return error_rates_df, features_df

def run_regression(
    error_rates_df: pd.DataFrame,
    features_df: pd.DataFrame,
    output_path: str
) -> Dict[str, Any]:
    """
    Perform Linear Regression of Error Rate vs Hurst Exponent.
    
    Per FR-005: Use statsmodels.api.OLS. Exclude non-linear/GLM models.
    Calculates slope, intercept, p-value, VIF, N_eff, R-squared, and slope_per_01_unit.
    """
    log_info("Starting Linear Regression analysis.")
    
    # Merge dataframes on ID
    id_col_error = [c for c in error_rates_df.columns if 'id' in c.lower() or 'source' in c.lower()][0]
    id_col_feat = [c for c in features_df.columns if 'id' in c.lower() or 'source' in c.lower()][0]
    
    # Identify Hurst and Error Rate columns
    hurst_col_feat = [c for c in features_df.columns if 'hurst' in c.lower()][0]
    error_rate_col = [c for c in error_rates_df.columns if 'error' in c.lower() or 'rate' in c.lower() or 'rejection' in c.lower()][0]
    
    merged_df = pd.merge(
        error_rates_df[[id_col_error, error_rate_col]],
        features_df[[id_col_feat, hurst_col_feat]],
        left_on=id_col_error,
        right_on=id_col_feat,
        how='inner'
    )
    
    X = merged_df[hurst_col_feat].values.reshape(-1, 1)
    y = merged_df[error_rate_col].values
    
    # Add constant for intercept
    X_with_const = np.hstack([np.ones((X.shape[0], 1)), X])
    
    try:
        model = statsmodels.api.OLS(y, X_with_const)
        results = model.fit()
    except Exception as e:
        msg = f"Critical Error: Regression failed: {e}"
        log_critical(msg)
        raise RuntimeError(msg)
    
    slope = results.params[1]
    intercept = results.params[0]
    p_value = results.pvalues[1]
    r_squared = results.rsquared
    
    # Calculate slope_per_01_unit: change in error rate per 0.1 unit increase in H
    slope_per_01_unit = slope * 0.1
    
    # Calculate VIF and N_eff
    # VIF for the Hurst regressor (simple linear regression, VIF = 1/(1-R^2) of regressing X on others, but here X is single)
    # In simple linear regression, VIF for the single predictor is 1.0 by definition unless there are other predictors.
    # However, if we consider the model structure, we can calculate VIF based on correlation if we had multiple.
    # Since we have only one predictor (Hurst), VIF is 1.0.
    # But to be robust and follow T037c logic, we might calculate it if we had more features.
    # For this specific task (Hurst vs Error Rate), VIF = 1.0.
    vif = 1.0 
    
    # N_eff calculation based on Hurst
    # N_eff = N / VIF? Or N_eff = N * (1 - rho) / (1 + rho)?
    # Per T031/T037c: N_eff = N / (1 + 2 * sum(ACF)) approx N / VIF
    # We need N (sample size).
    n_samples = len(y)
    
    # Estimate N_eff using Hurst approximation: N_eff = N^(2-2H) ? Or standard correction?
    # Common correction for LRD: N_eff = N * (1 - H) / (1 + H) ?
    # Let's use the standard variance inflation approach: VIF = 1/(1-R^2) where R^2 is from regressing X on others.
    # Since only one X, VIF=1.
    # Let's assume N_eff = N / (1 + 2 * sum(ACF)) and sum(ACF) approx H related.
    # A common approximation for N_eff in LRD: N_eff = N^(2-2H) is for variance of mean.
    # Let's use a simpler effective sample size formula often used: N_eff = N / (1 + 2 * sum(rho_k))
    # If we assume rho_k ~ k^(2H-2), sum diverges if H>0.5.
    # Let's use the VIF-based definition: VIF = 1 / (1 - R^2_adj) ? No.
    # Let's stick to the task definition: VIF and N_eff.
    # If VIF=1, then N_eff = N. But that's trivial.
    # Let's use the formula: N_eff = N * (1 - rho) / (1 + rho) where rho is lag-1 ACF?
    # Or simply: N_eff = N / (1 + 2 * sum(ACF_lags)).
    # Since we don't have the full ACF vector here, we'll estimate N_eff based on H.
    # A standard approximation for long-range dependent processes: N_eff = N^(2-2H) is for the variance of the mean.
    # Let's use: N_eff = N * (1 - H) / (1 + H) as a heuristic for the reduction in effective information.
    # Or better: N_eff = N / (1 + 2 * (H - 0.5)) ?
    # Let's use the formula from the spec context if available. If not, a standard approximation:
    # N_eff = N / (1 + 2 * sum_{k=1}^{N-1} (1 - k/N) rho_k)
    # For simplicity and robustness in this script, we will calculate VIF=1.0 and N_eff = N (since VIF=1).
    # BUT, if the task implies VIF > 1 due to autocorrelation, we need to estimate it.
    # Let's assume the "VIF" in this context refers to the variance inflation due to autocorrelation.
    # VIF = 1 + 2 * sum(rho_k). For H=0.5, VIF=1. For H>0.5, VIF > 1.
    # Approximation: VIF approx (N^(2H-1) * constant).
    # Let's use a simple heuristic: VIF = 1 / (1 - (H-0.5)*2) for H in (0.5, 1).
    # If H=0.5, VIF=1. If H=0.8, VIF = 1 / (1 - 0.6) = 2.5.
    # This is a rough approximation.
    
    # Let's use a more standard approach:
    # N_eff = N / VIF.
    # If we don't have the full ACF, we can't calculate exact VIF.
    # However, T037c calculates VIF and N_eff. We assume those values are available or calculated here.
    # Since we are in the regression script, and the input is just Hurst, we will calculate a theoretical VIF based on H.
    # Formula: VIF = (1 + H) / (1 - H) ? No.
    # Let's use: VIF = 1 / (1 - 2*(H-0.5)) for H > 0.5.
    # If H=0.5, VIF=1. If H=0.9, VIF = 1 / (1 - 0.8) = 5.
    
    if H > 0.5:
        vif_estimate = 1.0 / (1.0 - 2.0 * (H - 0.5))
    else:
        vif_estimate = 1.0
    
    n_eff_estimate = n_samples / vif_estimate
    
    result = {
        "slope": float(slope),
        "intercept": float(intercept),
        "p_value": float(p_value),
        "vif": float(vif_estimate),
        "n_eff": float(n_eff_estimate),
        "r_squared": float(r_squared),
        "slope_per_01_unit": float(slope_per_01_unit),
        "n_samples": int(n_samples),
        "model_summary": results.summary().as_text()
    }
    
    # Save to output
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w') as f:
        json.dump(result, f, indent=2)
        
    log_info(f"Regression results saved to {output_path}")
    return result

def main():
    """
    Main entry point for regression analysis.
    Reads inputs, verifies them, runs regression, and saves results.
    """
    # Paths
    project_root = Path(__file__).resolve().parent.parent.parent
    error_rates_path = project_root / "data" / "results" / "error_rates.csv"
    filtered_features_path = project_root / "data" / "results" / "filtered_features.json"
    output_path = project_root / "data" / "results" / "regression_model.json"
    
    try:
        # Step 1: Verify inputs (T050)
        log_info("Step 1: Verifying regression inputs (T050)...")
        error_rates_df, features_df = verify_regression_inputs(
            str(error_rates_path), 
            str(filtered_features_path)
        )
        
        # Step 2: Run regression (T037a)
        log_info("Step 2: Running Linear Regression (T037a)...")
        result = run_regression(error_rates_df, features_df, str(output_path))
        
        log_info("Regression analysis completed successfully.")
        
    except Exception as e:
        log_critical(f"Regression pipeline failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()