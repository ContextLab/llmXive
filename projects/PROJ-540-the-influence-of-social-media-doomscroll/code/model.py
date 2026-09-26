"""
Statistical modeling module for the Doomscrolling Anxiety Analysis Pipeline.
Implements correlation, OLS regression, assumption checks, and VIF.
"""
import pandas as pd
import numpy as np
import logging
from typing import Tuple, Dict, Any, Optional, Literal
from scipy import stats
import statsmodels.api as sm
import statsmodels.formula.api as smf
from pathlib import Path
from config import load_config
from validity import check_construct_validity
from exceptions import MathematicalCouplingError

logger = logging.getLogger(__name__)

def calculate_correlation(df: pd.DataFrame, x: str, y: str) -> Dict[str, Any]:
    """Calculate Pearson and Spearman correlation between two variables."""
    # Remove NaN values
    valid_data = df[[x, y]].dropna()
    
    if len(valid_data) < 2:
        raise ValueError("Insufficient data for correlation calculation.")
    
    pearson_r, pearson_p = stats.pearsonr(valid_data[x], valid_data[y])
    spearman_r, spearman_p = stats.spearmanr(valid_data[x], valid_data[y])
    
    return {
        "pearson": {"r": float(pearson_r), "p_value": float(pearson_p)},
        "spearman": {"r": float(spearman_r), "p_value": float(spearman_p)},
        "n": len(valid_data)
    }

def run_initial_correlations(df: pd.DataFrame) -> Dict[str, Any]:
    """Run initial correlations between news exposure and anxiety."""
    logger.info("Running initial correlations...")
    
    results = {}
    
    # Correlation between news exposure and anxiety score
    if 'news_exposure_freq' in df.columns and 'anxiety_score' in df.columns:
        results['news_exposure_anxiety'] = calculate_correlation(
            df, 'news_exposure_freq', 'anxiety_score'
        )
    
    # Correlation between news exposure and baseline anxiety
    if 'news_exposure_freq' in df.columns and 'baseline_anxiety' in df.columns:
        results['news_exposure_baseline'] = calculate_correlation(
            df, 'news_exposure_freq', 'baseline_anxiety'
        )
    
    # Correlation between anxiety score and baseline anxiety
    if 'anxiety_score' in df.columns and 'baseline_anxiety' in df.columns:
        results['anxiety_baseline'] = calculate_correlation(
            df, 'anxiety_score', 'baseline_anxiety'
        )
    
    logger.info(f"Correlation results: {results}")
    return results

