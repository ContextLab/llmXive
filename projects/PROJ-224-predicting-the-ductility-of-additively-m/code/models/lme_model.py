"""
Linear Mixed-Effects model implementation for the ductility prediction pipeline.
"""
import os
import sys
import logging
import json
import pandas as pd
import numpy as np
from pathlib import Path
import warnings

# Suppress warnings for cleaner output
warnings.filterwarnings('ignore')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
ARTIFACTS_DIR = PROJECT_ROOT / "artifacts"
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

def load_data() -> pd.DataFrame:
    """Load filtered dataset."""
    input_path = DATA_DIR / "filtered_builds_final.csv"
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        sys.exit(1)
    return pd.read_csv(input_path)

def prepare_features(df: pd.DataFrame) -> tuple:
    """Prepare features and target for LME model."""
    # Select fixed effects (exclude categorical and target)
    exclude_cols = ['alloy_family', 'ductility']
    feature_cols = [col for col in df.columns if col not in exclude_cols and df[col].dtype in ['float64', 'int64']]
    
    if not feature_cols:
        logger.error("No feature columns found")
        sys.exit(1)
    
    X = df[feature_cols]
    y = df['ductility']
    groups = df['alloy_family']
    
    return X, y, groups, feature_cols

def fit_lme_model(X: pd.DataFrame, y: pd.Series, groups: pd.Series, feature_cols: list):
    """Fit Linear Mixed-Effects model."""
    logger.info("Fitting Linear Mixed-Effects model")
    
    try:
        import statsmodels.api as sm
        import statsmodels.formula.api as smf
    except ImportError:
        logger.error("statsmodels not installed. Please run: pip install statsmodels")
        sys.exit(1)
    
    # Create formula
    fixed_effects = " + ".join(feature_cols)
    formula = f"ductility ~ {fixed_effects} + (1|alloy_family)"
    
    # Fit model
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        model = smf.mixedlm(formula, df, groups=df['alloy_family'])
        result = model.fit()
    
    # Check convergence
    convergence_failed = not result.converged
    if convergence_failed:
        logger.error("LME model failed to converge!")
    
    return result, convergence_failed

def extract_results(result, convergence_failed: bool, feature_cols: list) -> dict:
    """Extract model results."""
    logger.info("Extracting model results")
    
    # Fixed effects
    fixed_effects = result.fe_params
    std_errors = result.bse
    p_values = result.pvalues
    
    # Standardized coefficients (simple z-score standardization)
    standardized_coefs = {}
    for col in feature_cols:
        coef = fixed_effects[col]
        std_x = df[col].std()
        std_y = df['ductility'].std()
        std_coef = coef * (std_x / std_y)
        standardized_coefs[col] = std_coef
    
    # 95% CIs
    conf_int = result.conf_int(alpha=0.05)
    ci_95 = {}
    for i, col in enumerate(feature_cols):
        ci_95[col] = [conf_int.iloc[i, 0], conf_int.iloc[i, 1]]
    
    # Random effects
    random_effects = result.random_effects
    
    # Partial R² (approximation)
    # Compare with null model
    try:
        null_formula = "ductility ~ 1 + (1|alloy_family)"
        null_model = smf.mixedlm(null_formula, df, groups=df['alloy_family'])
        null_result = null_model.fit()
        
        # Likelihood ratio test
        lr_stat = 2 * (result.llf - null_result.llf)
        from scipy.stats import chi2
        df_diff = len(feature_cols)
        p_value_lr = 1 - chi2.cdf(lr_stat, df_diff)
        
        # Pseudo R²
        r2_null = 1 - (null_result.llf / result.llf) if result.llf != 0 else 0
        partial_r2 = max(0, r2_null)
    except Exception as e:
        logger.warning(f"Could not compute partial R²: {e}")
        partial_r2 = 0.0
    
    return {
        "convergence_failed": convergence_failed,
        "fixed_effects": fixed_effects.tolist(),
        "standardized_coefficients": standardized_coefs,
        "p_values": p_values.tolist(),
        "ci_95": ci_95,
        "random_effects": {k: v.tolist() for k, v in random_effects.items()},
        "partial_r2": partial_r2,
        "log_likelihood": result.llf,
        "aic": result.aic,
        "bic": result.bic
    }

def save_results(results: dict):
    """Save results to JSON."""
    output_path = ARTIFACTS_DIR / "lme_model_results.json"
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Saved LME results to {output_path}")

def main():
    """Main entry point for LME model."""
    logger.info("Starting LME model training")
    
    # Load data
    df = load_data()
    
    # Prepare features
    X, y, groups, feature_cols = prepare_features(df)
    
    # Fit model
    result, convergence_failed = fit_lme_model(X, y, groups, feature_cols)
    
    # Extract results
    results = extract_results(result, convergence_failed, feature_cols)
    
    # Save results
    save_results(results)
    
    return results

if __name__ == "__main__":
    main()
