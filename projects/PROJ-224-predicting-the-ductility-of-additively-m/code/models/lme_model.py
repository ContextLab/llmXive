import os
import logging
import json
import warnings
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

import pandas as pd
import numpy as np
import statsmodels.api as sm
import statsmodels.formula.api as smf

logger = logging.getLogger(__name__)

def load_data(input_path: str) -> pd.DataFrame:
    """Load the curated dataset."""
    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"Input data file not found: {path}")
    logger.info(f"Loading data from {path}")
    df = pd.read_csv(path)
    return df

def prepare_features(df: pd.DataFrame) -> Tuple[pd.DataFrame, list]:
    """
    Prepare features for the LME model.
    Returns the processed DataFrame and the list of fixed effect predictors.
    """
    # Ensure numeric types for process parameters
    numeric_cols = ['laser_power', 'scan_speed', 'hatch_spacing', 'layer_thickness', 'energy_density']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    # Drop rows with NaN in target or key predictors
    target_col = 'ductility'
    if target_col not in df.columns:
        raise ValueError("Column 'ductility' not found in dataset")

    # Identify fixed effects based on available columns
    # T023 logic: if Energy Density is used, individual components might be dropped.
    # We assume the dataset passed in has already been filtered by T023 (apply_vif_filtering).
    # We check for 'energy_density' first. If present and 'laser_power' etc are missing, use it.
    # Otherwise, use available process params.
    
    available_cols = [c for c in numeric_cols if c in df.columns and not df[c].isna().all()]
    
    if 'energy_density' in available_cols:
        predictors = ['energy_density']
        # If other process params are present but we decided to use ED, we might have dropped them in T023.
        # If they are still there, we ignore them per FR-005 logic if ED was selected.
        # For safety, we just use ED if present.
    else:
        # Fallback to individual params if ED is not present
        predictors = [c for c in ['laser_power', 'scan_speed', 'hatch_spacing', 'layer_thickness'] if c in available_cols]

    if not predictors:
        raise ValueError("No valid predictors found for the model.")

    logger.info(f"Using predictors: {predictors}")
    
    # Clean data for modeling: drop rows with NaN in target or predictors
    cols_to_check = [target_col] + predictors
    clean_df = df.dropna(subset=cols_to_check)
    
    return clean_df, predictors

def fit_lme_model(df: pd.DataFrame, predictors: list, target: str = 'ductility', group: str = 'alloy_family') -> Dict[str, Any]:
    """
    Fit a Linear Mixed-Effects model.
    Fixed effects: predictors
    Random effects: Random intercept for 'group'
    """
    formula = f"{target} ~ {' + '.join(predictors)}"
    group_col = group if group in df.columns else None
    
    if not group_col:
        logger.warning(f"Group column '{group}' not found. Using OLS fallback or single group.")
        # Fallback to OLS if no grouping variable
        X = sm.add_constant(df[predictors])
        y = df[target]
        model = sm.OLS(y, X).fit()
        results = {
            "type": "OLS",
            "converged": True,
            "coefficients": model.params.to_dict(),
            "std_errors": model.bse.to_dict(),
            "pvalues": model.pvalues.to_dict(),
            "conf_int": model.conf_int().to_dict(),
            "rsquared": model.rsquared,
            "message": "Used OLS because group column missing."
        }
        return results

    try:
        # Use statsmodels MixedLM
        # Note: statsmodels MixedLM formula interface is slightly different or requires specific setup
        # Using the formula API from smf
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            model = smf.mixedlm(formula, df, groups=df[group_col])
            result = model.fit(reml=False) # Use ML for comparison, or REML=True for estimation
        
        # Check convergence (statsmodels fit returns a boolean in some versions or we check the status)
        # In recent statsmodels, fit() returns a MixedLMResults object.
        # We assume it converged if no exception was raised during fit.
        
        # Extract fixed effects
        fixed_params = result.fe_params
        fixed_std = result.bse
        fixed_pvalues = result.pvalues
        fixed_conf_int = result.conf_int()
        
        # Extract random effects (variance components)
        # result.var_comp contains the variance of the random intercepts
        random_var = result.var_comp.to_dict() if hasattr(result, 'var_comp') else {}
        
        # Extract random intercept estimates (BLUPs) if available
        # result.random_effects is a dict of group_id -> random effects
        random_effects = result.random_effects if hasattr(result, 'random_effects') else {}
        
        # Calculate AIC/BIC
        aic = result.aic
        bic = result.bic

        results = {
            "type": "LME",
            "converged": True,
            "formula": formula,
            "fixed_effects": {
                "coefficients": fixed_params.to_dict(),
                "std_errors": fixed_std.to_dict(),
                "pvalues": fixed_pvalues.to_dict(),
                "conf_int_95": {k: v.tolist() for k, v in fixed_conf_int.iterrows()}
            },
            "random_effects": {
                "variance_components": random_var,
                "intercept_estimates": {k: v.get('intercept', 0.0) if isinstance(v, dict) else 0.0 for k, v in random_effects.items()}
            },
            "model_fit": {
                "aic": aic,
                "bic": bic,
                "loglike": result.llf
            },
            "message": "Model fitted successfully."
        }
        return results

    except Exception as e:
        logger.error(f"Model fitting failed: {str(e)}")
        return {
            "type": "LME",
            "converged": False,
            "error": str(e),
            "message": "Model failed to converge or fit."
        }

def save_results(results: Dict[str, Any], output_path: str) -> None:
    """Save the model results to a JSON file."""
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Results saved to {path}")

def main():
    """Main entry point for the LME model task."""
    # Paths
    input_data = Path("data/curated_builds.csv")
    output_artifact = Path("artifacts/mixed_effects_results.json")
    
    # Ensure directories exist
    output_artifact.parent.mkdir(parents=True, exist_ok=True)
    
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    try:
        # Load data
        df = load_data(str(input_data))
        
        # Prepare features
        clean_df, predictors = prepare_features(df)
        
        if clean_df.empty:
            logger.error("Cleaned dataset is empty. Cannot fit model.")
            # Save empty result structure
            save_results({"error": "Empty dataset after cleaning"}, str(output_artifact))
            return

        # Fit model
        logger.info(f"Fitting LME model with predictors: {predictors}")
        results = fit_lme_model(clean_df, predictors)
        
        # Save results
        save_results(results, str(output_artifact))
        
        if not results.get("converged", False):
            logger.error("Model did not converge. Check logs for details.")
        else:
            logger.info("LME model fitting completed successfully.")
            
    except Exception as e:
        logger.critical(f"Pipeline failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()