def fit_regression_model(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Fit OLS regression model: anxiety_score ~ news_exposure_freq + baseline_anxiety + age + gender
    Returns model summary and coefficients.
    """
    logger.info("Fitting OLS regression model...")
    
    # First, check construct validity
    validity_result = check_construct_validity(df)
    
    # Prepare formula
    if validity_result.get('baseline_anxiety_dropped'):
        logger.warning(f"Baseline anxiety dropped: {validity_result.get('reason')}")
        formula = "anxiety_score ~ news_exposure_freq + age + gender"
    else:
        formula = "anxiety_score ~ news_exposure_freq + baseline_anxiety + age + gender"
    
    # Convert gender to dummy variable if needed
    if 'gender' in df.columns:
        df['gender'] = df['gender'].astype(str)
    
    try:
        model = smf.ols(formula=formula, data=df).fit()
        
        results = {
            "formula": formula,
            "rsquared": float(model.rsquared),
            "rsquared_adj": float(model.rsquared_adj),
            "f_pvalue": float(model.f_pvalue),
            "coefficients": {},
            "p_values": {},
            "validity_checks": validity_result
        }
        
        for name, param in model.params.items():
          results["coefficients"][name] = float(param)
          results["p_values"][name] = float(model.pvalues[name])
        
        logger.info(f"Model fitted. R-squared: {model.rsquared:.4f}")
        return results
        
    except Exception as e:
        logger.error(f"Error fitting model: {e}")
        raise

def check_vif(df: pd.DataFrame, formula: str) -> Dict[str, float]:
    """Calculate Variance Inflation Factor for all predictors."""
    logger.info("Calculating VIF...")
    
    # Create design matrix
    y, X = dmatrices(formula, data=df, return_type='dataframe')
    
    vif_results = {}
    for i, col in enumerate(X.columns):
        if col == 'Intercept':
            continue
        vif = sm.OLS(X[col], X.drop(columns=[col])).fit().rsquared
        vif = 1 / (1 - vif) if vif < 1 else float('inf')
        vif_results[col] = vif
    
    # Check for multicollinearity
    high_vif = {k: v for k, v in vif_results.items() if v > 10}
    if high_vif:
        logger.warning(f"High VIF detected (>10): {high_vif}")
    
    return vif_results

def check_assumptions(df: pd.DataFrame, model) -> Dict[str, Any]:
    """
    Check regression assumptions:
    1. Linearity
    2. Homoscedasticity (Breusch-Pagan)
    3. Normality (Shapiro-Wilk)
    """
    logger.info("Checking model assumptions...")
    
    results = {
        "linearity": {},
        "homoscedasticity": {},
        "normality": {}
    }
    
    # 1. Linearity: Check residuals vs fitted
    residuals = model.resid
    fitted = model.fittedvalues
    
    # Simple linearity check: correlation between fitted and residuals should be ~0
    linearity_r, linearity_p = stats.pearsonr(fitted, residuals)
    results["linearity"] = {
        "correlation": float(linearity_r),
        "p_value": float(linearity_p),
        "passed": abs(linearity_r) < 0.1
    }
    
    # 2. Homoscedasticity: Breusch-Pagan test
    try:
        from statsmodels.stats.diagnostic import het_breuschpagan
        bp_test = het_breuschpagan(residuals, model.model.exog)
        bp_names = ['Lagrange multiplier statistic', 'p-value', 'f-value', 'f p-value']
        results["homoscedasticity"] = {
            "statistic": float(bp_test[0]),
            "p_value": float(bp_test[1]),
            "passed": bp_test[1] > 0.05  # Null hypothesis: homoscedasticity
        }
    except Exception as e:
        logger.warning(f"Breusch-Pagan test failed: {e}")
        results["homoscedasticity"] = {"passed": False, "error": str(e)}
    
    # 3. Normality: Shapiro-Wilk test
    try:
        shapiro_stat, shapiro_p = stats.shapiro(residuals[:5000])  # Limit for large N
        results["normality"] = {
            "statistic": float(shapiro_stat),
            "p_value": float(shapiro_p),
            "passed": shapiro_p > 0.05  # Null hypothesis: normal distribution
        }
    except Exception as e:
        logger.warning(f"Shapiro-Wilk test failed: {e}")
        results["normality"] = {"passed": False, "error": str(e)}
    
    return results

def check_proxy_anxiety(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Check if general_anxiety is used as a proxy for anticipatory_anxiety.
    Returns flag information for the report.
    """
    logger.info("Checking anxiety proxy usage...")
    
    flags = []
    
    # Check if 'anticipatory_anxiety' exists
    if 'anticipatory_anxiety' not in df.columns:
        if 'general_anxiety' in df.columns or 'anxiety_score' in df.columns:
            flags.append("Proxy Used: General Anxiety")
            logger.warning("Using general anxiety as proxy for anticipatory anxiety.")
    
    return {
        "proxy_used": len(flags) > 0,
        "flags": flags
    }

def run_full_analysis(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Run full statistical analysis pipeline.
    Returns comprehensive results dictionary.
    """
    logger.info("Running full statistical analysis...")
    
    # 1. Correlations
    correlations = run_initial_correlations(df)
    
    # 2. Regression model
    regression_results = fit_regression_model(df)
    
    # 3. VIF
    formula = regression_results.get("formula", "")
    if formula:
        vif_results = check_vif(df, formula)
        regression_results["vif"] = vif_results
    
    # 4. Assumption checks
    # Re-fit model to get model object for diagnostics
    try:
        model = smf.ols(formula, data=df).fit()
        assumptions = check_assumptions(df, model)
        regression_results["assumptions"] = assumptions
    except Exception as e:
        logger.warning(f"Assumption checks failed: {e}")
        regression_results["assumptions"] = {"error": str(e)}
    
    # 5. Proxy check
    proxy_info = check_proxy_anxiety(df)
    regression_results["flags"] = proxy_info.get("flags", [])
    
    # 6. Save correlation results
    corr_output_path = Path("outputs/correlation_results.json")
    with open(corr_output_path, 'w') as f:
        import json
        json.dump(correlations, f, indent=2)
    
    # 7. Save regression results
    reg_output_path = Path("outputs/regression_results.json")
    with open(reg_output_path, 'w') as f:
        import json
        json.dump(regression_results, f, indent=2)
    
    return {
        "correlations": correlations,
        "regression": regression_results
    }

def main():
    """CLI entry point for modeling."""
    try:
        input_path = Path("data/processed/analysis_data.csv")
        if not input_path.exists():
            logger.error("No input data found for modeling.")
            return 1
        
        df = pd.read_csv(input_path)
        results = run_full_analysis(df)
        
        logger.info("Analysis complete.")
        return 0
    except Exception as e:
        logger.error(f"Error during analysis: {e}")
        return 1

if __name__ == "__main__":
    import sys
    sys.exit(main())
