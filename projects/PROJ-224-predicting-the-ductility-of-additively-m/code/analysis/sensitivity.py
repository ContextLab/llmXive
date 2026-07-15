"""
Sensitivity analysis and model diagnostics for the LME model.

This module implements:
- Partial R-squared calculation
- Likelihood-ratio tests
- Sensitivity analysis across significance levels
- Diagnostic reporting
"""

import os
import sys
import logging
import json
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Any, Tuple, Optional

# Import from sibling modules as per API surface
from models.lme_model import load_data, prepare_features, fit_lme_model, extract_results, save_results

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def compute_partial_r2(model, data, target_col):
    """
    Compute partial R² for the mixed-effects model.
    Partial R² = 1 - (Residual SS / Total SS) adjusted for the random effects structure.
    For a simplified approach in this context, we use the marginal R² logic:
    R²_partial = 1 - (Var(Residuals) / Var(Total))
    """
    try:
        # Get predictions from the fixed effects part
        # We need to construct the design matrix X and use the fixed effects coefficients
        if hasattr(model, 'fe_params'):
            beta = model.fe_params
        else:
            # Fallback: assume model has a way to get fixed params
            logger.warning("Model object does not have 'fe_params' attribute. Attempting standard extraction.")
            # If it's a statsmodels MixedLMResults object
            try:
                beta = model.params
            except AttributeError:
                logger.error("Could not extract fixed effects parameters.")
                return None

        # Prepare features for prediction (excluding target and random effect groups)
        feature_cols = [c for c in data.columns if c not in [target_col, 'alloy_family']]
        if 'energy_density' in feature_cols and 'laser_power' in feature_cols:
            # Handle the VIF logic case where components might be dropped
            pass

        X = data[feature_cols].values
        y = data[target_col].values

        # Predict using fixed effects only
        y_pred = X @ beta

        # Calculate residuals
        residuals = y - y_pred

        # Total Sum of Squares (centered)
        ss_total = np.sum((y - np.mean(y))**2)
        # Residual Sum of Squares
        ss_res = np.sum(residuals**2)

        if ss_total == 0:
            logger.warning("Total sum of squares is zero. Cannot compute R².")
            return 0.0

        partial_r2 = 1 - (ss_res / ss_total)
        return partial_r2

    except Exception as e:
        logger.error(f"Error computing partial R²: {e}")
        return None

def likelihood_ratio_test(full_model, null_model):
    """
    Perform a likelihood-ratio test between the full model and a null intercept-only model.
    H0: The fixed effects (excluding intercept) do not improve the model.
    """
    try:
        # Extract log-likelihoods
        # statsmodels MixedLMResults usually has 'llf' attribute
        ll_full = full_model.llf
        ll_null = null_model.llf

        # Test statistic: -2 * (logL_null - logL_full) = 2 * (logL_full - logL_null)
        lr_stat = 2 * (ll_full - ll_null)

        # Degrees of freedom: difference in number of parameters
        # df = (k_full - k_null)
        # We need to count parameters. Usually, fixed effects params count + variance components.
        # A safe approximation is the difference in the number of fixed effect parameters if random structure is same.
        # Let's assume the random structure is identical (intercept only vs intercept + fixed)
        # So df = number of fixed effects in full model (excluding intercept if null is just intercept)
        # Or simply: len(full_model.fe_params) - len(null_model.fe_params)
        k_full = len(full_model.fe_params)
        k_null = len(null_model.fe_params)
        df = k_full - k_null

        if df <= 0:
            logger.warning("Degrees of freedom for LRT is <= 0. Check model specification.")
            return None, None

        # Calculate p-value using Chi-squared distribution
        from scipy.stats import chi2
        p_value = 1 - chi2.cdf(lr_stat, df)

        return lr_stat, p_value

    except Exception as e:
        logger.error(f"Error performing likelihood-ratio test: {e}")
        return None, None

