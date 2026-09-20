import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
import pandas as pd
import numpy as np
import statsmodels.api as sm
from statsmodels.stats.diagnostic import het_breuschpagan
from statsmodels.stats.stattools import durbin_watson
from scipy import stats
from utils.logger import get_logger, log_execution_start, log_execution_end
from data.config import get_config

logger = get_logger(__name__)

def check_normality(residuals: np.ndarray) -> Dict[str, Any]:
    """
    Perform Shapiro-Wilk test for normality of residuals.
    
    Args:
        residuals: Array of model residuals.
        
    Returns:
        Dictionary with 'shapiro_stat', 'shapiro_p', and 'is_normal' boolean.
    """
    if len(residuals) < 3:
        logger.warning("Not enough residuals for Shapiro-Wilk test.")
        return {
            "shapiro_stat": None,
            "shapiro_p": None,
            "is_normal": False,
            "message": "Insufficient data for normality test."
        }
    
    try:
        stat, p_value = stats.shapiro(residuals)
        is_normal = p_value > 0.05
        return {
            "shapiro_stat": float(stat),
            "shapiro_p": float(p_value),
            "is_normal": bool(is_normal)
        }
    except Exception as e:
        logger.error(f"Shapiro-Wilk test failed: {e}")
        return {
            "shapiro_stat": None,
            "shapiro_p": None,
            "is_normal": False,
            "message": str(e)
        }

def check_homoscedasticity(residuals: np.ndarray, predicted: np.ndarray) -> Dict[str, Any]:
    """
    Perform Breusch-Pagan test for homoscedasticity.
    
    Args:
        residuals: Array of model residuals.
        predicted: Array of predicted values.
        
    Returns:
        Dictionary with 'bp_stat', 'bp_p', and 'is_homoscedastic' boolean.
    """
    if len(residuals) < 10:
        logger.warning("Not enough data for Breusch-Pagan test.")
        return {
            "bp_stat": None,
            "bp_p": None,
            "is_homoscedastic": False,
            "message": "Insufficient data for homoscedasticity test."
        }
    
    try:
        # het_breuschpagan expects residuals and exog (predicted values or design matrix)
        # We use predicted values as the exog for the auxiliary regression
        bp_test = het_breuschpagan(residuals, predicted.reshape(-1, 1))
        # bp_test returns: (lm, lm_pvalue, f, f_pvalue)
        # We use the LM statistic and p-value
        lm_stat, lm_pvalue = bp_test[0], bp_test[1]
        is_homoscedastic = lm_pvalue > 0.05
        
        return {
            "bp_stat": float(lm_stat),
            "bp_p": float(lm_pvalue),
            "is_homoscedastic": bool(is_homoscedastic)
        }
    except Exception as e:
        logger.error(f"Breusch-Pagan test failed: {e}")
        return {
            "bp_stat": None,
            "bp_p": None,
            "is_homoscedastic": False,
            "message": str(e)
        }

def check_collinearity(df: pd.DataFrame, predictors: List[str]) -> Dict[str, Any]:
    """
    Calculate Variance Inflation Factors (VIF) for predictors.
    
    Args:
        df: DataFrame containing predictor variables.
        predictors: List of column names to check for collinearity.
        
    Returns:
        Dictionary with 'vif_values' (dict of var: vif), 'vif_max', and 'has_collinearity' boolean.
    """
    if not predictors:
        return {
            "vif_values": {},
            "vif_max": None,
            "has_collinearity": False,
            "message": "No predictors provided for VIF calculation."
        }
    
    try:
        # Filter dataframe to only include predictors
        X = df[predictors].dropna()
        if X.empty or len(X) < len(predictors) + 1:
            logger.warning("Not enough data points for VIF calculation.")
            return {
                "vif_values": {},
                "vif_max": None,
                "has_collinearity": False,
                "message": "Insufficient data for VIF calculation."
            }
        
        # Add constant for intercept
        X_with_const = sm.add_constant(X)
        
        vif_values = {}
        for col in X.columns:
            try:
                # VIF for a variable is 1 / (1 - R^2) where R^2 is from regressing 
                # that variable on all other independent variables
                y_var = X[col]
                X_other = X_with_const.drop(columns=[col])
                if X_other.shape[1] == 0:
                    vif_values[col] = 1.0
                    continue
                
                model = sm.OLS(y_var, X_other).fit()
                r_squared = model.rsquared
                if r_squared == 1.0:
                    vif = float('inf')
                else:
                    vif = 1.0 / (1.0 - r_squared)
                vif_values[col] = float(vif)
            except Exception as e:
                logger.warning(f"Could not calculate VIF for {col}: {e}")
                vif_values[col] = float('inf')
        
        vif_max = max(vif_values.values()) if vif_values else 0.0
        has_collinearity = vif_max >= 5.0
        
        return {
            "vif_values": vif_values,
            "vif_max": float(vif_max),
            "has_collinearity": bool(has_collinearity)
        }
    except Exception as e:
        logger.error(f"Collinearity check failed: {e}")
        return {
            "vif_values": {},
            "vif_max": None,
            "has_collinearity": False,
            "message": str(e)
        }

