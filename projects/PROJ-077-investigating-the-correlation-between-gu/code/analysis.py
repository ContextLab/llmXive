import os
import sys
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Tuple, Optional, Dict, Any

from config import INPUT_PATHS, RANDOM_SEED, SAMPLE_LIMIT, ensure_directories
from logging_config import get_logger, log_warning, log_provenance

logger = get_logger(__name__)

def load_processed_data() -> pd.DataFrame:
    """
    Load the cleaned dataset from data/processed/cleaned_data.csv.
    """
    input_path = Path(INPUT_PATHS['PROCESSED_DATA'])
    if not input_path.exists():
        raise FileNotFoundError(f"Processed data not found at {input_path}. "
                                "Run data ingestion pipeline first.")
    
    df = pd.read_csv(input_path)
    logger.info(f"Loaded {len(df)} rows from {input_path}")
    return df

def check_zero_variance(series: pd.Series, name: str) -> bool:
    """
    Check if a series has zero variance (all values identical or single value).
    Returns True if zero variance is detected.
    """
    if len(series) < 2:
        logger.warning(f"Series '{name}' has fewer than 2 values, cannot compute variance.")
        return True
    
    unique_count = series.nunique()
    if unique_count <= 1:
        logger.warning(f"Series '{name}' has zero variance (only {unique_count} unique value(s)).")
        return True
    
    return False

def compute_spearman_correlation(df: pd.DataFrame, 
                                 var_x: str, 
                                 var_y: str) -> Tuple[Optional[float], Optional[float], int]:
    """
    Compute Spearman rank correlation between two variables.
    Returns (r_value, p_value, n_obs).
    If either variable has zero variance, returns (None, None, n_obs) and logs a warning.
    """
    n_obs = len(df)
    
    # Check for zero variance in either variable
    if check_zero_variance(df[var_x], var_x):
        log_warning(f"Skipping correlation: {var_x} has zero variance.")
        return None, None, n_obs
    
    if check_zero_variance(df[var_y], var_y):
        log_warning(f"Skipping correlation: {var_y} has zero variance.")
        return None, None, n_obs
    
    # Drop rows with missing values in either column for this calculation
    valid_data = df[[var_x, var_y]].dropna()
    n_valid = len(valid_data)
    
    if n_valid < 2:
        logger.warning(f"Not enough valid pairs ({n_valid}) to compute correlation.")
        return None, None, n_obs
    
    r_value, p_value = scipy.stats.spearmanr(valid_data[var_x], valid_data[var_y])
    log_provenance(f"Spearman correlation computed: r={r_value:.4f}, p={p_value:.4f}")
    
    return r_value, p_value, n_obs

def calculate_vif(df: pd.DataFrame, predictors: list) -> Dict[str, float]:
    """
    Calculate Variance Inflation Factor (VIF) for multicollinearity diagnostics.
    """
    from statsmodels.stats.outliers_influence import variance_inflation_factor
    
    X = df[predictors].dropna()
    if len(X) < len(predictors) + 1:
        logger.warning("Not enough samples to calculate VIF.")
        return {}
    
    # Add constant for intercept
    X_with_const = sm.add_constant(X)
    
    vif_data = {}
    for i, col in enumerate(X_with_const.columns):
        if col == 'const':
            continue
        vif = variance_inflation_factor(X_with_const.values, i)
        vif_data[col] = vif
    
    return vif_data

def save_vif_results(vif_results: Dict[str, float], output_path: str):
    """
    Save VIF results to a JSON file.
    """
    import json
    with open(output_path, 'w') as f:
        json.dump(vif_results, f, indent=2)
    logger.info(f"VIF results saved to {output_path}")

def run_analysis_pipeline():
    """
    Main pipeline for User Story 2: Correlation and Regression Analysis.
    """
    ensure_directories()
    
    # Load data
    df = load_processed_data()
    
    # Define variables
    shannon_col = 'shannon_index'
    fi_col = 'fluid_intelligence'
    
    # Check zero variance for Fluid Intelligence (T025 requirement)
    if check_zero_variance(df[fi_col], fi_col):
        log_warning(f"Zero variance detected in {fi_col}. Skipping correlation analysis.")
        # Still save empty results or handle as needed
        correlation_results = pd.DataFrame(columns=['r_value', 'p_value', 'n_obs'])
        correlation_results.to_csv(INPUT_PATHS['CORRELATION_RESULTS'], index=False)
        return
    
    # Compute Spearman correlation
    r_value, p_value, n_obs = compute_spearman_correlation(df, shannon_col, fi_col)
    
    # Save correlation results
    if r_value is not None:
        corr_df = pd.DataFrame({
            'r_value': [r_value],
            'p_value': [p_value],
            'n_obs': [n_obs]
        })
        corr_df.to_csv(INPUT_PATHS['CORRELATION_RESULTS'], index=False)
        logger.info(f"Correlation results saved to {INPUT_PATHS['CORRELATION_RESULTS']}")
    else:
        logger.warning("No correlation results to save due to zero variance.")
    
    # Multivariate regression (if data permits)
    predictors = [shannon_col, 'Age', 'Sex', 'BMI', 'DQS']
    available_predictors = [p for p in predictors if p in df.columns]
    
    if len(available_predictors) >= 1:
        # Prepare data for regression
        reg_data = df[[shannon_col, fi_col] + [p for p in available_predictors if p != shannon_col]].dropna()
        
        if len(reg_data) > 10:  # Minimum sample size for regression
            import statsmodels.api as sm
            X = sm.add_constant(reg_data[available_predictors])
            y = reg_data[fi_col]
            
            model = sm.OLS(y, X).fit()
            
            # Save regression results
            results_df = pd.DataFrame({
                'predictor': model.params.index,
                'coefficient': model.params.values,
                'std_err': model.bse.values,
                'p_value': model.pvalues.values
            })
            results_df.to_csv(INPUT_PATHS['REGRESSION_RESULTS'], index=False)
            logger.info(f"Regression results saved to {INPUT_PATHS['REGRESSION_RESULTS']}")
            
            # VIF diagnostics
            vif_results = calculate_vif(reg_data, available_predictors)
            save_vif_results(vif_results, INPUT_PATHS['VIF_RESULTS'])
        else:
            logger.warning("Insufficient data for regression analysis.")
    else:
        logger.warning("No predictors available for regression.")

def main():
    """Entry point for the analysis pipeline."""
    run_analysis_pipeline()

if __name__ == '__main__':
    main()