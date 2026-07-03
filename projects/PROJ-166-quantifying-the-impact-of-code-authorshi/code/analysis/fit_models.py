import os
import sys
import json
import logging
import warnings
from pathlib import Path
from typing import Dict, Any, Tuple, List

import pandas as pd
import numpy as np
import statsmodels.api as sm
from statsmodels.genmod.generalized_linear_model import GLM
from statsmodels.genmod.families import NegativeBinomial
from statsmodels.stats.outliers_influence import variance_inflation_factor

# Import config for paths
from config import ensure_directories

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_data(input_path: str) -> pd.DataFrame:
    """
    Load the merged dataset from the specified CSV path.
    """
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    df = pd.read_csv(input_path)
    logger.info(f"Loaded {len(df)} rows from {input_path}")
    return df

def filter_zero_kloc(df: pd.DataFrame) -> pd.DataFrame:
    """
    Exclude rows where kloc is zero (log(0) undefined).
    Logs a warning for each excluded row.
    """
    initial_count = len(df)
    # Filter out rows where kloc is 0 or NaN
    mask = (df['kloc'] > 0) & df['kloc'].notna()
    filtered_df = df[mask].copy()
    excluded_count = initial_count - len(filtered_df)
    
    if excluded_count > 0:
        logger.warning(f"Excluded {excluded_count} rows where kloc <= 0 or is null.")
    else:
        logger.info("No rows excluded based on kloc > 0 filter.")
    
    return filtered_df

def calculate_vif(df: pd.DataFrame, predictors: List[str]) -> Dict[str, float]:
    """
    Calculate Variance Inflation Factor (VIF) for each predictor.
    """
    # Ensure we have a constant term for VIF calculation if not already in predictors
    # VIF is typically calculated on the design matrix including the constant
    X = df[predictors].copy()
    
    # Add constant if not present (statsmodels vif usually expects it for intercept handling)
    # But standard VIF calculation on predictors usually doesn't include the intercept column in the matrix passed to vif
    # We will calculate VIF for the predictors provided.
    
    vif_data = {}
    for i, col in enumerate(predictors):
        try:
            # Calculate VIF for each feature
            # VIF for feature j = 1 / (1 - R_j^2) where R_j^2 is from regressing feature j on all other features
            vif = variance_inflation_factor(X.values, i)
            vif_data[col] = vif
        except Exception as e:
            logger.error(f"Error calculating VIF for {col}: {e}")
            vif_data[col] = np.nan
    
    return vif_data

def benjamini_hochberg(p_values: pd.Series) -> pd.Series:
    """
    Apply Benjamini-Hochberg correction to p-values.
    Returns adjusted p-values.
    """
    if len(p_values) == 0:
        return pd.Series([], dtype=float)
    
    # Sort p-values
    sorted_indices = p_values.argsort()
    sorted_p_values = p_values.iloc[sorted_indices]
    n = len(sorted_p_values)
    
    # Calculate BH adjusted p-values
    # Formula: p_adj[i] = p[i] * n / rank[i]
    # Where rank is 1-indexed position in sorted order
    # Ensure monotonicity: p_adj[i] <= p_adj[i+1]
    
    adjusted = np.empty(n)
    for i in range(n):
        rank = i + 1
        adjusted[i] = sorted_p_values.iloc[i] * n / rank
    
    # Enforce monotonicity (cumulative min from the end)
    adjusted = np.minimum.accumulate(adjusted[::-1])[::-1]
    
    # Cap at 1.0
    adjusted = np.minimum(adjusted, 1.0)
    
    # Reorder back to original indices
    result = pd.Series(0.0, index=p_values.index, dtype=float)
    result.iloc[sorted_indices] = adjusted
    
    return result

