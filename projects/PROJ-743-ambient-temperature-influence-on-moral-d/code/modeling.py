"""
Modeling module for User Story 2: Mixed-Effects Regression.

Implements:
1. Log-transformation of response times.
2. Outlier handling (winsorization or exclusion based on config).
3. Fallback logic: If LMM (Linear Mixed-Effects) fails to converge, switch to GLMM
   (Generalized Linear Mixed-Effects) or a robust OLS with clustered errors.

This module assumes the merged dataset from T022 exists at data/processed/merged_dataset.parquet.
"""
import os
import sys
import logging
import json
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
from scipy import stats

# Import project utilities
from config import get_path_env_override
from setup_logging import get_model_diagnostics_logger
from loaders import load_parquet_as_df

# Configure logging
logger = get_model_diagnostics_logger()

# Constants
LOG_THRESHOLD_MS = 100.0  # Values below this might be suspicious after log transform
CONVERGENCE_TIMEOUT = 120 # seconds (conceptual, statsmodels handles this internally usually)

def load_merged_data() -> pd.DataFrame:
    """
    Loads the merged dataset from the processed directory.
    Raises FileNotFoundError if the file does not exist (fail loudly).
    """
    path_str = get_path_env_override("MERGED_DATA_PATH", "data/processed/merged_dataset.parquet")
    path = Path(path_str)
    
    if not path.exists():
        raise FileNotFoundError(f"Required merged dataset not found at {path}. "
                                "Please ensure T022 (output generation) has been executed successfully.")
    
    logger.info(f"Loading merged dataset from {path}")
    df = load_parquet_as_df(path)
    logger.info(f"Loaded {len(df)} records. Columns: {list(df.columns)}")
    return df

def log_transform_response_times(df: pd.DataFrame, column: str = "response_time_ms") -> Tuple[pd.DataFrame, pd.Series]:
    """
    Performs log-transformation of response times.
    Handles non-positive values by filtering them out or adding a small epsilon if strictly necessary,
    but primarily filters invalid data as per FR-002.
    
    Returns:
        Tuple of (cleaned_df, log_transformed_series)
    """
    df_clean = df.copy()
    
    # Filter out non-positive response times which cannot be log-transformed
    invalid_mask = df_clean[column] <= 0
    if invalid_mask.any():
        count_invalid = invalid_mask.sum()
        logger.warning(f"Found {count_invalid} records with response_time <= 0. Filtering them out for log transform.")
        df_clean = df_clean[~invalid_mask]
    
    # Perform log transform (natural log)
    # Adding a small epsilon if there are values extremely close to 0 but positive, 
    # though strictly log(x) is defined for x > 0.
    # We assume valid data is > 0 after the filter above.
    df_clean["log_response_time"] = np.log(df_clean[column])
    
    logger.info(f"Log transformation complete. New column 'log_response_time' created.")
    return df_clean, df_clean["log_response_time"]

def handle_outliers(df: pd.DataFrame, column: str = "log_response_time", 
                    method: str = "winsorize", 
                    lower_percentile: float = 1.0, 
                    upper_percentile: float = 99.0) -> pd.DataFrame:
    """
    Handles outliers in the log-transformed response times.
    
    Args:
        df: Input DataFrame.
        column: Column name to process.
        method: 'winsorize' or 'exclude'.
        lower_percentile: Lower bound percentile.
        upper_percentile: Upper bound percentile.
        
    Returns:
        DataFrame with outliers handled.
    """
    df_out = df.copy()
    
    if method == "winsorize":
        lower_val = np.percentile(df_out[column], lower_percentile)
        upper_val = np.percentile(df_out[column], upper_percentile)
        
        mask_low = df_out[column] < lower_val
        mask_high = df_out[column] > upper_val
        
        if mask_low.any() or mask_high.any():
            logger.info(f"Winsorizing {mask_low.sum()} low and {mask_high.sum()} high outliers.")
            df_out.loc[mask_low, column] = lower_val
            df_out.loc[mask_high, column] = upper_val
            
    elif method == "exclude":
        lower_val = np.percentile(df_out[column], lower_percentile)
        upper_val = np.percentile(df_out[column], upper_percentile)
        
        mask_keep = (df_out[column] >= lower_val) & (df_out[column] <= upper_val)
        dropped = (~mask_keep).sum()
        
        if dropped > 0:
            logger.info(f"Excluding {dropped} records due to outlier threshold.")
            df_out = df_out[mask_keep]
    else:
        logger.warning(f"Unknown outlier method: {method}. Skipping.")
        
    return df_out

