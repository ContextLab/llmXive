import os
import sys
import json
import logging
import warnings
from pathlib import Path
from typing import Dict, Any, Tuple, Optional, List

import pandas as pd
import numpy as np
import statsmodels.api as sm
from statsmodels.stats.outliers_influence import variance_inflation_factor

# Import config for paths
try:
    from config import ensure_directories
except ImportError:
    # Fallback for running as script or different import context
    from code.config import ensure_directories

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
INPUT_FILE = Path("data/processed/repo_metrics.csv")
OUTPUT_FILE = Path("data/processed/model_results.json")

def load_data() -> pd.DataFrame:
    """Load the merged dataset from disk."""
    if not INPUT_FILE.exists():
        raise FileNotFoundError(f"Input file {INPUT_FILE} not found. Run data ingestion pipeline first.")
    df = pd.read_csv(INPUT_FILE)
    logger.info(f"Loaded {len(df)} rows from {INPUT_FILE}")
    return df

def filter_zero_kloc(df: pd.DataFrame) -> pd.DataFrame:
    """
    Exclude rows where kloc is zero or NaN because log(0) is undefined.
    Logs a warning for excluded rows.
    """
    initial_count = len(df)
    # Filter out NaN and zero values in kloc
    mask = (df['kloc'].notna()) & (df['kloc'] > 0)
    filtered_df = df[mask].copy()
    excluded_count = initial_count - len(filtered_df)
    
    if excluded_count > 0:
        logger.warning(f"Excluded {excluded_count} rows with kloc <= 0 or NaN.")
    else:
        logger.info("No rows excluded due to zero/NaN kloc.")
        
    return filtered_df

def calculate_vif(df: pd.DataFrame, predictors: List[str]) -> Dict[str, float]:
    """
    Calculate Variance Inflation Factor (VIF) for each predictor.
    """
    vif_data = {}
    # Add constant for intercept if not present in predictors (statsmodels usually requires it for OLS, 
    # but GLM handles it differently. For VIF calculation, we need a matrix with intercept).
    # However, VIF is typically calculated on predictors excluding the intercept.
    X = df[predictors].copy()
    
    # Handle potential NaNs in predictors for VIF calculation
    if X.isnull().any().any():
        logger.warning("NaN values found in predictors for VIF calculation. Dropping rows with NaNs for VIF only.")
        X = X.dropna()
    
    if len(X) == 0:
        logger.error("No valid rows remaining for VIF calculation after dropping NaNs.")
        return {p: np.nan for p in predictors}

    # Add constant for VIF calculation (VIF is 1/(1-R^2) where R^2 is regressing one predictor on others)
    X_with_const = sm.add_constant(X)
    
    for col in predictors:
        try:
            # VIF calculation: regress col against all other predictors
            y = X_with_const[col]
            X_other = X_with_const.drop(columns=[col])
            model = sm.OLS(y, X_other).fit()
            vif = 1 / (1 - model.rsquared)
            vif_data[col] = vif
        except Exception as e:
            logger.error(f"Error calculating VIF for {col}: {e}")
            vif_data[col] = np.nan
    
    return vif_data

def benjamini_hochberg(p_values: List[float]) -> List[float]:
    """
    Apply Benjamini-Hochberg correction to a list of p-values.
    Returns adjusted p-values.
    """
    if not p_values:
        return []
    
    m = len(p_values)
    sorted_indices = np.argsort(p_values)
    sorted_p = np.array(p_values)[sorted_indices]
    
    # Calculate BH adjusted p-values
    # p_adj[i] = p[i] * m / (i + 1)
    # Then ensure monotonicity and cap at 1.0
    adjusted = np.zeros(m)
    for i in range(m):
        adjusted[i] = sorted_p[i] * m / (i + 1)
    
    # Enforce monotonicity (cumulative min from the end)
    for i in range(m - 2, -1, -1):
        adjusted[i] = min(adjusted[i], adjusted[i + 1])
    
    # Cap at 1.0
    adjusted = np.minimum(adjusted, 1.0)
    
    # Reorder to original indices
    final_adjusted = np.zeros(m)
    final_adjusted[sorted_indices] = adjusted
    
    return final_adjusted.tolist()

def fit_negative_binomial_glm(df: pd.DataFrame) -> Tuple[Any, bool]:
    """
    Fit a Negative Binomial GLM.
    Response: cve_count
    Predictors: unique_authors, primary_language (one-hot encoded), project_age, release_count
    Offset: log(kloc)
    """
    # Prepare predictors
    predictors = ['unique_authors', 'project_age', 'release_count']
    
    # One-hot encode primary_language
    df_encoded = pd.get_dummies(df, columns=['primary_language'], prefix='lang', drop_first=True)
    
    # Identify language columns
    lang_cols = [col for col in df_encoded.columns if col.startswith('lang_')]
    all_predictors = predictors + lang_cols
    
    # Filter for available columns
    available_predictors = [col for col in all_predictors if col in df_encoded.columns]
    
    if not available_predictors:
        raise ValueError("No valid predictors found after encoding.")
    
    X = df_encoded[available_predictors].copy()
    y = df_encoded['cve_count'].copy()
    
    # Create offset
    offset = np.log(df_encoded['kloc'])
    
    # Add constant
    X = sm.add_constant(X)
    
    # Fit model
    try:
        model = sm.GLM(
            y, 
            X, 
            family=sm.families.NegativeBinomial(),
            offset=offset
        )
        result = model.fit()
        converged = result.converged
        return result, converged
    except Exception as e:
        logger.error(f"Model fitting failed: {e}")
        return None, False