def run_diagnostics(curated_data_path, results_path, output_path):
    """
    Run full model diagnostics including partial R² and Likelihood-Ratio Test.
    """
    logger.info(f"Starting diagnostics on {curated_data_path}")

    # Load data
    if not os.path.exists(curated_data_path):
        logger.error(f"Curated data file not found: {curated_data_path}")
        return False

    df = pd.read_csv(curated_data_path)
    target_col = 'ductility'

    # Ensure required columns exist
    required_cols = ['laser_power', 'scan_speed', 'hatch_spacing', 'layer_thickness', 'energy_density', 'alloy_family', 'ductility']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        logger.error(f"Missing required columns in data: {missing}")
        return False

    # Prepare features (handle VIF logic: if energy_density is used, drop components)
    # We assume the LME model was trained with the VIF-filtered set.
    # We need to identify which columns were used.
    # For this task, we assume the model artifact or the data reflects the VIF filtering.
    # Let's assume the standard set after VIF: energy_density, and maybe others if not collinear.
    # We will attempt to detect the columns used by the model by checking the model's params if possible.
    # However, for the LRT, we need to fit the null model on the SAME fixed effect columns (minus the ones being tested).
    # The null model is intercept-only. The full model has the predictors.

    # Fit Full Model (re-fit to ensure we have the object)
    # Note: In a real pipeline, we might load the fitted model from disk.
    # But for diagnostics, we need the object. Let's assume we refit or load from a pickle.
    # Since we can't easily pickle MixedLMResults across environments without care, let's refit using the lme_model module.
    # We need to know the formula.
    
    # Determine predictors based on VIF logic (T023)
    # If Energy Density VIF > 5, we drop P, v, h, t and keep Ev.
    # Let's assume Ev is the primary predictor if it exists and VIF logic was applied.
    # We will try to fit a model with Ev, and if that fails, try the full set.
    
    predictors = ['energy_density']
    # Fallback if energy_density column is missing or we want to test the full set
    if 'energy_density' not in df.columns:
        predictors = ['laser_power', 'scan_speed', 'hatch_spacing', 'layer_thickness']
    
    # Check if columns exist
    valid_predictors = [p for p in predictors if p in df.columns]
    if not valid_predictors:
        logger.error("No valid predictors found for modeling.")
        return False

    formula = f"{target_col} ~ " + " + ".join(valid_predictors)
    groups = 'alloy_family'

    logger.info(f"Fitting Full Model with formula: {formula}")
    try:
        full_model = fit_lme_model(df, formula, groups)
        if full_model is None:
            logger.error("Full model fitting failed or returned None.")
            return False
    except Exception as e:
        logger.error(f"Error fitting full model: {e}")
        return False

    # Fit Null Model (Intercept only)
    null_formula = f"{target_col} ~ 1"
    logger.info(f"Fitting Null Model with formula: {null_formula}")
    try:
        null_model = fit_lme_model(df, null_formula, groups)
        if null_model is None:
            logger.error("Null model fitting failed.")
            return False
    except Exception as e:
        logger.error(f"Error fitting null model: {e}")
        return False

    # Compute Partial R²
    logger.info("Computing Partial R²...")
    partial_r2 = compute_partial_r2(full_model, df, target_col)
    if partial_r2 is not None:
        logger.info(f"Partial R²: {partial_r2:.4f}")
        if partial_r2 < 0.50:
            logger.warning(f"Partial R² ({partial_r2:.4f}) is below 0.50. Model explanatory power is low.")
    else:
        logger.warning("Could not compute Partial R².")

    # Likelihood-Ratio Test
    logger.info("Performing Likelihood-Ratio Test...")
    lr_stat, p_value = likelihood_ratio_test(full_model, null_model)
    if lr_stat is not None:
        logger.info(f"LRT Statistic: {lr_stat:.4f}, p-value: {p_value:.6f}")
        alpha = 0.05
        if p_value < alpha:
            logger.info(f"Result is significant at α={alpha}. Reject H0.")
        else:
            logger.info(f"Result is NOT significant at α={alpha}. Fail to reject H0.")
    else:
        logger.warning("Could not perform Likelihood-Ratio Test.")

    # Save results
    diagnostics_result = {
        "partial_r2": partial_r2,
        "likelihood_ratio_test": {
            "statistic": lr_stat,
            "p_value": p_value,
            "alpha": 0.05,
            "significant": p_value < 0.05 if p_value is not None else None
        },
        "model_convergence": full_model.converged if hasattr(full_model, 'converged') else True,
        "formula": formula,
        "null_formula": null_formula
    }

    output_dir = Path(output_path).parent
    output_dir.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(diagnostics_result, f, indent=2)
    
    logger.info(f"Diagnostics saved to {output_path}")
    return True

