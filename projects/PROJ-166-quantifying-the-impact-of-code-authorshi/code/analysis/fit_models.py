import os
import sys
import json
import logging
import warnings
from pathlib import Path

import pandas as pd
import numpy as np
import statsmodels.api as sm
from statsmodels.genmod.generalized_linear_model import GLM
from statsmodels.genmod.families import NegativeBinomial
from scipy.stats import chi2

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/fit_models.log', mode='a')
    ]
)
logger = logging.getLogger(__name__)

# Ensure directories exist (imported from config)
from config import ensure_directories
ensure_directories()

# Constants
DATA_PATH = Path("data/processed/repo_metrics.csv")
OUTPUT_PATH = Path("data/processed/model_results.json")
MIN_KLOC = 0.001  # Threshold to avoid log(0)

def load_data():
    """Load the merged dataset from repo_metrics.csv."""
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Input file not found: {DATA_PATH}. "
                                "Run the data pipeline (T009) first.")
    df = pd.read_csv(DATA_PATH)
    logger.info(f"Loaded {len(df)} rows from {DATA_PATH}")
    return df

def filter_zero_kloc(df):
    """
    Exclude rows where kloc is zero (log(0) undefined).
    Logs a warning for each excluded row.
    """
    initial_count = len(df)
    # Filter out rows where kloc <= 0
    mask = df['kloc'] > MIN_KLOC
    filtered_df = df[mask]
    excluded_count = initial_count - len(filtered_df)
    
    if excluded_count > 0:
        logger.warning(f"Excluded {excluded_count} rows with kloc <= {MIN_KLOC} (log(0) undefined).")
        # Log specific URLs if needed for debugging
        excluded_urls = df[~mask]['url'].tolist()
        logger.debug(f"Excluded URLs: {excluded_urls[:10]}...") # Log first 10
    else:
        logger.info("No rows excluded based on kloc threshold.")
    
    return filtered_df

def calculate_vif(df, predictors):
    """
    Calculate Variance Inflation Factor (VIF) for all predictors.
    
    Args:
        df: DataFrame containing the data
        predictors: List of column names used as predictors
        
    Returns:
        dict: VIF values for each predictor
    """
    if not predictors:
        return {}
    
    vif_data = {}
    # Add a constant for the intercept if not already present in the calculation logic
    # VIF is calculated on the design matrix excluding the intercept column usually, 
    # but here we calculate VIF for the specific predictor columns.
    
    X = df[predictors].dropna()
    if X.empty:
        return {p: np.nan for p in predictors}
        
    # Add constant for intercept in the auxiliary regression
    X_const = sm.add_constant(X)
    
    for col in predictors:
        try:
            # Regress col against all other predictors
            y = X[col]
            other_cols = [c for c in predictors if c != col]
            X_other = sm.add_constant(X[other_cols])
            
            model = sm.OLS(y, X_other).fit()
            vif = 1 / (1 - model.rsquared)
            vif_data[col] = vif
        except Exception as e:
            logger.warning(f"Could not calculate VIF for {col}: {e}")
            vif_data[col] = np.nan
    
    return vif_data

def benjamini_hochberg(p_values):
    """
    Apply Benjamini-Hochberg correction to p-values.
    
    Args:
        p_values: list or array of p-values
        
    Returns:
        list: adjusted p-values
    """
    p_values = np.array(p_values)
    n = len(p_values)
    if n == 0:
        return []
    
    # Sort indices
    sorted_indices = np.argsort(p_values)
    sorted_p = p_values[sorted_indices]
    
    # Calculate BH adjusted p-values
    # Formula: p_adj[i] = p[i] * n / (n - i)
    # We need to ensure monotonicity (cumulative min from right to left)
    adjusted = np.zeros(n)
    
    for i in range(n):
        rank = i + 1
        adjusted[i] = sorted_p[i] * n / rank
    
    # Enforce monotonicity: adjusted p-values must be non-decreasing
    # We process from largest rank to smallest
    for i in range(n-2, -1, -1):
        adjusted[i] = min(adjusted[i], adjusted[i+1])
    
    # Cap at 1.0
    adjusted = np.minimum(adjusted, 1.0)
    
    # Reorder back to original order
    result = np.zeros(n)
    result[sorted_indices] = adjusted
    
    return result.tolist()

def fit_negative_binomial_glm(df, predictors, offset_col):
    """
    Fit a Negative Binomial GLM with the specified formula.
    
    Args:
        df: DataFrame
        predictors: List of predictor column names (excluding offset)
        offset_col: Column name for the offset (log(kloc))
        
    Returns:
        results: statsmodels GLMResults object
        converged: bool
    """
    # Prepare data
    y = df['cve_count'].values
    X = df[predictors].values
    
    # Add constant for intercept
    X_const = sm.add_constant(X)
    
    # Calculate offset
    offset = np.log(df[offset_col].values)
    
    try:
        # Fit Negative Binomial GLM
        # family=NegativeBinomial() handles the dispersion parameter
        model = GLM(y, X_const, family=NegativeBinomial(), offset=offset)
        results = model.fit()
        converged = results.converged
        logger.info(f"Model convergence status: {converged}")
        return results, converged
    except Exception as e:
        logger.error(f"GLM fitting failed: {e}")
        return None, False

