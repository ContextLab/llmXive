"""
Statistical modeling module for the Doomscrolling Anxiety study.
Handles correlation, regression, and assumption checks.
"""
import pandas as pd
import numpy as np
import logging
from typing import Tuple, Dict, Any, Optional, Literal
from scipy import stats
import statsmodels.api as sm
import statsmodels.formula.api as smf
import matplotlib.pyplot as plt
import seaborn as sns

from validity import check_construct_validity
from exceptions import MathematicalCouplingError

logger = logging.getLogger(__name__)

REGRESSION_FORMULA = "anxiety_score ~ news_exposure_freq + baseline_anxiety + age + gender"

def calculate_correlation(df: pd.DataFrame, col1: str, col2: str) -> Dict[str, float]:
    """
    Calculates Pearson and Spearman correlation between two columns.

    Args:
        df: DataFrame.
        col1: First column.
        col2: Second column.

    Returns:
        Dict with correlation coefficients and p-values.
    """
    valid = df[[col1, col2]].dropna()
    if len(valid) < 2:
        return {'pearson_r': np.nan, 'pearson_p': np.nan, 'spearman_r': np.nan, 'spearman_p': np.nan}

    pearson_r, pearson_p = stats.pearsonr(valid[col1], valid[col2])
    spearman_r, spearman_p = stats.spearmanr(valid[col1], valid[col2])

    return {
        'pearson_r': float(pearson_r),
        'pearson_p': float(pearson_p),
        'spearman_r': float(spearman_r),
        'spearman_p': float(spearman_p)
    }

