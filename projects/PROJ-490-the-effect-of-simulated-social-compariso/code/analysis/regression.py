import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List

import pandas as pd
import numpy as np
import statsmodels.api as sm
import statsmodels.formula.api as smf
from scipy import stats

from utils.logger import get_logger, log_execution_start, log_execution_end
from utils.validators import validate_dataframe_schema, load_schema

logger = get_logger(__name__)

def check_normality(residuals: pd.Series) -> Dict[str, Any]:
    """
    Perform Shapiro-Wilk test for normality of residuals.
    
    Args:
        residuals: Series of residuals from the fitted model.
        
    Returns:
        Dictionary containing test statistic, p-value, and pass/fail status.
        Passes if p-value > 0.05 (fail to reject null hypothesis of normality).
    """
    if len(residuals) < 3:
        logger.warning("Shapiro-Wilk test requires at least 3 observations.")
        return {
            "test": "Shapiro-Wilk",
            "statistic": np.nan,
            "p_value": np.nan,
            "passed": False,
            "message": "Insufficient data for normality test"
        }
    
    try:
        stat, p_value = stats.shapiro(residuals.dropna())
        passed = p_value > 0.05
        logger.info(f"Shapiro-Wilk: statistic={stat:.4f}, p-value={p_value:.4f}, passed={passed}")
        return {
            "test": "Shapiro-Wilk",
            "statistic": float(stat),
            "p_value": float(p_value),
            "passed": bool(passed),
            "message": "Normality assumption met" if passed else "Normality assumption violated"
        }
    except Exception as e:
        logger.error(f"Shapiro-Wilk test failed: {e}")
        return {
            "test": "Shapiro-Wilk",
            "statistic": np.nan,
            "p_value": np.nan,
            "passed": False,
            "message": f"Test failed: {str(e)}"
        }

def check_homoscedasticity(model: sm.OLSResults, residuals: pd.Series, 
                           predicted: pd.Series) -> Dict[str, Any]:
    """
    Perform Breusch-Pagan test for homoscedasticity.
    
    Args:
        model: Fitted OLS model results.
        residuals: Series of residuals.
        predicted: Series of predicted values.
        
    Returns:
        Dictionary containing test statistic, p-value, and pass/fail status.
        Passes if p-value > 0.05 (fail to reject null hypothesis of constant variance).
    """
    try:
        # Breusch-Pagan test using statsmodels
        # Null hypothesis: homoscedasticity (constant variance)
        bp_test = sm.stats.diagnostic.het_breuschpagan(residuals, model.model.exog)
        
        # bp_test returns: (lm statistic, lm p-value, f-statistic, f p-value)
        lm_stat = bp_test[0]
        lm_pvalue = bp_test[1]
        
        passed = lm_pvalue > 0.05
        logger.info(f"Breusch-Pagan: LM-statistic={lm_stat:.4f}, p-value={lm_pvalue:.4f}, passed={passed}")
        
        return {
            "test": "Breusch-Pagan",
            "statistic": float(lm_stat),
            "p_value": float(lm_pvalue),
            "passed": bool(passed),
            "message": "Homoscedasticity assumption met" if passed else "Homoscedasticity assumption violated"
        }
    except Exception as e:
        logger.error(f"Breusch-Pagan test failed: {e}")
        return {
            "test": "Breusch-Pagan",
            "statistic": np.nan,
            "p_value": np.nan,
            "passed": False,
            "message": f"Test failed: {str(e)}"
        }

def check_collinearity(model: sm.OLSResults) -> Dict[str, List[Dict[str, Any]]]:
    """
    Calculate Variance Inflation Factors (VIF) for all predictors.
    
    Args:
        model: Fitted OLS model results.
        
    Returns:
        Dictionary with list of VIF results for each predictor.
        Flags predictors with VIF >= 5 as high collinearity.
    """
    try:
        # Get the design matrix (exog)
        exog = model.model.exog
        feature_names = model.model.exog_names
        
        # Remove intercept (first column if it's all ones)
        # Check if first column is constant (intercept)
        if np.allclose(exog[:, 0], 1.0):
            exog_no_intercept = exog[:, 1:]
            feature_names_no_intercept = feature_names[1:]
        else:
            exog_no_intercept = exog
            feature_names_no_intercept = feature_names
        
        vif_results = []
        max_vif = 0
        
        for i, name in enumerate(feature_names_no_intercept):
            # Calculate VIF for each feature
            var_inflation_factor = 1.0 / (1.0 - stats.pearsonr(
                exog_no_intercept[:, i],
                exog_no_intercept[:, np.arange(exog_no_intercept.shape[1]) != i].mean(axis=1)
            )[0]**2) if exog_no_intercept.shape[1] > 1 else 1.0
            
            # More robust VIF calculation using matrix inversion
            # VIF_j = 1 / (1 - R_j^2) where R_j^2 is from regressing X_j on all other X's
            try:
                # Regress feature i on all other features
                other_features = exog_no_intercept[:, np.arange(exog_no_intercept.shape[1]) != i]
                if other_features.shape[1] > 0:
                    other_features = sm.add_constant(other_features)
                    aux_ols = sm.OLS(exog_no_intercept[:, i], other_features).fit()
                    r_squared = aux_ols.rsquared
                    vif = 1.0 / (1.0 - r_squared) if (1.0 - r_squared) > 1e-10 else np.inf
                else:
                    vif = 1.0
            except:
                vif = np.nan
            
            high_collinearity = vif >= 5.0
            if vif > max_vif:
                max_vif = vif
            
            vif_results.append({
                "feature": name,
                "vif": float(vif) if not np.isinf(vif) else float('inf'),
                "high_collinearity": bool(high_collinearity),
                "threshold": 5.0
            })
            
            logger.info(f"VIF for {name}: {vif:.4f} {'(HIGH)' if high_collinearity else ''}")
        
        return {
            "results": vif_results,
            "max_vif": float(max_vif) if not np.isinf(max_vif) else float('inf'),
            "threshold": 5.0,
            "passed": all(not r["high_collinearity"] for r in vif_results),
            "message": "Collinearity assumption met" if all(not r["high_collinearity"] for r in vif_results) 
                       else "High collinearity detected"
        }
    except Exception as e:
        logger.error(f"VIF calculation failed: {e}")
        return {
            "results": [],
            "max_vif": np.nan,
            "threshold": 5.0,
            "passed": False,
            "message": f"Test failed: {str(e)}"
        }

