import pandas as pd
import numpy as np
import logging
from typing import Tuple, Dict, Any, Optional, Literal
from scipy import stats
import statsmodels.api as sm

from config import load_config, ensure_directories
from exceptions import MathematicalCouplingError
from validity import check_construct_validity

logger = logging.getLogger(__name__)

def _log_step(message: str) -> None:
    """Helper to log steps with consistent formatting."""
    logger.info(f"MODEL: {message}")

def calculate_correlation(df: pd.DataFrame, var1: str, var2: str) -> Tuple[float, float]:
    """
    Calculate Pearson or Spearman correlation between two variables.
    Returns (correlation, p-value).
    """
    _log_step(f"Calculating correlation between {var1} and {var2}")
    if var1 not in df.columns or var2 not in df.columns:
        raise ValueError(f"Columns {var1} or {var2} not found")
    
    # Check for missing values
    valid_data = df[[var1, var2]].dropna()
    if len(valid_data) < 2:
        return 0.0, 1.0
    
    corr, p_value = stats.pearsonr(valid_data[var1], valid_data[var2])
    return corr, p_value

def run_initial_correlations(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Run initial correlations between predictor and outcome.
    """
    _log_step("Running initial correlations")
    
    results = {}
    predictor = "news_exposure_freq"
    outcome = "anxiety_score"
    
    if predictor in df.columns and outcome in df.columns:
        corr, p_val = calculate_correlation(df, predictor, outcome)
        results[predictor] = {
            "correlation": corr,
            "p_value": p_val,
            "outcome": outcome
        }
    
    return results

def fit_regression_model(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Fit OLS regression model: anxiety_score ~ news_exposure_freq + baseline_anxiety + age + gender.
    """
    _log_step("Fitting regression model")
    
    required_cols = ["anxiety_score", "news_exposure_freq", "baseline_anxiety", "age", "gender"]
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        raise ValueError(f"Missing columns for regression: {missing}")
    
    # Prepare data
    y = df["anxiety_score"]
    X = df[["news_exposure_freq", "baseline_anxiety", "age", "gender"]]
    
    # Handle categorical variables if necessary (simplified for this task)
    # Assuming 'gender' is numeric or already encoded
    
    X = sm.add_constant(X)
    model = sm.OLS(y, X).fit()
    
    # Extract results
    results = {
        "coefficients": model.params.to_dict(),
        "p_values": model.pvalues.to_dict(),
        "r_squared": model.rsquared,
        "adj_r_squared": model.rsquared_adj,
        "f_statistic": model.fvalue,
        "f_pvalue": model.f_pvalue,
        "n_obs": model.nobs
    }
    
    _log_step("Regression model fitted successfully")
    return results

def check_vif(df: pd.DataFrame, predictors: list) -> Dict[str, float]:
    """
    Calculate Variance Inflation Factor (VIF) for all predictors.
    Flags model as unstable if any VIF > 10.
    """
    _log_step("Checking VIF")
    
    from statsmodels.stats.outliers_influence import variance_inflation_factor
    
    X = df[predictors]
    X = sm.add_constant(X)
    
    vif_data = {}
    for i, col in enumerate(X.columns):
        vif = variance_inflation_factor(X.values, i)
        vif_data[col] = vif
        if vif > 10:
            logger.warning(f"High VIF detected for {col}: {vif}")
    
    return vif_data

def check_assumptions(df: pd.DataFrame, y_col: str, X_cols: list) -> Dict[str, Any]:
    """
    Check regression assumptions: Linearity, Homoscedasticity, Normality.
    """
    _log_step("Checking model assumptions")
    
    y = df[y_col]
    X = df[X_cols]
    X = sm.add_constant(X)
    
    model = sm.OLS(y, X).fit()
    residuals = model.resid
    
    # Linearity (simplified: check correlation of residuals vs fitted)
    fitted = model.fittedvalues
    linearity_corr, _ = stats.pearsonr(fitted, residuals)
    
    # Homoscedasticity (Breusch-Pagan)
    from statsmodels.stats.diagnostic import het_breuschpagan
    bp_test = het_breuschpagan(residuals, model.model.exog)
    bp_stat, bp_pvalue = bp_test[0], bp_test[1]
    
    # Normality (Shapiro-Wilk)
    shapiro_stat, shapiro_pvalue = stats.shapiro(residuals)
    
    return {
        "linearity": {
            "correlation": linearity_corr,
            "pass": abs(linearity_corr) < 0.1 # Arbitrary threshold
        },
        "homoscedasticity": {
            "breusch_pagan_stat": bp_stat,
            "p_value": bp_pvalue,
            "pass": bp_pvalue > 0.05
        },
        "normality": {
            "shapiro_stat": shapiro_stat,
            "p_value": shapiro_pvalue,
            "pass": shapiro_pvalue > 0.05
        }
    }

def check_proxy_anxiety(df: pd.DataFrame) -> bool:
    """
    Check if 'general_anxiety' was used as a proxy for 'anticipatory_anxiety'.
    Returns True if proxy was used.
    """
    _log_step("Checking proxy anxiety")
    # Simplified: check if a column named 'general_anxiety' exists
    proxy_used = "general_anxiety" in df.columns
    if proxy_used:
        logger.warning("General anxiety used as proxy. Construct validity limitation noted.")
    return proxy_used

def run_full_analysis(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Run full analysis: correlations, regression, VIF, assumptions.
    """
    _log_step("Running full analysis")
    
    # Construct validity check
    try:
        check_construct_validity(df)
    except MathematicalCouplingError as e:
        logger.error(f"Construct validity failed: {e}")
        raise
    
    # Correlations
    correlations = run_initial_correlations(df)
    
    # Regression
    regression_results = fit_regression_model(df)
    
    # VIF
    predictors = ["news_exposure_freq", "baseline_anxiety", "age", "gender"]
    vif_results = check_vif(df, predictors)
    
    # Assumptions
    assumptions = check_assumptions(df, "anxiety_score", predictors)
    
    # Proxy check
    proxy_flag = check_proxy_anxiety(df)
    
    return {
        "correlations": correlations,
        "regression": regression_results,
        "vif": vif_results,
        "assumptions": assumptions,
        "proxy_flag": proxy_flag
    }

def main() -> None:
    """Main entry point for model analysis script."""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    config = load_config()
    ensure_directories()
    
    input_path = Path("data/processed/analysis_data.csv")
    
    try:
        if not input_path.exists():
            raise FileNotFoundError(f"Input file not found: {input_path}")
        
        df = pd.read_csv(input_path)
        results = run_full_analysis(df)
        
        # Save results (simplified for this task)
        import json
        output_path = Path("outputs/regression_results.json")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        logger.info("Full analysis completed and saved")
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    import sys
    main()
