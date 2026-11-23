import os
import sys
import json
import logging
import warnings
from pathlib import Path

import pandas as pd
import numpy as np
import statsmodels.api as sm
from statsmodels.stats.outliers_influence import variance_inflation_factor
from scipy.stats import chi2

from config import ensure_directories

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/analysis.log')
    ]
)
logger = logging.getLogger(__name__)

# Constants
DATA_PATH = Path('data/processed/repo_metrics_clean.csv')
OUTPUT_PATH = Path('data/processed/model_results_raw.json')
VIF_THRESHOLD = 5.0

def load_data():
    """Load the cleaned repository metrics dataset."""
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Data file not found: {DATA_PATH}. Run T014 first.")
    df = pd.read_csv(DATA_PATH)
    logger.info(f"Loaded {len(df)} rows from {DATA_PATH}")
    return df

def filter_zero_kloc(df):
    """Exclude rows where kloc <= 0 as per T017 requirements."""
    initial_count = len(df)
    df = df[df['kloc'] > 0].copy()
    excluded = initial_count - len(df)
    if excluded > 0:
        logger.warning(f"Excluded {excluded} rows with kloc <= 0")
    return df

def calculate_vif(df, predictors):
    """
    Calculate Variance Inflation Factor (VIF) for specified predictors.
    
    Args:
        df: DataFrame containing the data
        predictors: List of column names to calculate VIF for
        
    Returns:
        dict: Mapping of predictor name to VIF value
    """
    vif_data = {}
    # Add a constant for the intercept if not present in the calculation
    # VIF calculation typically uses the design matrix without the intercept column itself
    # but we need the intercept for the regression context. 
    # For VIF, we regress each predictor against all others.
    
    X = df[predictors].values
    
    # Check for constant columns or NaNs
    if np.isnan(X).any():
        logger.warning("NaN values found in predictor columns for VIF calculation.")
        # Handle NaNs by dropping rows for VIF calculation only
        valid_mask = ~np.isnan(X).any(axis=1)
        X = X[valid_mask]
        df_vif = df[valid_mask]
    else:
        df_vif = df

    for i, col in enumerate(predictors):
        try:
            # VIF for column i: regress col_i against all other predictors
            y = X[:, i]
            # Create X_matrix without the i-th column
            X_other = np.delete(X, i, axis=1)
            
            # Add constant for intercept in the auxiliary regression
            X_other_const = sm.add_constant(X_other)
            
            # Fit OLS
            model = sm.OLS(y, X_other_const).fit()
            vif = 1 / (1 - model.rsquared)
            vif_data[col] = vif
        except Exception as e:
            logger.error(f"Error calculating VIF for {col}: {e}")
            vif_data[col] = np.nan

    return vif_data

def fit_negative_binomial_glm(df, predictors, formula_str):
    """
    Fit a Negative Binomial GLM.
    
    Args:
        df: DataFrame
        predictors: List of predictor column names
        formula_str: Statsmodels formula string
        
    Returns:
        fitted model object
    """
    # Ensure target is integer
    df['cve_count'] = df['cve_count'].astype(int)
    
    # Prepare formula
    # The formula_str should already include the log(kloc) term if needed
    # e.g., "cve_count ~ author_count + project_age + C(primary_language) + release_count + np.log(kloc)"
    
    try:
        model = sm.GLM(
            df['cve_count'],
            sm.add_constant(df[predictors]), # Note: If formula uses strings, use from_formula
            family=sm.families.NegativeBinomial()
        )
        # If using formula string directly:
        result = sm.GLM.from_formula(
            formula_str,
            data=df,
            family=sm.families.NegativeBinomial()
        ).fit()
        return result
    except Exception as e:
        logger.error(f"GLM fitting failed: {e}")
        return None

def benjamini_hochberg(p_values):
    """
    Apply Benjamini-Hochberg correction to a list of p-values.
    
    Args:
        p_values: List of raw p-values
        
    Returns:
        List of adjusted p-values
    """
    p_values = np.array(p_values)
    n = len(p_values)
    if n == 0:
        return []
    
    # Sort p-values and keep original indices
    sorted_indices = np.argsort(p_values)
    sorted_p = p_values[sorted_indices]
    
    # Calculate BH adjusted p-values
    adjusted_p = np.zeros(n)
    for i in range(n):
        adjusted_p[sorted_indices[i]] = min(1, sorted_p[i] * n / (i + 1))
    
    # Ensure monotonicity (cumulative min from the end)
    for i in range(n - 2, -1, -1):
        adjusted_p[sorted_indices[i]] = min(adjusted_p[sorted_indices[i]], adjusted_p[sorted_indices[i+1]])
        
    return adjusted_p.tolist()

