import os
import sys
import json
import pandas as pd
import numpy as np
import statsmodels.api as sm
from statsmodels.formula.api import ols, gls
from statsmodels.stats.outliers_influence import variance_inflation_factor
from logger import get_logger
from utils import load_json, save_json, ensure_directory

logger = get_logger(__name__)

def validate_data_structure(data_path: str) -> dict:
    """
    Validates the data structure (between vs within subjects) based on participant_id repetition.
    Writes the result to data/processed/structure_config.json.
    """
    ensure_directory("data/processed")
    df = pd.read_csv(data_path)
    
    if 'participant_id' not in df.columns:
        raise ValueError("Data must contain 'participant_id' column.")
    
    subject_counts = df['participant_id'].nunique()
    total_rows = len(df)
    
    # If every participant appears exactly once, it's between-subjects
    # If participants appear multiple times, it's within-subjects (or mixed)
    is_between = (df['participant_id'].value_counts() == 1).all()
    
    structure_type = "between-subjects" if is_between else "within-subjects"
    n_subjects = subject_counts
    
    config = {
        "type": structure_type,
        "n_subjects": int(n_subjects)
    }
    
    config_path = "data/processed/structure_config.json"
    save_json(config_path, config)
    logger.info(f"Data structure validated: {structure_type} ({n_subjects} subjects)")
    
    return config

def fit_fixed_effects(df: pd.DataFrame, formula: str = None) -> dict:
    """
    Fits a Fixed-Effects model (OLS/GLM) using statsmodels.
    Formula: risk_taking ~ status_level * observed_behavior
    Used when structure_config is 'between-subjects'.
    
    Args:
        df: Processed dataframe with columns: risk_taking_score, status_level, observed_behavior
        formula: Optional custom formula. Defaults to interaction of status and behavior.
    
    Returns:
        dict: Model results summary, coefficients, p-values, and VIFs.
    """
    if formula is None:
        formula = "risk_taking_score ~ status_level * observed_behavior"
    
    logger.info(f"Fitting Fixed-Effects model with formula: {formula}")
    
    # Ensure categorical variables are treated as such for interaction
    if 'status_level' in df.columns:
        df['status_level'] = pd.Categorical(df['status_level'])
    if 'observed_behavior' in df.columns:
        df['observed_behavior'] = pd.Categorical(df['observed_behavior'])
    
    try:
        model = ols(formula, data=df).fit()
    except Exception as e:
        logger.error(f"OLS model fitting failed: {e}")
        raise e
    
    # Extract coefficients
    results = {
        "model_type": "Fixed-Effects (OLS)",
        "formula": formula,
        "rsquared": float(model.rsquared),
        "rsquared_adj": float(model.rsquared_adj),
        "nobs": int(model.nobs),
        "coefficients": {},
        "pvalues": {},
        "vif": {}
    }
    
    # Process summary table
    summary_df = model.summary2().tables[1]
    for idx, row in summary_df.iterrows():
        coef_name = str(idx)
        results["coefficients"][coef_name] = float(row["Coef."])
        results["pvalues"][coef_name] = float(row["P>|t|"])
    
    # Calculate VIF
    # VIF requires an intercept column in the design matrix
    y = model.model.endog
    X = model.model.exog
    
    # Check for constant column to avoid singular matrix issues in VIF calc if not handled by statsmodels
    # statsmodels ols usually adds constant automatically if not present, but let's be safe for VIF
    if not np.any(np.all(np.isclose(X, X[0,:]), axis=0)): 
        # If no constant column found in X, we might need to handle it, but ols() usually handles it.
        # We calculate VIF on the design matrix used by the model.
        pass

    vif_data = {}
    feature_names = model.model.exog_names
    
    for i, name in enumerate(feature_names):
        if name == "Intercept":
            continue # Skip intercept for VIF
        try:
            vif = variance_inflation_factor(X, i)
            vif_data[name] = float(vif)
        except Exception as e:
            logger.warning(f"Could not calculate VIF for {name}: {e}")
            vif_data[name] = None
    
    results["vif"] = vif_data
    
    logger.info(f"Fixed-Effects model fit complete. R-squared: {model.rsquared:.4f}")
    return results

def fit_mixed_effects(df: pd.DataFrame, formula: str = None) -> dict:
    """
    Fits a Mixed-Effects model using statsmodels.
    Formula: risk_taking ~ status_level * observed_behavior + (1|participant_id)
    Used when structure_config is 'within-subjects'.
    """
    if formula is None:
        # Note: statsmodels mixedlm formula syntax differs slightly from lme4
        # (1|participant_id) is converted to groups='participant_id'
        pass 
    
    logger.warning("Mixed effects implementation placeholder. T021a handles this.")
    # This function exists for API consistency but T021a is the active implementation for mixed effects.
    # For T021b, we focus on Fixed Effects.
    return {}

def calculate_vif(results: dict) -> dict:
    """
    Calculates Variance Inflation Factors (VIF) for all predictors.
    Flags if VIF > 5.0.
    """
    vif_data = results.get("vif", {})
    flagged = {}
    for name, val in vif_data.items():
        if val is not None and val > 5.0:
            flagged[name] = val
    return flagged

def analyze_interaction(df: pd.DataFrame, structure_config: dict, family_type: str = "gaussian") -> dict:
    """
    Selects and runs the appropriate model (Fixed or Mixed) based on structure_config.
    """
    structure_type = structure_config.get("type", "between-subjects")
    
    if structure_type == "between-subjects":
        return fit_fixed_effects(df)
    else:
        return fit_mixed_effects(df)

def main():
    """
    Main entry point to run the analysis pipeline.
    """
    # Load processed data
    data_path = "data/processed/processed_data.csv"
    if not os.path.exists(data_path):
        logger.error(f"Processed data not found at {data_path}. Run preprocessing first.")
        sys.exit(1)
    
    df = pd.read_csv(data_path)
    
    # Load structure config
    config_path = "data/processed/structure_config.json"
    if not os.path.exists(config_path):
        logger.error(f"Structure config not found at {config_path}. Run validation first.")
        sys.exit(1)
    
    structure_config = load_json(config_path)
    
    # Run analysis
    results = analyze_interaction(df, structure_config)
    
    # Save results
    output_path = "data/processed/analysis_results.json"
    save_json(output_path, results)
    logger.info(f"Analysis results saved to {output_path}")
    
    # Print summary
    print(json.dumps(results, indent=2))

if __name__ == "__main__":
    main()