def extract_results(result: Any, predictors: List[str], vif_data: Dict[str, float], converged: bool) -> Dict[str, Any]:
    """
    Extract coefficients, standard errors, p-values, confidence intervals, and adjusted p-values.
    """
    if result is None:
        return {
            "convergence_status": False,
            "message": "Model did not converge or failed to fit.",
            "coefficients": {},
            "standard_errors": {},
            "p_values": {},
            "confidence_intervals": {},
            "adjusted_p_values": {},
            "vif_metrics": vif_data
        }
    
    params = result.params
    bse = result.bse
    pvalues = result.pvalues
    conf_int = result.conf_int()
    
    # Prepare lists for BH correction
    p_values_list = []
    coef_dict = {}
    se_dict = {}
    p_dict = {}
    ci_dict = {}
    
    # Iterate over predictors (skip constant for BH correction if desired, but usually we correct all)
    # The task asks for BH correction on "main model p-values". We'll include all non-constant.
    non_const_params = []
    
    for i, param_name in enumerate(params.index):
        if param_name == 'const':
            continue
        
        non_const_params.append(param_name)
        coef_dict[param_name] = float(params[param_name])
        se_dict[param_name] = float(bse[param_name])
        p_dict[param_name] = float(pvalues[param_name])
        
        ci_lower = float(conf_int.iloc[i, 0])
        ci_upper = float(conf_int.iloc[i, 1])
        ci_dict[param_name] = [ci_lower, ci_upper]
        
        p_values_list.append(float(pvalues[param_name]))
    
    # Apply BH correction
    adjusted_p_values = benjamini_hochberg(p_values_list)
    adj_p_dict = {name: val for name, val in zip(non_const_params, adjusted_p_values)}
    
    return {
        "convergence_status": converged,
        "coefficients": coef_dict,
        "standard_errors": se_dict,
        "p_values": p_dict,
        "confidence_intervals": ci_dict,
        "adjusted_p_values": adj_p_dict,
        "vif_metrics": vif_data,
        "n_obs": int(result.nobs)
    }

def main():
    """Main entry point for the model fitting task."""
    ensure_directories()
    
    logger.info("Starting model fitting task T017...")
    
    # 1. Load Data
    df = load_data()
    
    # 2. Filter Zero KLOC
    df_filtered = filter_zero_kloc(df)
    
    if len(df_filtered) == 0:
        logger.error("No data remaining after filtering zero kloc. Cannot fit model.")
        # Write empty result with failure status
        results = {
            "convergence_status": False,
            "message": "No data available after filtering.",
            "coefficients": {},
            "standard_errors": {},
            "p_values": {},
            "confidence_intervals": {},
            "adjusted_p_values": {},
            "vif_metrics": {}
        }
        with open(OUTPUT_FILE, 'w') as f:
            json.dump(results, f, indent=2)
        return
    
    # 3. Calculate VIF on the filtered data
    # Determine predictors for VIF (excluding offset and response)
    # We need to know what predictors will be used in the model.
    # Based on fit_negative_binomial_glm, we use unique_authors, project_age, release_count, and lang_*.
    # For VIF, we calculate on the numeric predictors first, then handle dummies if needed.
    # To be safe, we calculate VIF on the numeric subset first, or just pass the list to the function.
    # The VIF function handles encoding internally if we pass the full df? No, VIF expects numeric.
    # Let's prepare the numeric predictors for VIF calculation.
    numeric_predictors = ['unique_authors', 'project_age', 'release_count']
    # Ensure they exist
    numeric_predictors = [p for p in numeric_predictors if p in df_filtered.columns]
    
    vif_metrics = calculate_vif(df_filtered, numeric_predictors)
    
    # 4. Fit Model
    result, converged = fit_negative_binomial_glm(df_filtered)
    
    # 5. Extract Results
    # We need the list of predictors used in the model for extraction.
    # The extract_results function builds this list from the model result params.
    # But we need to pass the VIF data which was calculated on numeric predictors.
    # The VIF data keys might not match the model params keys (which include lang_*).
    # The task asks for VIF metrics. We include what we calculated.
    
    results = extract_results(result, numeric_predictors, vif_metrics, converged)
    
    # 6. Save Output
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Model results saved to {OUTPUT_FILE}")
    logger.info(f"Convergence Status: {converged}")
    
    if not converged:
        logger.error("Model failed to converge. Check data and specification.")

if __name__ == "__main__":
    main()