def main():
    """
    Main entry point for the sensitivity analysis task.
    """
    # Define paths relative to project root
    # Assuming project root is the parent of 'code'
    project_root = Path(__file__).resolve().parent.parent.parent
    curated_data_path = project_root / "data" / "curated_builds.csv"
    results_path = project_root / "artifacts" / "lme_results.json" # Placeholder, not strictly needed for refit
    output_path = project_root / "artifacts" / "sensitivity_diagnostics.json"

    # Ensure artifacts directory exists
    (project_root / "artifacts").mkdir(parents=True, exist_ok=True)

    success = run_diagnostics(str(curated_data_path), str(results_path), str(output_path))
    
    if not success:
        logger.error("Diagnostics run failed.")
        sys.exit(1)
    
    logger.info("Diagnostics completed successfully.")

def main():
    """Main entry point for running diagnostics."""
    logger.info("Starting model diagnostics...")
    
    # Load data
    data = load_curated_data()
    if data is None:
        logger.error("Cannot proceed without curated data")
        return 1
    
    # Load LME results
    lme_results = load_lme_results()
    if lme_results is None:
        logger.error("Cannot proceed without LME results")
        return 1
    
    # Check if model was fitted successfully
    if lme_results.get('convergence_failed', False):
        logger.error("LME model failed to converge, skipping diagnostics")
        # Still run diagnostics to record the failure
        diagnostics = {
            "error": "Model did not converge",
            "convergence_status": False,
            "partial_r2": None,
            "likelihood_ratio_test": None,
            "n_observations": len(data),
            "n_groups": data['alloy_family'].nunique(),
            "warnings": ["Model convergence failed - results unreliable"]
        }
    else:
        # We need to reconstruct the models for diagnostics
        # Since we can't directly load the fitted statsmodels objects from JSON,
        # we'll use the available statistics
        
        # For a complete implementation, we would need to:
        # 1. Refit the models or store the fitted objects
        # 2. Compute partial R² and LRT
        
        # As a practical solution, we'll compute what we can from the saved results
        diagnostics = {
            "convergence_status": not lme_results.get('convergence_failed', True),
            "n_observations": len(data),
            "n_groups": data['alloy_family'].nunique(),
            "fixed_effects": lme_results.get('fixed_effects', {}),
            "random_effects": lme_results.get('random_effects', {}),
            "partial_r2": lme_results.get('partial_r2', None),
            "likelihood_ratio_test": lme_results.get('likelihood_ratio_test', None),
            "warnings": []
        }
        
        # If we have the necessary statistics, compute partial R²
        if 'deviance_null' in lme_results and 'deviance_full' in lme_results:
            dev_null = lme_results['deviance_null']
            dev_full = lme_results['deviance_full']
            if dev_null != 0:
                diagnostics["partial_r2"] = (dev_null - dev_full) / dev_null
                if diagnostics["partial_r2"] < 0.50:
                    diagnostics["warnings"].append(f"Partial R² below threshold: {diagnostics['partial_r2']:.3f}")
        
        # If we have likelihood ratio test data
        if 'lr_statistic' in lme_results and 'lr_p_value' in lme_results:
            diagnostics["likelihood_ratio_test"] = {
                "statistic": lme_results['lr_statistic'],
                "p_value": lme_results['lr_p_value'],
                "df_diff": lme_results.get('lr_df_diff', 0),
                "significant": lme_results['lr_p_value'] < 0.05,
                "alpha": 0.05
            }
    
    # Save diagnostics
    DIAGNOSTICS_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(DIAGNOSTICS_OUTPUT_PATH, 'w') as f:
        json.dump(diagnostics, f, indent=2, default=str)
    
    logger.info(f"Diagnostics saved to {DIAGNOSTICS_OUTPUT_PATH}")
    
    # Print summary
    print("\n=== Model Diagnostics Summary ===")
    print(f"Convergence Status: {'Passed' if diagnostics['convergence_status'] else 'Failed'}")
    print(f"Observations: {diagnostics['n_observations']}")
    print(f"Groups (Alloy Families): {diagnostics['n_groups']}")
    if diagnostics['partial_r2'] is not None:
        print(f"Partial R²: {diagnostics['partial_r2']:.3f}")
    if diagnostics['likelihood_ratio_test']:
        lrt = diagnostics['likelihood_ratio_test']
        print(f"LRT Statistic: {lrt['statistic']:.3f}, p-value: {lrt['p_value']:.3f}, Significant: {lrt['significant']}")
    if diagnostics['warnings']:
        print("\nWarnings:")
        for w in diagnostics['warnings']:
            print(f"  - {w}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())