def fit_lmm(df: pd.DataFrame, formula: str) -> Optional[Any]:
    """
    Attempts to fit a Linear Mixed-Effects Model using statsmodels.
    
    Args:
        df: DataFrame with prepared data.
        formula: Statsmodels formula string.
        
    Returns:
        Fitted model object or None if it fails.
    """
    logger.info(f"Fitting Linear Mixed-Effects Model with formula: {formula}")
    try:
        # Using MixedLM from statsmodels
        # Note: statsmodels MixedLM requires specific grouping
        model = smf.mixedlm(formula, df, groups=df["participant_id"])
        result = model.fit(maxiter=1000)
        
        if not result.converged:
            logger.warning("LMM did not converge. Switching to fallback.")
            return None
            
        logger.info("LMM converged successfully.")
        return result
    except Exception as e:
        logger.error(f"LMM fitting failed with error: {e}")
        return None

def fit_glmm_fallback(df: pd.DataFrame, formula: str) -> Optional[Any]:
    """
    Fallback to GLMM (Generalized Linear Mixed Model) or robust OLS if LMM fails.
    Since statsmodels GLMM implementation is limited compared to R, we often fallback 
    to a robust OLS with clustered standard errors as a valid alternative for 
    quantifying fixed effects when random effects estimation is unstable.
    
    This aligns with the Plan's "Scalable Strategy" for large datasets.
    """
    logger.info("Attempting GLMM / Robust OLS fallback.")
    
    # Try GLMM if available (statsmodels has limited GLMM support, often via GLM + groups)
    # For this implementation, we prioritize the robust OLS as the primary fallback 
    # because it guarantees convergence and provides cluster-robust SEs.
    
    try:
        # Fit OLS
        model = smf.ols(formula, data=df)
        result = model.fit()
        
        # Apply Clustered Robust Standard Errors
        # We assume 'region' or 'country' is the cluster variable. 
        # If not present, we use 'participant_id' as a proxy for clustering if needed,
        # but typically we cluster by the higher-level unit (e.g., country/region).
        cluster_col = "country_code" if "country_code" in df.columns else "region"
        if cluster_col not in df.columns:
            logger.warning(f"Cluster column '{cluster_col}' not found. Using 'participant_id' as fallback.")
            cluster_col = "participant_id"
        
        robust_result = result.get_robustcov_results(cov_type='cluster', groups=df[cluster_col])
        
        logger.info(f"Fallback Robust OLS with clustered SEs (cluster={cluster_col}) successful.")
        return robust_result
        
    except Exception as e:
        logger.error(f"Fallback model fitting failed: {e}")
        return None

def run_primary_modeling() -> Dict[str, Any]:
    """
    Orchestrates the modeling pipeline:
    1. Load data.
    2. Log-transform response times.
    3. Handle outliers.
    4. Fit LMM. If fails, fit GLMM/Robust OLS.
    5. Extract results.
    """
    # 1. Load
    df = load_merged_data()
    
    # 2. Log Transform
    df, _ = log_transform_response_times(df)
    
    # 3. Outliers
    df = handle_outliers(df, method="winsorize")
    
    # Define formula based on FR-004 and T026 description
    # Fixed effects: temperature, dilemma complexity, time-of-day, dilemma choice
    # Random effect: participant_id (if LMM)
    # We assume columns exist: 'temperature_celsius', 'dilemma_complexity', 'time_of_day', 'choice'
    # If 'choice' is categorical, we need to ensure it's treated as such.
    
    formula = "log_response_time ~ temperature_celsius + C(dilemma_complexity) + C(time_of_day) + C(choice)"
    
    # 4. Fit LMM
    lmm_result = fit_lmm(df, formula)
    model_type = "LMM"
    final_result = lmm_result
    
    if lmm_result is None:
        # 5. Fallback
        final_result = fit_glmm_fallback(df, formula)
        model_type = "Robust_OLS_Clustered"
        
    if final_result is None:
        raise RuntimeError("All modeling attempts (LMM and Fallback) failed.")
    
    # 6. Extract and Format Results
    results_dict = {
        "model_type": model_type,
        "n_observations": len(df),
        "formula": formula,
        "coefficients": {},
        "p_values": {},
        "std_errors": {},
        "convergence_status": "converged" if hasattr(final_result, 'converged') and final_result.converged else "fallback_used"
    }
    
    # Extract params
    params = final_result.params
    bse = final_result.bse
    pvalues = final_result.pvalues
    
    for var in params.index:
        if var != "Intercept":
            results_dict["coefficients"][var] = float(params[var])
            results_dict["std_errors"][var] = float(bse[var])
            results_dict["p_values"][var] = float(pvalues[var])
            
    # Save to JSON
    output_path = Path("results/stats/model_results.json")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w") as f:
        json.dump(results_dict, f, indent=2)
        
    logger.info(f"Model results saved to {output_path}")
    return results_dict

def main():
    """Entry point for the modeling task."""
    logger.info("Starting T025: Modeling (Log-transform & Convergence Fallback)")
    try:
        results = run_primary_modeling()
        logger.info(f"Modeling completed. Temperature coefficient: {results['coefficients'].get('temperature_celsius', 'N/A')}")
        return 0
    except Exception as e:
        logger.critical(f"Modeling pipeline failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