def validate_model_assumptions(model: sm.OLSResults, residuals: pd.Series, 
                               predicted: pd.Series) -> Dict[str, Any]:
    """
    Run all assumption validation tests for the regression model.
    
    Args:
        model: Fitted OLS model results.
        residuals: Series of residuals.
        predicted: Series of predicted values.
        
    Returns:
        Dictionary containing results of all assumption tests.
    """
    logger.info("Starting model assumption validation...")
    
    normality_result = check_normality(residuals)
    homoscedasticity_result = check_homoscedasticity(model, residuals, predicted)
    collinearity_result = check_collinearity(model)
    
    # Overall pass/fail
    all_passed = (
        normality_result["passed"] and 
        homoscedasticity_result["passed"] and 
        collinearity_result["passed"]
    )
    
    validation_summary = {
        "normality": normality_result,
        "homoscedasticity": homoscedasticity_result,
        "collinearity": collinearity_result,
        "all_assumptions_met": all_passed,
        "warnings": []
    }
    
    if not all_passed:
        if not normality_result["passed"]:
            validation_summary["warnings"].append("Normality assumption violated")
        if not homoscedasticity_result["passed"]:
            validation_summary["warnings"].append("Homoscedasticity assumption violated")
        if not collinearity_result["passed"]:
            validation_summary["warnings"].append("Collinearity assumption violated (VIF >= 5)")
    
    logger.info(f"Model validation complete. All assumptions met: {all_passed}")
    return validation_summary

def run_assumption_validation(data: pd.DataFrame, model_results: sm.OLSResults) -> Dict[str, Any]:
    """
    Main entry point for assumption validation.
    
    Args:
        data: Preprocessed DataFrame used for the model.
        model_results: Fitted OLS model results.
        
    Returns:
        Dictionary containing validation results.
    """
    # Extract residuals and predicted values
    residuals = pd.Series(model_results.resid, index=data.index)
    predicted = pd.Series(model_results.fittedvalues, index=data.index)
    
    # Run validation
    validation_results = validate_model_assumptions(model_results, residuals, predicted)
    
    return validation_results

@log_execution_start
@log_execution_end
def validate_regression_assumptions(config: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main function to validate regression assumptions for the ANCOVA model.
    This function is designed to be called after the model is fitted.
    
    Args:
        config: Configuration dictionary containing paths and parameters.
        
    Returns:
        Dictionary containing validation results and diagnostics.
    """
    logger.info("Running regression assumption validation (T019)")
    
    # Load preprocessed data
    processed_path = Path(config.get("processed_data_path", "data/processed/preprocessed_data.csv"))
    if not processed_path.exists():
        logger.error(f"Preprocessed data not found at {processed_path}")
        raise FileNotFoundError(f"Preprocessed data not found: {processed_path}")
    
    data = pd.read_csv(processed_path)
    logger.info(f"Loaded {len(data)} rows from {processed_path}")
    
    # Fit the ANCOVA model (re-fitting to get model object for validation)
    # Formula: post_self_esteem ~ pre_self_esteem + avatar_condition + comparison_tendency + 
    #         pre_self_esteem:comparison_tendency
    formula = "post_self_esteem ~ pre_self_esteem + avatar_condition + comparison_tendency + " \
              "pre_self_esteem:comparison_tendency"
    
    try:
        model = smf.ols(formula, data=data).fit()
        logger.info("Model fitted successfully for assumption validation")
    except Exception as e:
        logger.error(f"Failed to fit model for validation: {e}")
        return {"error": str(e), "assumptions_met": False}
    
    # Run assumption validation
    validation_results = run_assumption_validation(data, model)
    
    # Save results to processed directory
    output_path = Path(config.get("output_path", "data/processed/regression_diagnostics.json"))
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    import json
    with open(output_path, 'w') as f:
        json.dump(validation_results, f, indent=2, default=str)
    
    logger.info(f"Validation results saved to {output_path}")
    
    return validation_results

if __name__ == "__main__":
    # Example usage for testing
    from data.config import get_config
    config = get_config()
    results = validate_regression_assumptions(config)
    print(json.dumps(results, indent=2, default=str))
