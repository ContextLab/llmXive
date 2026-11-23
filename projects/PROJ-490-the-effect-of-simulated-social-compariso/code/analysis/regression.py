"""
Regression Analysis Module.
Implements ANCOVA model fitting and assumption validation.
"""
import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
import pandas as pd
import numpy as np
import statsmodels.api as sm
import statsmodels.formula.api as smf
from scipy import stats
from utils.logger import get_logger
from data.config import get_config

logger = get_logger("regression")

def check_normality(residuals: np.ndarray) -> float:
    """
    Perform Shapiro-Wilk test for normality on residuals.

    Args:
        residuals: Array of model residuals

    Returns:
        p-value from the Shapiro-Wilk test
    """
    if len(residuals) < 3:
        logger.warning("Too few residuals for Shapiro-Wilk test.")
        return 1.0
    stat, p_value = stats.shapiro(residuals)
    logger.info(f"Shapiro-Wilk normality test: W={stat:.4f}, p={p_value:.4f}")
    return p_value

def check_homoscedasticity(y: np.ndarray, residuals: np.ndarray) -> float:
    """
    Perform Breusch-Pagan test for homoscedasticity.

    Args:
        y: Observed values
        residuals: Model residuals

    Returns:
        p-value from the Breusch-Pagan test
    """
    if len(residuals) < 3:
        logger.warning("Too few residuals for Breusch-Pagan test.")
        return 1.0
    try:
        # Using a simplified version of Breusch-Pagan
        # Regress squared residuals against fitted values
        X = np.column_stack([np.ones(len(residuals)), y])
        model = sm.OLS(residuals**2, X).fit()
        n = len(residuals)
        # LM = n * R^2
        # We approximate R^2 from the auxiliary regression
        # Since we are regressing residuals^2 on y (and intercept)
        # We can compute R^2 directly
        ss_res = model.ssr
        ss_tot = np.sum((residuals**2 - np.mean(residuals**2))**2)
        r_squared = 1 - (ss_res / ss_tot) if ss_tot != 0 else 0
        lm_stat = n * r_squared
        # The statistic follows a Chi-square distribution with k-1 degrees of freedom
        # k is the number of regressors in the auxiliary model (2 here: intercept + y)
        # So df = 1
        p_value = 1 - stats.chi2.cdf(lm_stat, 1)
        logger.info(f"Breusch-Pagan test: LM={lm_stat:.4f}, p={p_value:.4f}")
        return p_value
    except Exception as e:
        logger.warning(f"Breusch-Pagan test failed: {e}")
        return 1.0

def check_collinearity(df: pd.DataFrame, predictors: List[str]) -> float:
    """
    Calculate maximum Variation Inflation Factor (VIF) for predictors.

    Args:
        df: DataFrame containing the variables
        predictors: List of column names to check

    Returns:
        Maximum VIF value
    """
    if len(predicters) < 2:
        return 0.0

    try:
        # Add intercept for VIF calculation
        X = df[predictors].values
        X_with_intercept = sm.add_constant(X)
        # Calculate VIF for each predictor
        vifs = []
        for i in range(1, X_with_intercept.shape[1]):
            # Regress variable i against all others
            y_i = X_with_intercept[:, i]
            X_others = np.delete(X_with_intercept, i, axis=1)
            model = sm.OLS(y_i, X_others).fit()
            r_squared = model.rsquared
            vif = 1.0 / (1.0 - r_squared) if r_squared < 1.0 else float('inf')
            vifs.append(vif)

        max_vif = max(vifs)
        logger.info(f"VIF check: Max VIF = {max_vif:.4f}")
        return max_vif
    except Exception as e:
        logger.warning(f"VIF calculation failed: {e}")
        return float('inf')