def extract_results(model_result, vif_data, high_collinearity_flag):
    """
    Extract coefficient, standard error, p-value, and CI from the fitted model.
    
    Args:
        model_result: Fitted GLM result object
        vif_data: Dictionary of VIF values
        high_collinearity_flag: Boolean indicating if high collinearity was detected
        
    Returns:
        dict: Extracted results
    """
    if model_result is None:
        return {
            "author_count_coefficient": None,
            "std_err": None,
            "p_value": None,
            "ci_95_lower": None,
            "ci_95_upper": None,
            "vif": vif_data,
            "convergence_status": False,
            "high_collinearity_warning": high_collinearity_flag
        }

    try:
        params = model_result.params
        bse = model_result.bse
        pvalues = model_result.pvalues
        conf_int = model_result.conf_int()

        # Extract author_count coefficient specifically
        # Assuming 'author_count' is in the formula
        author_coeff = params.get('author_count', None)
        author_se = bse.get('author_count', None)
        author_pval = pvalues.get('author_count', None)
        
        if author_coeff is not None:
            ci_lower = conf_int.loc['author_count', 0]
            ci_upper = conf_int.loc['author_count', 1]
        else:
            ci_lower = None
            ci_upper = None

        return {
            "author_count_coefficient": float(author_coeff) if author_coeff is not None else None,
            "std_err": float(author_se) if author_se is not None else None,
            "p_value": float(author_pval) if author_pval is not None else None,
            "ci_95_lower": float(ci_lower) if ci_lower is not None else None,
            "ci_95_upper": float(ci_upper) if ci_upper is not None else None,
            "vif": {k: float(v) for k, v in vif_data.items()},
            "convergence_status": True,
            "high_collinearity_warning": high_collinearity_flag
        }
    except Exception as e:
        logger.error(f"Error extracting results: {e}")
        return {
            "author_count_coefficient": None,
            "std_err": None,
            "p_value": None,
            "ci_95_lower": None,
            "ci_95_upper": None,
            "vif": vif_data,
            "convergence_status": False,
            "high_collinearity_warning": high_collinearity_flag
        }

def main():
    """Main execution function for T017 with T035 VIF check integration."""
    ensure_directories()
    
    logger.info("Starting model fitting with collinearity check (T035)...")
    
    # 1. Load Data
    df = load_data()
    
    # 2. Filter zero kloc
    df = filter_zero_kloc(df)
    if len(df) == 0:
        logger.error("No data remaining after filtering zero kloc.")
        return

    # 3. Define Predictors and Formula
    # Formula: cve_count ~ author_count + project_age + C(primary_language) + release_count + np.log(kloc)
    # We need to identify the numeric predictors for VIF calculation.
    # C(primary_language) is categorical, so we exclude it from VIF or handle it differently.
    # T035 specifically asks for VIF on 'author_count' and 'kloc'.
    
    predictors_for_vif = ['author_count', 'kloc']
    
    # Filter to rows where these predictors are valid for VIF
    df_vif = df.dropna(subset=predictors_for_vif)
    
    if len(df_vif) < 2:
        logger.warning("Insufficient data for VIF calculation.")
        vif_data = {p: np.nan for p in predictors_for_vif}
        high_collinearity = False
    else:
        vif_data = calculate_vif(df_vif, predictors_for_vif)
        
        # Check for high collinearity
        high_collinearity = False
        for col, val in vif_data.items():
            if not np.isnan(val) and val > VIF_THRESHOLD:
                logger.warning(f"High collinearity detected for {col}: VIF = {val:.2f} (threshold: {VIF_THRESHOLD})")
                high_collinearity = True
        
        if high_collinearity:
            logger.warning("Proceeding with model fitting despite high collinearity warning.")

    # 4. Fit Model
    formula = "cve_count ~ author_count + project_age + C(primary_language) + release_count + np.log(kloc)"
    model_result = fit_negative_binomial_glm(df, predictors_for_vif, formula)
    
    # 5. Extract Results
    results = extract_results(model_result, vif_data, high_collinearity)
    
    # 6. Save Output
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Model results saved to {OUTPUT_PATH}")
    logger.info(f"High collinearity warning: {high_collinearity}")

if __name__ == "__main__":
    main()