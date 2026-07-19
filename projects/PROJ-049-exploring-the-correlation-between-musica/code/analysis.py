import os
import logging
import pandas as pd
import numpy as np
from scipy.stats import spearmanr
from statsmodels.stats.outliers_influence import variance_inflation_factor
from statsmodels.regression.linear_model import OLS
from statsmodels.tools import add_constant
from typing import Tuple, List, Dict, Any, Optional
import json

# Ensure utils is importable if run as script, though typically in package
try:
    from utils import setup_logging
except ImportError:
    # Fallback for direct script execution if package structure isn't fully set up
    import sys
    sys.path.insert(0, os.path.dirname(__file__))
    from utils import setup_logging

logger = setup_logging()

def log_transform_column(df: pd.DataFrame, column: str) -> pd.DataFrame:
    """
    Log-transforms a numeric column in place.
    Handles zeros and negative values by adding 1 before log.
    """
    if column not in df.columns:
        raise ValueError(f"Column {column} not found in dataframe")
    
    logger.info(f"Log-transforming column: {column}")
    df[column] = df[column].apply(lambda x: np.log1p(x) if x >= 0 else np.log1p(abs(x)))
    return df

def compute_spearman_correlations(df: pd.DataFrame, traits: List[str], genres: List[str], target_col: str) -> pd.DataFrame:
    """
    Computes Spearman correlations between personality traits and a target variable (e.g., log-listening minutes)
    for each genre.
    """
    results = []
    for trait in traits:
        for genre in genres:
            col_name = f"{trait}_{genre}"
            if col_name not in df.columns or target_col not in df.columns:
                continue
            
            # Drop NaNs for this pair
            valid_data = df[[col_name, target_col]].dropna()
            if len(valid_data) < 3:
                continue

            rho, p_value = spearmanr(valid_data[col_name], valid_data[target_col])
            results.append({
                'trait': trait,
                'genre': genre,
                'rho': rho,
                'p_value': p_value,
                'n_obs': len(valid_data)
            })
    
    return pd.DataFrame(results)

def detect_collinearity(df: pd.DataFrame, predictors: List[str], threshold: float = 5.0) -> Tuple[List[str], Dict[str, float]]:
    """
    Detects collinear predictors using Variance Inflation Factor (VIF).
    Returns list of predictors to drop and their VIF scores.
    """
    if len(predictors) < 2:
        return [], {}
    
    X = df[predictors].dropna()
    if len(X) < 2:
        return [], {}
    
    vif_data = {}
    for i, col in enumerate(X.columns):
        vif = variance_inflation_factor(X.values, i)
        vif_data[col] = vif
    
    to_drop = [col for col, vif in vif_data.items() if vif > threshold]
    logger.warning(f"Detected collinearity (VIF > {threshold}): {to_drop}")
    
    return to_drop, vif_data

def run_multiple_linear_regression(df: pd.DataFrame, target: str, predictors: List[str], covariates: List[str]) -> Tuple[Dict[str, float], str]:
    """
    Runs a multiple linear regression for a specific target against predictors and covariates.
    Handles collinearity by dropping high VIF predictors.
    Returns coefficients and the model definition string.
    """
    # Combine predictors and covariates
    all_vars = list(set(predictors + covariates))
    
    # Check for collinearity among predictors (covariates are usually kept unless extreme)
    # We check VIF on all variables to be safe, but prioritize dropping from predictors
    cols_to_drop, vif_scores = detect_collinearity(df, all_vars, threshold=5.0)
    
    # If high VIF, drop them
    final_vars = [v for v in all_vars if v not in cols_to_drop]
    
    if len(final_vars) == 0:
        logger.error("All predictors dropped due to collinearity. Cannot run regression.")
        return {}, "No predictors"
    
    # Prepare data
    X = df[final_vars].dropna()
    y = df.loc[X.index, target].dropna()
    X = X.loc[y.index] # Align indices
    
    if len(X) < 10:
        logger.warning(f"Insufficient samples for regression on {target}.")
        return {}, f"Insufficient samples (n={len(X)})"
    
    X = add_constant(X)
    model = OLS(y, X).fit()
    
    coefficients = model.params.to_dict()
    # Remove 'const' from the model definition string if present, or keep it as intercept
    model_def_str = ", ".join([v for v in final_vars])
    
    return coefficients, model_def_str