def fit_negative_binomial_glm(df: pd.DataFrame) -> Tuple[GLM, Dict[str, Any]]:
    """
    Fit a Negative-Binomial GLM with cve_count as response,
    author_count + controls as predictors, and log(kloc) as offset.
    Returns the fitted model and a dictionary of results.
    """
    # Define response and predictors
    # Response: cve_count
    # Predictors: author_count, language (one-hot), project_age, release_count
    # Offset: log(kloc)
    
    response_col = 'cve_count'
    # Controls: project_age, release_count. author_count is the main predictor.
    # We need to handle categorical 'language' by one-hot encoding.
    
    if 'language' in df.columns:
        # One-hot encode language
        df_encoded = pd.get_dummies(df, columns=['language'], drop_first=True)
        # Identify the new language columns
        lang_cols = [col for col in df_encoded.columns if col.startswith('language_')]
    else:
        df_encoded = df.copy()
        lang_cols = []
    
    # Define predictors
    # Main predictor: author_count
    # Controls: project_age, release_count
    # Plus the dummy language variables
    predictor_cols = ['author_count', 'project_age', 'release_count'] + lang_cols
    
    # Check if all predictor columns exist
    missing_cols = [col for col in predictor_cols if col not in df_encoded.columns]
    if missing_cols:
        raise ValueError(f"Missing predictor columns in data: {missing_cols}")
    
    X = df_encoded[predictor_cols]
    y = df_encoded[response_col]
    
    # Calculate offset: log(kloc)
    # kloc is already filtered > 0
    offset = np.log(df_encoded['kloc'])
    
    # Fit Negative Binomial GLM
    # Using statsmodels GLM with NegativeBinomial family
    # Note: statsmodels GLM with NegativeBinomial requires specifying link function (log is default)
    # and the family.
    
    try:
        # Add constant if needed? GLM with NegativeBinomial usually handles it via family or explicit constant.
        # We will add a constant term explicitly for the intercept.
        X_with_const = sm.add_constant(X)
        
        model = GLM(y, X_with_const, family=NegativeBinomial(), offset=offset)
        result = model.fit()
        
        convergence_status = result.converged
        
        logger.info(f"Model converged: {convergence_status}")
        logger.info(f"Deviance: {result.deviance}")
        
    except Exception as e:
        logger.error(f"Model fitting failed: {e}")
        # Return a dummy result or re-raise?
        # We'll return a result indicating failure
        convergence_status = False
        result = None
    
    return result, {'convergence_status': convergence_status, 'predictor_cols': predictor_cols}

def extract_results(result: GLM, df: pd.DataFrame, predictor_cols: List[str], p_values: pd.Series) -> Dict[str, Any]:
    """
    Extract coefficients, standard errors, p-values, CIs, and adjusted p-values.
    """
    if result is None:
        return {}
    
    summary = result.summary2().tables[1] # Get the coefficients table
    
    # Extract data from summary
    # The summary table has columns: 'Coef.', 'Std.Err.', 'z', 'P>|z|', '[0.025', '0.975]'
    # We need to map these to our output structure.
    
    coef_data = {}
    
    # Iterate over the rows of the summary table
    # The index of the summary table corresponds to the variable names
    for var_name in summary.index:
        if var_name == 'const':
            coef_data['Intercept'] = {
                'coefficient': summary.loc[var_name, 'Coef.'],
                'std_error': summary.loc[var_name, 'Std.Err.'],
                'p_value': summary.loc[var_name, 'P>|z|'],
                'ci_lower': summary.loc[var_name, '[0.025'],
                'ci_upper': summary.loc[var_name, '0.975]']
            }
        else:
            # Check if this is one of our predictors
            if var_name in predictor_cols or var_name.startswith('language_'):
                coef_data[var_name] = {
                    'coefficient': summary.loc[var_name, 'Coef.'],
                    'std_error': summary.loc[var_name, 'Std.Err.'],
                    'p_value': summary.loc[var_name, 'P>|z|'],
                    'ci_lower': summary.loc[var_name, '[0.025'],
                    'ci_upper': summary.loc[var_name, '0.975]']
                }
    
    # Calculate VIF
    # We need the original dataframe (before one-hot encoding if we want VIF on raw predictors? 
    # Or on the encoded ones? Usually VIF is calculated on the design matrix used in the model.
    # So we use the encoded dataframe and the predictor cols used in the model (including dummies).
    # But the function calculate_vif expects a dataframe and list of columns.
    # We should pass the encoded dataframe and the columns used in the model (excluding const).
    vif_predictors = [col for col in predictor_cols if col != 'const'] # const is not in predictor_cols usually
    # Actually, predictor_cols from fit function does not include 'const'.
    # But we added const in X_with_const.
    # So for VIF, we should use the columns from X (without const).
    # The predictor_cols passed to this function are the ones from the model (excluding const).
    
    # We need the dataframe used for fitting (df_encoded) to calculate VIF.
    # Let's assume we pass df_encoded to this function or reconstruct it.
    # For simplicity, we'll calculate VIF on the df used for fitting (which is passed as df in this context? No, df is the original).
    # We need to pass the encoded dataframe. Let's adjust the function call in main.
    
    # For now, we'll return the basic stats. VIF calculation will be done in main.
    return coef_data