def validate_model_assumptions(model_results: Any, df: pd.DataFrame, 
                               outcome_col: str, predictor_cols: List[str]) -> Dict[str, Any]:
    """
    Validate all model assumptions: Normality, Homoscedasticity, Collinearity.
    
    Args:
        model_results: Fitted statsmodels OLS results object.
        df: Original DataFrame with data.
        outcome_col: Name of the outcome variable.
        predictor_cols: List of predictor variable names used in the model.
        
    Returns:
        Dictionary containing all assumption test results.
    """
    logger.info("Validating model assumptions...")
    
    # Get residuals and predicted values
    residuals = model_results.resid
    predicted = model_results.fittedvalues
    
    # Check Normality (Shapiro-Wilk)
    normality_results = check_normality(residuals)
    
    # Check Homoscedasticity (Breusch-Pagan)
    homoscedasticity_results = check_homoscedasticity(residuals, predicted)
    
    # Check Collinearity (VIF)
    collinearity_results = check_collinearity(df, predictor_cols)
    
    # Compile results
    assumptions = {
        "shapiro_p": normality_results.get("shapiro_p"),
        "breusch_pagan_p": homoscedasticity_results.get("bp_p"),
        "vif_max": collinearity_results.get("vif_max"),
        "details": {
            "normality": normality_results,
            "homoscedasticity": homoscedasticity_results,
            "collinearity": collinearity_results
        }
    }
    
    # Log summary
    logger.info(f"Assumption Validation Summary:")
    logger.info(f"  - Normality (Shapiro-Wilk p={normality_results.get('shapiro_p', 'N/A')})")
    logger.info(f"  - Homoscedasticity (BP p={homoscedasticity_results.get('bp_p', 'N/A')})")
    logger.info(f"  - Collinearity (Max VIF={collinearity_results.get('vif_max', 'N/A')})")
    
    if not normality_results.get("is_normal", False):
        logger.warning("Normality assumption violated (p <= 0.05). Consider robust standard errors.")
    if not homoscedasticity_results.get("is_homoscedastic", False):
        logger.warning("Homoscedasticity assumption violated (p <= 0.05). Consider robust standard errors.")
    if collinearity_results.get("has_collinearity", False):
        logger.warning("Collinearity detected (VIF >= 5). Results should be interpreted descriptively.")
        
    return assumptions