def extract_results(results, predictors, p_values_raw, vif_data, converged):
    """
    Extract coefficients, standard errors, p-values, CIs, and adjusted p-values.
    
    Args:
        results: GLMResults object
        predictors: List of predictor names (including 'const')
        p_values_raw: List of raw p-values corresponding to predictors
        vif_data: Dict of VIF values
        converged: bool
        
    Returns:
        dict: Structured results
    """
    if results is None:
        return {
            "convergence_status": converged,
            "coefficients": {},
            "standard_errors": {},
            "p_values": {},
            "adjusted_p_values": {},
            "confidence_intervals": {},
            "vif_metrics": {}
        }
    
    params = results.params
    bse = results.bse
    pvals = results.pvalues
    conf_int = results.conf_int()
    
    # Adjust p-values
    adjusted_p = benjamini_hochberg(pvals.tolist())
    
    results_dict = {
        "convergence_status": converged,
        "coefficients": {},
        "standard_errors": {},
        "p_values": {},
        "adjusted_p_values": {},
        "confidence_intervals": {},
        "vif_metrics": {}
    }
    
    for i, pred in enumerate(predictors):
        # Handle 'const' (intercept)
        key = "intercept" if pred == "const" else pred
        
        results_dict["coefficients"][key] = float(params[i])
        results_dict["standard_errors"][key] = float(bse[i])
        results_dict["p_values"][key] = float(pvals[i])
        results_dict["adjusted_p_values"][key] = float(adjusted_p[i])
        results_dict["confidence_intervals"][key] = [
            float(conf_int.iloc[i, 0]),
            float(conf_int.iloc[i, 1])
        ]
        results_dict["vif_metrics"][key] = float(vif_data.get(pred, np.nan))
    
    return results_dict

def main():
    """Main execution function for T017."""
    logger.info("Starting T017: Fit Negative Binomial GLM with offset")
    
    try:
        # 1. Load Data
        df = load_data()
        
        # 2. Filter Zero KLOC
        df_clean = filter_zero_kloc(df)
        if df_clean.empty:
            raise ValueError("No data remaining after filtering zero KLOC. Cannot fit model.")
        
        # 3. Define Predictors
        # Primary predictor: author_count
        # Controls: kloc (as offset, not predictor), language (if needed), project_age, release_count
        # Note: kloc is used as offset, so it is NOT in the predictors list for the GLM coefficients
        # unless we want to test its effect directly, but the task says use log(kloc) as offset.
        # We will include 'project_age' and 'release_count' as controls.
        # 'language' is categorical, need to handle it. For simplicity in this GLM, 
        # we might need to one-hot encode or select a primary language. 
        # Given the schema, let's assume we treat 'language' as a control if it's numeric or 
        # we drop it if not encoded. The prompt says "author_count + controls". 
        # Let's assume the merged data has 'project_age' and 'release_count' as numeric controls.
        # If 'language' is present, we might need to encode it. 
        # To be safe and strictly follow "author_count + controls", we'll use:
        predictors = ['author_count', 'project_age', 'release_count']
        
        # Check if predictors exist
        missing = [p for p in predictors if p not in df_clean.columns]
        if missing:
            logger.warning(f"Predictors {missing} not found in data. Removing from model.")
            predictors = [p for p in predictors if p in df_clean.columns]
        
        if not predictors:
            raise ValueError("No valid predictors found to fit the model.")
        
        # 4. Calculate VIF
        vif_data = calculate_vif(df_clean, predictors)
        logger.info(f"VIF calculated: {vif_data}")
        
        # 5. Fit Model
        results, converged = fit_negative_binomial_glm(df_clean, predictors, 'kloc')
        
        if results is None:
            raise RuntimeError("Model fitting failed.")
        
        # 6. Extract Results
        # Get p-values for BH correction
        pvals_list = results.pvalues.tolist()
        
        final_results = extract_results(
            results, 
            predictors, 
            pvals_list, 
            vif_data, 
            converged
        )
        
        # 7. Save Output
        OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(OUTPUT_PATH, 'w') as f:
            json.dump(final_results, f, indent=2)
        
        logger.info(f"Model results saved to {OUTPUT_PATH}")
        print(f"Success: Model results written to {OUTPUT_PATH}")
        
    except Exception as e:
        logger.error(f"Execution failed: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