def main():
    """
    Main entry point for fitting the model.
    """
    # Paths
    input_file = 'data/processed/repo_metrics.csv'
    output_file = 'data/processed/model_results.json'
    
    # Ensure output directory exists
    ensure_directories()
    
    # Load data
    try:
        df = load_data(input_file)
    except FileNotFoundError as e:
        logger.error(str(e))
        sys.exit(1)
    
    # Filter zero kloc
    df = filter_zero_kloc(df)
    
    if len(df) == 0:
        logger.error("No data remaining after filtering zero kloc.")
        sys.exit(1)
    
    # Fit model
    result, model_info = fit_negative_binomial_glm(df)
    convergence_status = model_info['convergence_status']
    predictor_cols = model_info['predictor_cols']
    
    if result is None:
        logger.error("Model fitting failed. Outputting failure status.")
        output_data = {
            'convergence_status': False,
            'coefficients': {},
            'vif_metrics': {},
            'message': 'Model fitting failed.'
        }
    else:
        # Extract p-values for BH correction
        # Get p-values from the result
        p_values = result.pvalues
        # Exclude intercept from BH correction? Usually we correct all p-values.
        # We'll correct all.
        
        # Apply BH correction
        # p_values is a Series with index as variable names
        adj_p_values = benjamini_hochberg(p_values)
        
        # Extract coefficients
        coef_data = {}
        for var_name, p_val in p_values.items():
            if var_name == 'const':
                name = 'Intercept'
            else:
                name = var_name
            
            coef_data[name] = {
                'coefficient': float(result.params[var_name]),
                'std_error': float(result.bse[var_name]),
                'p_value': float(p_val),
                'ci_lower': float(result.conf_int().loc[var_name, 0]),
                'ci_upper': float(result.conf_int().loc[var_name, 1]),
                'adj_p_value': float(adj_p_values[var_name])
            }
        
        # Calculate VIF
        # We need the encoded dataframe. Let's re-encode or pass it.
        # To avoid re-encoding, we can do it here again or pass it.
        # Since we need to pass the encoded dataframe to calculate_vif, and we don't have it here,
        # we will re-encode.
        
        df_encoded = pd.get_dummies(df, columns=['language'], drop_first=True)
        lang_cols = [col for col in df_encoded.columns if col.startswith('language_')]
        vif_predictors = ['author_count', 'project_age', 'release_count'] + lang_cols
        
        # Ensure all columns exist
        vif_predictors = [col for col in vif_predictors if col in df_encoded.columns]
        
        vif_metrics = calculate_vif(df_encoded, vif_predictors)
        
        output_data = {
            'convergence_status': convergence_status,
            'coefficients': coef_data,
            'vif_metrics': vif_metrics,
            'n_observations': len(df),
            'model_type': 'NegativeBinomialGLM'
        }
    
    # Save output
    with open(output_file, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    logger.info(f"Model results saved to {output_file}")

if __name__ == '__main__':
    main()