def apply_fdr_correction(df: pd.DataFrame, p_value_col: str = 'p_value', alpha: float = 0.05) -> pd.DataFrame:
    """
    Applies Benjamini-Hochberg FDR correction to p-values.
    Adds 'adjusted_p_value' and 'is_significant' columns.
    """
    df = df.copy()
    df = df.sort_values(p_value_col)
    n = len(df)
    df['rank'] = range(1, n + 1)
    
    # BH procedure
    df['adjusted_p_value'] = (df[p_value_col] * n) / df['rank']
    # Ensure monotonicity (cumulative min from bottom up)
    df['adjusted_p_value'] = df['adjusted_p_value'].iloc[::-1].cummin().iloc[::-1]
    df['adjusted_p_value'] = df['adjusted_p_value'].clip(upper=1.0)
    
    df['is_significant'] = df['adjusted_p_value'] < alpha
    
    return df.drop(columns=['rank'])

def run_analysis(input_path: str, output_path: str) -> None:
    """
    Orchestrates the analysis:
    1. Loads merged data.
    2. Log-transforms listening minutes.
    3. Computes Spearman correlations.
    4. Runs regressions with demographic controls.
    5. Applies FDR correction.
    6. Saves final results.
    """
    logger.info(f"Starting analysis from {input_path}")
    
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    df = pd.read_csv(input_path)
    
    # Define columns based on expected schema from T017/T012
    traits = ['openness', 'conscientiousness', 'extraversion', 'agreeableness', 'neuroticism']
    # Assuming genre columns are named like 'genre_name_count' or similar in merged data
    # We need to identify genre columns dynamically or assume a pattern.
    # Based on T020, we assume the data has columns for traits and genre counts.
    
    # Identify genre columns (exclude known metadata/traits)
    exclude_cols = set(traits + ['user_id', 'age', 'gender', 'country', 'listening_minutes'])
    genre_cols = [col for col in df.columns if col not in exclude_cols and col != 'listening_minutes']
    
    # Ensure listening_minutes exists and log transform
    if 'listening_minutes' not in df.columns:
        # Fallback or error depending on strictness
        logger.warning("listening_minutes not found. Attempting to find similar column.")
        # This might need adjustment based on actual merged data schema
        raise ValueError("listening_minutes column not found in merged data")
    
    df = log_transform_column(df, 'listening_minutes')
    log_minutes_col = 'listening_minutes' # Assuming in-place update or new col name logic
    # If log_transform_column modifies in place, the column name remains 'listening_minutes'
    
    # 1. Compute Spearman Correlations
    logger.info("Computing Spearman correlations...")
    corr_results = compute_spearman_correlations(df, traits, genre_cols, log_minutes_col)
    
    # 2. Run Multiple Linear Regressions
    logger.info("Running multiple linear regressions...")
    regression_results = []
    covariates = ['age', 'gender', 'country'] # These might need one-hot encoding if not done in ingest
    # Assuming ingest already handled encoding or these are numeric/categorical handled by statsmodels
    # If 'gender' and 'country' are strings, OLS might fail. 
    # Let's assume T016/T012 ensured numeric encoding or one-hot encoding was done.
    # If they are strings, we must encode them here or assume they are already encoded.
    # For safety, let's check types.
    
    # If columns are categorical strings, we need to encode.
    # Assuming T016 handled this or the data is already numeric.
    # If not, we'll try to encode on the fly for the regression step.
    for col in covariates:
        if col in df.columns and df[col].dtype == 'object':
            logger.info(f"One-hot encoding {col} for regression")
            dummies = pd.get_dummies(df[col], prefix=col, drop_first=True)
            df = pd.concat([df, dummies], axis=1)
            # Remove original
            df.drop(columns=[col], inplace=True)
            # Update covariates list to include new dummy columns
            covariates = [c for c in covariates if c != col] + [c for c in dummies.columns]

    for trait in traits:
        # We are regressing trait on listening_minutes + covariates? 
        # Or listening_minutes on trait + covariates?
        # T020 says "correlation between trait and genre". T021 says "regression for each trait with age, gender, country as covariates".
        # Usually: Trait = beta0 + beta1*Genre + beta2*Covariates.
        # But T020 correlates Trait with Genre. T021 might be checking if Genre predicts Trait controlling for demographics.
        # Let's assume the model is: Trait ~ Genre + Covariates.
        # However, T020 output is trait-genre pairs.
        # Let's run regression: Trait ~ Genre + Covariates for each trait-genre pair.
        
        for genre in genre_cols:
            target = trait
            predictor = genre
            # Combine predictor and covariates
            # Ensure predictor exists
            if predictor not in df.columns:
                continue
                
            # Prepare predictors list for this model
            model_predictors = [predictor] + covariates
            
            # Filter for non-nulls in all involved columns
            cols_needed = [target] + model_predictors
            valid_df = df[cols_needed].dropna()
            
            if len(valid_df) < 10:
                continue
            
            coeffs, model_def = run_multiple_linear_regression(valid_df, target, [predictor], covariates)
            
            # Extract beta for the predictor (genre)
            beta = coeffs.get(predictor, 0.0)
            p_val = 0.0 # OLS p-values need extraction from summary if we want them per coefficient
            # Re-run OLS to get p-value for the specific coefficient
            try:
                X = valid_df[[predictor] + covariates]
                if len(X.columns) == 0:
                    continue
                X = add_constant(X)
                y = valid_df[target]
                model = OLS(y, X).fit()
                p_val = model.pvalues.get(predictor, 1.0)
            except Exception as e:
                logger.warning(f"Regression failed for {trait}-{genre}: {e}")
                p_val = 1.0
                beta = 0.0

            regression_results.append({
                'trait': trait,
                'genre': genre,
                'beta': beta,
                'p_value': p_val,
                'model_definition': model_def
            })

    reg_df = pd.DataFrame(regression_results)
    
    # Merge correlation and regression results?
    # T024 asks for: rho, p-value, adjusted p-value, is_significant, beta coefficients, model_definition
    # We have corr_results (rho, p) and reg_df (beta, p, model_def)
    
    # Merge on trait, genre
    final_df = pd.merge(corr_results, reg_df[['trait', 'genre', 'beta', 'model_definition']], on=['trait', 'genre'], how='left')
    
    # Apply FDR correction on the correlation p-values (as per T023)
    # T023 says "Apply FDR correction to all p-values". Usually this is on the correlation test.
    # We'll apply it to the 'p_value' from correlation.
    if 'p_value' in final_df.columns:
        final_df = apply_fdr_correction(final_df, p_value_col='p_value')
    else:
        # If we merged and lost p_value? No, corr_results has it.
        pass
        
    # Ensure output columns match spec
    output_cols = ['trait', 'genre', 'rho', 'p_value', 'adjusted_p_value', 'is_significant', 'beta', 'model_definition']
    # Reorder and ensure existence
    for col in output_cols:
        if col not in final_df.columns:
            final_df[col] = np.nan
            
    final_df = final_df[output_cols]
    
    # Save to CSV
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    final_df.to_csv(output_path, index=False)
    logger.info(f"Analysis results saved to {output_path}")

def main():
    """Entry point for running analysis."""
    input_file = "data/processed/merged_data.csv"
    output_file = "data/processed/analysis_results.csv"
    
    # Allow override via environment or args if needed, but hardcode for task T024
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
    if len(sys.argv) > 2:
        output_file = sys.argv[2]
        
    run_analysis(input_file, output_file)

if __name__ == "__main__":
    main()