def validate_model_assumptions(model: smf.OLS, df: pd.DataFrame) -> Dict[str, Any]:
    """
    Validate all model assumptions: Normality, Homoscedasticity, Collinearity.

    Args:
        model: Fitted OLS model
        df: DataFrame used for fitting

    Returns:
        Dictionary of assumption test results
    """
    residuals = model.resid
    fitted = model.fittedvalues

    shapiro_p = check_normality(residuals)
    bp_p = check_homoscedasticity(fitted.values, residuals) # Use fitted values as 'y' for BP approx

    # For VIF, we need the predictor columns used in the formula
    # Extract predictors from formula (simplified)
    # Formula is usually like "post ~ pre + avatar + incom + avatar:incom"
    # We'll assume we know the columns: pre_self_esteem, avatar_condition, comparison_tendency
    predictors = ['pre_self_esteem', 'avatar_condition', 'comparison_tendency', 'avatar_condition:comparison_tendency']
    # Filter to columns that actually exist in df
    available_predictors = [p for p in predictors if p in df.columns]
    # If interaction term is not a separate column, we need to construct it or use the formula terms
    # For VIF calculation, we usually use the main effects if the interaction is present
    # But strict VIF checks all columns in the design matrix.
    # Let's use the columns available in df that are numeric and part of the model.
    # We'll simplify: check VIF on the main numeric columns used.
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    relevant_cols = [c for c in numeric_cols if c in ['pre_self_esteem', 'avatar_condition', 'comparison_tendency']]

    vif_max = check_collinearity(df, relevant_cols)

    return {
        'shapiro_p': float(shapiro_p),
        'breusch_pagan_p': float(bp_p),
        'vif_max': float(vif_max)
    }

def fit_ancova_model(df: pd.DataFrame) -> smf.OLS:
    """
    Fit the ANCOVA model.
    Outcome: post_self_esteem
    Covariate: pre_self_esteem
    Predictors: avatar_condition, comparison_tendency, and their interaction.

    Args:
        df: DataFrame with the data

    Returns:
        Fitted OLS model
    """
    logger.info("Fitting ANCOVA model...")
    logger.info(f"Data shape: {df.shape}")
    logger.info(f"Columns: {df.columns.tolist()}")

    # Ensure required columns exist
    required = ['post_self_esteem', 'pre_self_esteem', 'avatar_condition', 'comparison_tendency']
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns for ANCOVA: {missing}")

    # Construct the formula
    # ANCOVA: post ~ pre + avatar + incom + avatar:incom
    # We use the interaction term explicitly
    formula = "post_self_esteem ~ pre_self_esteem + avatar_condition + comparison_tendency + avatar_condition:comparison_tendency"

    try:
        model = smf.OLS.from_formula(formula, data=df)
        results = model.fit()
        logger.info(f"Model fitted. R-squared: {results.rsquared:.4f}")
        return results
    except Exception as e:
        logger.error(f"Failed to fit ANCOVA model: {e}")
        raise

def get_coefficients(model_results: smf.OLS) -> List[Dict[str, Any]]:
    """
    Extract regression coefficients from the fitted model.

    Args:
        model_results: Fitted OLS model results

    Returns:
        List of dictionaries with coefficient details
    """
    coeffs = model_results.params
    std_err = model_results.std_err
    p_values = model_results.pvalues

    result_list = []
    for name in coeffs.index:
        result_list.append({
            'name': name,
            'estimate': float(coeffs[name]),
            'std_err': float(std_err[name]),
            'p_value': float(p_values[name])
        })
    return result_list

def run_regression_analysis(df: pd.DataFrame) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Run the full regression analysis pipeline.
    1. Fit ANCOVA model
    2. Validate assumptions
    3. Extract coefficients

    Args:
        df: Processed DataFrame

    Returns:
        Tuple of (coefficients_list, diagnostics_dict)
    """
    logger.info("Running regression analysis pipeline.")

    # 1. Fit Model
    model = fit_ancova_model(df)

    # 2. Validate Assumptions
    diagnostics = validate_model_assumptions(model, df)
    diagnostics['data_source_type'] = 'synthetic' # Default, updated later if needed
    if 'data_source_type' not in diagnostics:
        # Check if we can infer from data or config
        # For now, we rely on the config or a flag passed in
        # But T021 just exports what we have.
        pass

    # 3. Extract Coefficients
    coefficients = get_coefficients(model)

    logger.info("Regression analysis complete.")
    return coefficients, diagnostics

if __name__ == "__main__":
    config = get_config()
    imputed_path = Path(config['paths']['processed']) / "imputed_data.csv"
    if imputed_path.exists():
        df = pd.read_csv(imputed_path)
        coeffs, diags = run_regression_analysis(df)
        print(f"Coefficients: {coeffs}")
        print(f"Diagnostics: {diags}")
    else:
        logger.error(f"Imputed data not found at {imputed_path}")
