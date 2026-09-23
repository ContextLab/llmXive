"""
ANCOVA regression model and assumption validation.

Implements:
- T018: ANCOVA regression model
- T019: Assumption validation
- T022: Collinearity handling
- T021: Export coefficients
"""
import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
import pandas as pd
import numpy as np
import statsmodels.api as sm
import statsmodels.formula.api as smf

from utils.logger import get_logger
from data.config import get_config

logger = get_logger(__name__)

def check_normality(residuals: pd.Series) -> float:
    """Shapiro-Wilk test for normality."""
    from scipy.stats import shapiro
    stat, p_value = shapiro(residuals)
    return p_value

def check_homoscedasticity(y: pd.Series, residuals: pd.Series) -> float:
    """Breusch-Pagan test for homoscedasticity."""
    from statsmodels.stats.diagnostic import het_breuschpagan
    lm_stat, lm_p, f_p, f_p2 = het_breuschpagan(residuals, np.column_stack([y]))
    return lm_p

def check_collinearity(df: pd.DataFrame, formula: str) -> float:
    """Calculate VIF for predictors."""
    import statsmodels.api as sm
    
    # Parse formula to get predictors
    # Simple approach: assume formula is "y ~ x1 + x2 + ..."
    parts = formula.split("~")
    if len(parts) != 2:
        return 0.0
    
    predictors = parts[1].strip().split("+")
    predictors = [p.strip() for p in predictors if p.strip() and p.strip() != "1"]
    
    # Build design matrix
    X = df[predictors]
    X = sm.add_constant(X)
    
    vifs = []
    for i, col in enumerate(X.columns):
        if col == "const":
            continue
        X_other = X.drop(columns=[col])
        r2 = sm.OLS(X[col], X_other).fit().rsquared
        vif = 1.0 / (1.0 - r2) if r2 < 1.0 else np.inf
        vifs.append(vif)
    
    return max(vifs) if vifs else 0.0

def validate_model_assumptions(model, df: pd.DataFrame, formula: str) -> Dict[str, float]:
    """
    Validate model assumptions: normality, homoscedasticity, collinearity.
    
    Returns:
        Dict with shapiro_p, breusch_pagan_p, vif_max
    """
    residuals = model.resid
    y = model.model.endog
    
    shapiro_p = check_normality(pd.Series(residuals))
    breusch_p = check_homoscedasticty(y, residuals)
    vif_max = check_collinearity(df, formula)
    
    return {
        "shapiro_p": shapiro_p,
        "breusch_pagan_p": breusch_p,
        "vif_max": vif_max
    }

def fit_ancova_model(df: pd.DataFrame) -> smf.OLSResults:
    """
    Fit ANCOVA model: post_self_esteem ~ pre_self_esteem + avatar_condition + comparison_tendency + interaction
    
    Note: Using ANCOVA (outcome: post, covariate: pre) to avoid mathematical coupling.
    """
    formula = "post_self_esteem ~ pre_self_esteem + avatar_condition + comparison_tendency + avatar_condition:comparison_tendency"
    model = smf.ols(formula, data=df).fit()
    return model

def get_coefficients(model: smf.OLSResults) -> List[Dict[str, float]]:
    """Extract coefficients from model."""
    coeffs = []
    for name, row in model.summary2().tables[1].iterrows():
        coeffs.append({
            "name": name,
            "estimate": row["Coef."],
            "std_err": row["Std.Err."],
            "p_value": row["P>|t|"]
        })
    return coeffs

def run_regression_analysis():
    """
    Run full regression analysis and export results.
    
    Artifacts:
    - data/processed/regression_coefficients.csv
    - data/processed/model_diagnostics.json
    """
    config = get_config()
    processed_dir = Path(config["paths"]["data_processed"])
    
    # Load imputed data
    imputed_file = processed_dir / "imputed_data.csv"
    if not imputed_file.exists():
        raise FileNotFoundError(f"Imputed data not found: {imputed_file}")
    
    df = pd.read_csv(imputed_file)
    logger.info(f"Loaded {len(df)} rows for regression")
    
    # Fit model
    model = fit_ancova_model(df)
    logger.info("ANCOVA model fitted successfully")
    
    # Validate assumptions
    assumptions = validate_model_assumptions(model, df, "post_self_esteem ~ pre_self_esteem + avatar_condition + comparison_tendency + avatar_condition:comparison_tendency")
    
    # Get coefficients
    coeffs = get_coefficients(model)
    
    # Export coefficients
    coeffs_file = processed_dir / "regression_coefficients.csv"
    pd.DataFrame(coeffs).to_csv(coeffs_file, index=False)
    logger.info(f"Saved coefficients to {coeffs_file}")
    
    # Export diagnostics
    diagnostics_file = processed_dir / "model_diagnostics.json"
    diagnostics = {
        "assumptions": assumptions,
        "r_squared": model.rsquared,
        "adj_r_squared": model.rsquared_adj,
        "n_obs": model.nobs
    }
    
    # T022: Collinearity warning
    if assumptions["vif_max"] >= 5:
        diagnostics["collinearity_warning"] = True
        logger.warning(f"High collinearity detected: VIF_max={assumptions['vif_max']}")
    else:
        diagnostics["collinearity_warning"] = False
    
    import json
    with open(diagnostics_file, 'w') as f:
        json.dump(diagnostics, f, indent=2)
    logger.info(f"Saved diagnostics to {diagnostics_file}")
    
    return model, coeffs, assumptions

if __name__ == "__main__":
    run_regression_analysis()