def run_initial_correlations(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Runs correlations for all relevant pairs.

    Args:
        df: Cleaned DataFrame.

    Returns:
        Dict of correlation results.
    """
    results = {}
    pairs = [
        ('news_exposure_freq', 'anxiety_score'),
        ('news_exposure_freq', 'baseline_anxiety'),
        ('baseline_anxiety', 'anxiety_score'),
        ('age', 'anxiety_score'),
        ('age', 'news_exposure_freq')
    ]
    
    for c1, c2 in pairs:
        key = f"{c1}_vs_{c2}"
        results[key] = calculate_correlation(df, c1, c2)
        logger.info(f"Correlation {key}: Pearson r={results[key]['pearson_r']:.4f}, p={results[key]['pearson_p']:.4f}")
    
    return results

def fit_regression_model(df: pd.DataFrame, formula: str = REGRESSION_FORMULA) -> Dict[str, Any]:
    """
    Fits an OLS regression model.

    Args:
        df: Cleaned DataFrame.
        formula: Statsmodels formula string.

    Returns:
        Dict containing model summary stats and coefficients.
    """
    logger.info(f"Fitting regression model: {formula}")
    
    # Ensure gender is treated as categorical if it's string
    if 'gender' in df.columns and df['gender'].dtype == object:
        # Statsmodels handles categorical variables with C() in formula
        pass
    
    model = smf.ols(formula, data=df).fit()
    
    # Extract coefficients
    coefficients = {}
    for param, value in model.params.items():
        coefficients[param] = float(value)
    
    # Extract stats
    results = {
        'formula': formula,
        'coefficients': coefficients,
        'rsquared': float(model.rsquared),
        'rsquared_adj': float(model.rsquared_adj),
        'aic': float(model.aic),
        'bic': float(model.bic),
        'nobs': int(model.nobs),
        'f_statistic': float(model.fvalue),
        'f_pvalue': float(model.f_pvalue),
        'summary': model.summary().as_text()
    }
    
    logger.info(f"Model fitted. R-squared: {results['rsquared']:.4f}, F-stat: {results['f_statistic']:.4f}")
    return results

def check_vif(df: pd.DataFrame, predictors: list) -> Dict[str, float]:
    """
    Calculates Variance Inflation Factor (VIF) for predictors.

    Args:
        df: DataFrame.
        predictors: List of predictor column names.

    Returns:
        Dict of VIF values.
    """
    from statsmodels.stats.outliers_influence import variance_inflation_factor
    
    # Add intercept for VIF calculation if needed, though VIF usually calculated on X
    X = df[predictors].dropna()
    # Add constant for intercept
    X_const = sm.add_constant(X)
    
    vif_data = {}
    for i, col in enumerate(X_const.columns):
        if col == 'const':
            continue
        vif = variance_inflation_factor(X_const.values, i)
        vif_data[col] = float(vif)
    
    return vif_data

def check_assumptions(df: pd.DataFrame, model_results: Dict[str, Any]) -> Dict[str, Any]:
    """
    Checks regression assumptions: Linearity, Homoscedasticity, Normality, VIF.

    Args:
        df: Cleaned DataFrame.
        model_results: Results from fit_regression_model.

    Returns:
        Dict of assumption check results.
    """
    assumptions = {}
    
    # 1. VIF Check
    predictors = ['news_exposure_freq', 'baseline_anxiety', 'age']
    # Handle gender if it's numeric, else skip or encode
    if 'gender' in df.columns and pd.api.types.is_numeric_dtype(df['gender']):
        predictors.append('gender')
    
    vif_results = check_vif(df, predictors)
    assumptions['vif'] = vif_results
    
    max_vif = max(vif_results.values()) if vif_results else 0
    if max_vif > 10:
        error_msg = f"High VIF detected: {max_vif}. Mathematical coupling or multicollinearity suspected."
        logger.error(error_msg)
        raise MathematicalCouplingError(error_msg)
    logger.info(f"VIF check passed. Max VIF: {max_vif:.2f}")

    # 2. Residual Analysis (Linearity, Homoscedasticity, Normality)
    # We need to reconstruct the model object or use the results to get residuals
    # Since we have summary stats but not the object, we refit briefly for residuals
    formula = model_results['formula']
    model = smf.ols(formula, data=df).fit()
    residuals = model.resid
    fitted = model.fittedvalues

    # Homoscedasticity: Breusch-Pagan Test
    from statsmodels.stats.diagnostic import het_breuschpagan
    bp_test = het_breuschpagan(residuals, model.model.exog)
    # bp_test: (lm, lm_pvalue, f, f_pvalue)
    assumptions['homoscedasticity'] = {
        'breusch_pagan_stat': float(bp_test[0]),
        'breusch_pagan_pvalue': float(bp_test[1]),
        'status': 'PASS' if bp_test[1] > 0.05 else 'FAIL'
    }
    logger.info(f"Homoscedasticity (Breusch-Pagan): p={bp_test[1]:.4f}")

    # Normality: Shapiro-Wilk Test
    shapiro_stat, shapiro_p = stats.shapiro(residuals)
    assumptions['normality'] = {
        'shapiro_statistic': float(shapiro_stat),
        'shapiro_pvalue': float(shapiro_p),
        'status': 'PASS' if shapiro_p > 0.05 else 'FAIL'
    }
    logger.info(f"Normality (Shapiro-Wilk): p={shapiro_p:.4f}")

    # Linearity: Check correlation between residuals and fitted values (should be ~0)
    linearity_corr, linearity_p = stats.pearsonr(residuals, fitted)
    assumptions['linearity'] = {
        'residuals_vs_fitted_corr': float(linearity_corr),
        'status': 'PASS' if abs(linearity_corr) < 0.1 else 'WARN'
    }
    
    return assumptions

def check_proxy_anxiety(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Checks if 'anxiety_score' is a proxy for 'general_anxiety'.
    Flags if the dataset lacks 'anticipatory_anxiety'.
    """
    results = {
        'is_proxy': False,
        'proxy_type': None,
        'limitation_note': None
    }
    
    cols = df.columns.tolist()
    if 'anticipatory_anxiety' not in cols and 'general_anxiety' in cols:
        results['is_proxy'] = True
        results['proxy_type'] = 'general_anxiety'
        results['limitation_note'] = "Analysis uses general_anxiety as a proxy for anticipatory_anxiety. Construct validity limitation applies."
        logger.warning(results['limitation_note'])
    elif 'anticipatory_anxiety' in cols:
        results['is_proxy'] = False
        results['limitation_note'] = "Direct measure of anticipatory_anxiety used."
    
    return results

def run_full_analysis(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Orchestrates the full statistical analysis: Validity, Correlation, Regression, Assumptions.

    Args:
        df: Cleaned DataFrame.

    Returns:
        Dict containing all analysis results.
    """
    # 1. Construct Validity
    check_construct_validity(df)
    
    # 2. Correlations
    correlations = run_initial_correlations(df)
    
    # 3. Regression
    regression_results = fit_regression_model(df)
    
    # 4. Assumptions
    assumptions = check_assumptions(df, regression_results)
    
    # 5. Proxy Check
    proxy_info = check_proxy_anxiety(df)
    
    return {
        'correlations': correlations,
        'regression': regression_results,
        'assumptions': assumptions,
        'proxy_info': proxy_info
    }

def main():
    """
    Main entry point for model analysis.
    """
    from config import load_config, ensure_directories
    from pathlib import Path
    import json
    
    config = load_config()
    ensure_directories()
    
    input_path = Path(config['paths']['processed_data']) / 'analysis_data.csv'
    output_reg = Path(config['paths']['outputs']) / 'regression_results.json'
    output_corr = Path(config['paths']['outputs']) / 'correlation_results.json'
    
    if not input_path.exists():
        raise FileNotFoundError(f"Processed data not found: {input_path}. Run clean.py first.")
    
    df = pd.read_csv(input_path)
    results = run_full_analysis(df)
    
    # Save Regression
    with open(output_reg, 'w') as f:
        json.dump(results['regression'], f, indent=2, default=str)
    logger.info(f"Regression results saved to {output_reg}")
    
    # Save Correlation
    with open(output_corr, 'w') as f:
        json.dump(results['correlations'], f, indent=2)
    logger.info(f"Correlation results saved to {output_corr}")

if __name__ == '__main__':
    main()