def fit_ancova_model(df: pd.DataFrame, outcome: str, covariate: str, 
                     treatment: str, moderator: str, interaction: bool = True) -> Tuple[Any, Dict[str, Any]]:
    """
    Fit ANCOVA model: outcome ~ covariate + treatment + moderator + treatment*moderator
    
    Args:
        df: DataFrame with data.
        outcome: Name of outcome variable (post_self_esteem).
        covariate: Name of covariate (pre_self_esteem).
        treatment: Name of treatment variable (avatar_condition).
        moderator: Name of moderator variable (comparison_tendency).
        interaction: Whether to include interaction term.
        
    Returns:
        Tuple of (fitted model results, model summary info).
    """
    logger.info(f"Fitting ANCOVA model: {outcome} ~ {covariate} + {treatment} + {moderator}")
    
    # Prepare formula
    if interaction:
        formula = f"{outcome} ~ {covariate} + {treatment} * {moderator}"
    else:
        formula = f"{outcome} ~ {covariate} + {treatment} + {moderator}"
    
    # Drop rows with missing values in relevant columns
    cols_needed = [outcome, covariate, treatment, moderator]
    clean_df = df[cols_needed].dropna()
    
    if len(clean_df) < 10:
        raise ValueError(f"Insufficient data for ANCOVA model. Need at least 10 rows, got {len(clean_df)}.")
    
    # Fit model
    model = sm.OLS.from_formula(formula, data=clean_df)
    results = model.fit()
    
    # Prepare summary info
    summary_info = {
        "formula": formula,
        "n_obs": len(clean_df),
        "r_squared": float(results.rsquared),
        "adj_r_squared": float(results.rsquared_adj),
        "f_statistic": float(results.fvalue),
        "f_pvalue": float(results.f_pvalue)
    }
    
    logger.info(f"Model fitted: R²={summary_info['r_squared']:.4f}, Adj R²={summary_info['adj_r_squared']:.4f}")
    
    return results, summary_info

def get_coefficients(results: Any) -> List[Dict[str, Any]]:
    """
    Extract coefficients from fitted model results.
    
    Args:
        results: Fitted statsmodels OLS results object.
        
    Returns:
        List of dictionaries with coefficient details.
    """
    coeffs = []
    for name, row in results.params.to_frame().iterrows():
        coef_info = {
            "name": name,
            "estimate": float(row[0]),
            "std_err": float(results.bse[name]),
            "t_stat": float(results.tvalues[name]),
            "p_value": float(results.pvalues[name]),
            "conf_int_low": float(results.conf_int().loc[name, 0]),
            "conf_int_high": float(results.conf_int().loc[name, 1])
        }
        coeffs.append(coef_info)
    return coeffs

def run_regression_analysis(df: pd.DataFrame, config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Run complete regression analysis including model fitting and assumption validation.
    
    Args:
        df: DataFrame with processed data.
        config: Optional configuration dictionary.
        
    Returns:
        Dictionary with model results and assumption validation.
    """
    log_execution_start(logger, "run_regression_analysis")
    
    if config is None:
        config = get_config()
    
    # Define column names based on spec
    outcome = "post_self_esteem"
    covariate = "pre_self_esteem"
    treatment = "avatar_condition"
    moderator = "comparison_tendency"
    
    # Check if required columns exist
    required_cols = [outcome, covariate, treatment, moderator]
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in data: {missing_cols}")
    
    # Fit model
    model_results, model_summary = fit_ancova_model(
        df, outcome, covariate, treatment, moderator, interaction=True
    )
    
    # Extract coefficients
    coefficients = get_coefficients(model_results)
    
    # Validate assumptions
    assumptions = validate_model_assumptions(
        model_results, df, outcome, [covariate, treatment, moderator]
    )
    
    # Compile final results
    results = {
        "model_summary": model_summary,
        "coefficients": coefficients,
        "assumptions": assumptions,
        "data_source_type": config.get("data_source_type", "unknown")
    }
    
    log_execution_end(logger, "run_regression_analysis")
    return results

def main():
    """Main entry point for regression analysis."""
    log_execution_start(logger, "main")
    
    try:
        config = get_config()
        data_path = Path(config.get("data_processed_path", "data/processed/imputed_data.csv"))
        
        if not data_path.exists():
            raise FileNotFoundError(f"Data file not found: {data_path}")
        
        df = pd.read_csv(data_path)
        
        logger.info(f"Loaded data from {data_path} with {len(df)} rows")
        
        results = run_regression_analysis(df, config)
        
        # Log key findings
        logger.info(f"Regression analysis complete. Found {len(results['coefficients'])} coefficients.")
        logger.info(f"Assumption validation: VIF max = {results['assumptions']['vif_max']}")
        
        return results
        
    except Exception as e:
        logger.error(f"Regression analysis failed: {e}")
        raise
    finally:
        log_execution_end(logger, "main")

if __name__ == "__main__":
    main()