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

# Ensure we can import from the project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from statsmodels.regression.mixed_linear_model import MixedLM
from statsmodels.stats.diagnostic import linear_harvey_collier
from scipy.stats import chi2
import warnings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
ARTIFACTS_DIR = PROJECT_ROOT / "artifacts"
DATA_DIR = PROJECT_ROOT / "data"
LME_RESULTS_PATH = ARTIFACTS_DIR / "lme_results.json"
DIAGNOSTICS_OUTPUT_PATH = ARTIFACTS_DIR / "diagnostics.json"

def load_lme_results() -> Optional[Dict[str, Any]]:
    """Load the LME model results artifact."""
    if not LME_RESULTS_PATH.exists():
        logger.error(f"LME results artifact not found at {LME_RESULTS_PATH}")
        return None
    
    try:
        with open(LME_RESULTS_PATH, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load LME results: {e}")
        return None

def load_curated_data() -> Optional[pd.DataFrame]:
    """Load the curated dataset."""
    curated_path = DATA_DIR / "curated_builds.csv"
    if not curated_path.exists():
        logger.error(f"Curated data not found at {curated_path}")
        return None
    
    try:
        return pd.read_csv(curated_path)
    except Exception as e:
        logger.error(f"Failed to load curated data: {e}")
        return None

def compute_partial_r2(
    full_model: MixedLM,
    null_model: MixedLM,
    df_full: int,
    df_null: int
) -> float:
    """
    Compute partial R-squared for the full model compared to a null model.
    
    Partial R² = (Deviance_null - Deviance_full) / Deviance_null
    
    Args:
        full_model: The full mixed-effects model
        null_model: The intercept-only null model
        df_full: Degrees of freedom for the full model
        df_null: Degrees of freedom for the null model
        
    Returns:
        Partial R-squared value
    """
    dev_null = null_model.llf * -2  # Deviance = -2 * log-likelihood
    dev_full = full_model.llf * -2
    
    if dev_null == 0:
        logger.warning("Null model deviance is zero, cannot compute partial R²")
        return 0.0
    
    partial_r2 = (dev_null - dev_full) / dev_null
    return partial_r2

def likelihood_ratio_test(
    full_model: MixedLM,
    null_model: MixedLM,
    alpha: float = 0.05
) -> Dict[str, Any]:
    """
    Perform a likelihood-ratio test between full and null models.
    
    Args:
        full_model: The full mixed-effects model
        null_model: The intercept-only null model
        alpha: Significance level for the test
        
    Returns:
        Dictionary containing test statistic, p-value, and decision
    """
    ll_full = full_model.llf
    ll_null = null_model.llf
    
    # Likelihood ratio statistic
    lr_stat = -2 * (ll_null - ll_full)
    
    # Degrees of freedom difference (number of fixed effects added)
    # This is approximate; in practice, we count the number of fixed effects
    df_diff = len(full_model.fe_params) - 1  # Subtract intercept
    
    if df_diff <= 0:
        logger.warning("No additional degrees of freedom, cannot perform LRT")
        return {
            "statistic": 0.0,
            "p_value": 1.0,
            "df_diff": 0,
            "significant": False,
            "alpha": alpha
        }
    
    # P-value from chi-squared distribution
    p_value = 1 - chi2.cdf(lr_stat, df_diff)
    
    return {
        "statistic": float(lr_stat),
        "p_value": float(p_value),
        "df_diff": int(df_diff),
        "significant": p_value < alpha,
        "alpha": alpha
    }

def run_diagnostics(
    full_model: MixedLM,
    null_model: MixedLM,
    data: pd.DataFrame,
    fixed_effects: list,
    alpha: float = 0.05
) -> Dict[str, Any]:
    """
    Run comprehensive model diagnostics.
    
    Args:
        full_model: The fitted full mixed-effects model
        null_model: The fitted null (intercept-only) model
        data: The dataset used for fitting
        fixed_effects: List of fixed effect feature names
        alpha: Significance level for tests
        
    Returns:
        Dictionary containing all diagnostic results
    """
    logger.info("Running model diagnostics...")
    
    diagnostics = {
        "partial_r2": None,
        "likelihood_ratio_test": None,
        "convergence_status": full_model.converged,
        "n_observations": len(data),
        "n_groups": data['alloy_family'].nunique(),
        "fixed_effects": fixed_effects,
        "warnings": []
    }
    
    # Compute partial R²
    try:
        df_full = len(fixed_effects) + 1  # +1 for intercept
        df_null = 1  # Only intercept
        diagnostics["partial_r2"] = compute_partial_r2(full_model, null_model, df_full, df_null)
        
        if diagnostics["partial_r2"] < 0.50:
            logger.warning(f"Partial R² ({diagnostics['partial_r2']:.3f}) is below 0.50 threshold")
            diagnostics["warnings"].append(f"Partial R² below threshold: {diagnostics['partial_r2']:.3f}")
    except Exception as e:
        logger.error(f"Failed to compute partial R²: {e}")
        diagnostics["warnings"].append(f"Partial R² computation failed: {str(e)}")
    
    # Perform likelihood-ratio test
    try:
        diagnostics["likelihood_ratio_test"] = likelihood_ratio_test(full_model, null_model, alpha)
    except Exception as e:
        logger.error(f"Failed to perform likelihood-ratio test: {e}")
        diagnostics["warnings"].append(f"LRT computation failed: {str(e)}")
    
    # Check for convergence issues
    if not diagnostics["convergence_status"]:
        diagnostics["warnings"].append("Model did not converge - results may be unreliable")
    
    return diagnostics

def run_sensitivity_analysis(
    data: pd.DataFrame,
    formula: str,
    groups: str,
    alpha_levels: list = [0.05, 0.10, 0.01]
) -> Dict[str, Any]:
    """
    Run sensitivity analysis across different significance levels.
    
    Args:
        data: The dataset
        formula: Model formula string
        groups: Grouping variable name
        alpha_levels: List of significance levels to test
        
    Returns:
        Dictionary containing sensitivity analysis results
    """
    logger.info("Running sensitivity analysis...")
    
    results = {
        "alpha_levels": alpha_levels,
        "results_by_alpha": {},
        "coefficient_variation": {},
        "partial_r2_values": []
    }
    
    # Fit the full model once
    try:
        # Prepare data
        endog = data['ductility']
        exog = data[formula.split('+')[-1].strip().split(' ')[0].split('*')[0].split('-')[0].strip()]
        # This is a simplified approach; in practice, we'd use patsy to parse the formula
        
        # For now, we'll use the existing full model if available
        full_model_data = load_lme_results()
        if full_model_data and 'model_fitted' in full_model_data:
            # Use the already fitted model
            pass
        else:
            logger.warning("No pre-fitted model found, skipping sensitivity analysis")
            return results
            
    except Exception as e:
        logger.error(f"Failed to prepare for sensitivity analysis: {e}")
        return results
    
    # Since we don't have a direct way to refit with different alphas in the same model,
    # we'll analyze the coefficient stability by looking at confidence intervals
    # The alpha affects the width of the CIs, not the point estimates
    
    if full_model_data:
        coefficients = full_model_data.get('fixed_effects', {})
        std_errors = full_model_data.get('std_errors', {})
        
        for alpha in alpha_levels:
            ci_width = 2 * 1.96 * (1 + (alpha - 0.05) * 2)  # Approximate adjustment
            results["results_by_alpha"][alpha] = {
                "ci_multiplier": 1.96 if alpha == 0.05 else (2.576 if alpha == 0.01 else 1.645),
                "note": "CI width varies with alpha, point estimates remain constant"
            }
        
        # Compute coefficient variation (simple metric)
        if coefficients:
            coef_values = list(coefficients.values())
            if len(coef_values) > 0:
                results["coefficient_variation"] = {
                    "mean": float(np.mean(coef_values)),
                    "std": float(np.std(coef_values)),
                    "cv": float(np.std(coef_values) / np.mean(coef_values)) if np.mean(coef_values) != 0 else 0
                }
    
    return results

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