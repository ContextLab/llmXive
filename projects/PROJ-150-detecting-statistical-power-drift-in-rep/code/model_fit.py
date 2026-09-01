"""
code/model_fit.py
-----------------
Implements the statistical modeling pipeline for detecting statistical power drift.
This script is invoked by the quickstart run-book.

It performs:
1. Loads grouping validation (T011b output).
2. Fits a Pilot OLS model to control for input drift (effect_size, sample_size).
3. Calculates power_residuals.
4. Fits the Full LMM (power_residual ~ year + (1|field)) dynamically based on validation.
5. Fits the Reduced LMM (power_residual ~ 1).
6. Performs Likelihood Ratio Test (LRT).
7. Extracts metrics and saves to results/lmm_final_summary.json.
"""
import os
import sys
import json
import pickle
import logging
from pathlib import Path

import pandas as pd
import numpy as np
import statsmodels.formula.api as smf
import statsmodels.api as sm

# Ensure project root is in path for imports if running from subdirectory
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from code.logging_config import get_module_logger

logger = get_module_logger("model_fit")

def load_grouping_validation(validation_path: str) -> dict:
    """Load the grouping validation JSON produced by T011b."""
    if not os.path.exists(validation_path):
        raise FileNotFoundError(f"Grouping validation file not found at {validation_path}")
    with open(validation_path, 'r') as f:
        return json.load(f)

def fit_pilot_ols(df: pd.DataFrame) -> tuple:
    """
    Fit pilot OLS: power_estimate ~ effect_size + sample_size.
    Returns the fitted model and the dataframe with predicted values added.
    """
    logger.info("Fitting Pilot OLS model to control for input drift...")
    # Ensure columns exist
    required_cols = ['power_estimate', 'effect_size', 'sample_size']
    if not all(col in df.columns for col in required_cols):
        raise ValueError(f"Pilot OLS requires columns: {required_cols}")

    model = smf.ols("power_estimate ~ effect_size + sample_size", data=df).fit()
    df['predicted_power'] = model.predict()
    return model, df

def calculate_residuals(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate power_residual = power_estimate - predicted_power."""
    if 'predicted_power' not in df.columns:
        raise ValueError("predicted_power column missing. Run fit_pilot_ols first.")
    df['power_residual'] = df['power_estimate'] - df['predicted_power']
    return df

def build_random_effect_formula(validation: dict) -> tuple:
    """
    Dynamically build the random effects formula based on validation status.
    Returns (group_col_for_statsmodels, formula_string).
    Note: statsmodels MixedLM supports only ONE grouping variable.
    We prioritize 'field' if valid, else 'original_study_id'.
    """
    valid_groups = []
    if validation.get("field", {}).get("status") == "valid":
        valid_groups.append("field")
    if validation.get("original_study_id", {}).get("status") == "valid":
        valid_groups.append("original_study_id")

    if not valid_groups:
        logger.warning("No valid random effect groups found. Falling back to OLS for residuals.")
        return None, None

    # Statsmodels MixedLM limitation: only one grouping variable allowed in 'groups' argument.
    # We select the highest priority group (field) if available.
    group_col = valid_groups[0]
    logger.info(f"Using '{group_col}' as the random effect grouping variable.")
    return group_col, None # Formula string not used directly for RE in MixedLM constructor

def fit_full_lmm(df: pd.DataFrame, group_col: str) -> object:
    """Fit the Full LMM: power_residual ~ year + (1|group_col)."""
    if group_col is None:
        raise ValueError("Cannot fit LMM without a grouping column.")

    logger.info(f"Fitting Full LMM: power_residual ~ year + (1|{group_col})")
    # Check for convergence issues or singular fit later
    try:
        model = smf.mixedlm("power_residual ~ year", df, groups=df[group_col])
        result = model.fit()
        if not result.converged:
            logger.warning("Full LMM did not converge. Attempting refit with different optimizer...")
            result = model.fit(optimizer='bfgs')
        return result
    except Exception as e:
        logger.error(f"Failed to fit Full LMM: {e}")
        raise

def fit_reduced_lmm(df: pd.DataFrame, group_col: str) -> object:
    """Fit the Reduced LMM: power_residual ~ 1 + (1|group_col)."""
    if group_col is None:
        # If no group, reduced model is just intercept OLS
        logger.info("No grouping variable. Fitting reduced OLS model: power_residual ~ 1")
        model = smf.ols("power_residual ~ 1", data=df)
        return model.fit()

    logger.info(f"Fitting Reduced LMM: power_residual ~ 1 + (1|{group_col})")
    try:
        model = smf.mixedlm("power_residual ~ 1", df, groups=df[group_col])
        return model.fit()
    except Exception as e:
        logger.error(f"Failed to fit Reduced LMM: {e}")
        raise

def perform_lrt(full_result, reduced_result) -> dict:
    """Perform Likelihood Ratio Test."""
    logger.info("Performing Likelihood Ratio Test...")
    # LRT statistic: 2 * (llf_full - llf_reduced)
    lrt_stat = 2 * (full_result.llf - reduced_result.llf)
    # Degrees of freedom difference: Full has 'year' fixed effect (1 df) vs Reduced (0 df)
    # Assuming random effects structure is same (or reduced has same RE but no fixed year)
    df_diff = 1
    p_value = 1 - sm.stats.chi2.cdf(lrt_stat, df_diff)

    return {
        "chi2_statistic": float(lrt_stat),
        "df_diff": df_diff,
        "p_value_lrt": float(p_value)
    }

def extract_year_metrics(full_result) -> dict:
    """Extract slope, SE, and 95% CI for the 'year' predictor."""
    params = full_result.params
    bse = full_result.bse

    slope = float(params["year"])
    se = float(bse["year"])
    ci_lower = slope - 1.96 * se
    ci_upper = slope + 1.96 * se

    return {
        "slope_year": slope,
        "se_year": se,
        "ci_lower": ci_lower,
        "ci_upper": ci_upper
    }

def save_results(output_path: str, metrics: dict, lrt_results: dict, group_col: str):
    """Save the final summary to JSON."""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    final_output = {
        **metrics,
        **lrt_results,
        "grouping_variable_used": group_col,
        "note": "Statsmodels MixedLM supports only one random effect grouping variable. Using '{group_col}' as primary."
    }

    with open(output_path, 'w') as f:
        json.dump(final_output, f, indent=2)
    logger.info(f"Saved final results to {output_path}")

def main():
    """Main entry point for the model fitting pipeline."""
    logger.info("Starting model fitting pipeline (T011c implementation).")

    # Paths
    # Assume running from project root or script handles relative paths correctly
    # Based on execution feedback, paths are relative to project root
    base_path = Path(__file__).resolve().parent.parent
    cleaned_data_path = base_path / "data" / "derived" / "cleaned_data.csv"
    validation_path = base_path / "data" / "derived" / "grouping_validation.json"
    output_path = base_path / "results" / "lmm_final_summary.json"
    residuals_path = base_path / "data" / "derived" / "residuals.csv"
    pilot_model_path = base_path / "data" / "derived" / "pilot_ols_model.pkl"

    # 1. Load Data
    if not cleaned_data_path.exists():
        raise FileNotFoundError(f"Cleaned data not found at {cleaned_data_path}. Run T011a first.")
    df = pd.read_csv(cleaned_data_path)
    logger.info(f"Loaded {len(df)} rows from cleaned_data.csv")

    # 2. Load Validation
    if not validation_path.exists():
        raise FileNotFoundError(f"Validation file not found at {validation_path}. Run T011b first.")
    validation = load_grouping_validation(str(validation_path))

    # 3. Fit Pilot OLS & Calculate Residuals
    # Note: T011a might have done this, but we do it here to ensure consistency and save artifacts
    # as per T011c spec.
    pilot_model, df = fit_pilot_ols(df)
    df = calculate_residuals(df)

    # Save intermediate artifacts required by spec
    with open(str(pilot_model_path), 'wb') as f:
        pickle.dump(pilot_model, f)
    logger.info(f"Saved pilot model to {pilot_model_path}")

    # Save residuals dataframe
    residuals_df = df[['study_id', 'year', 'field', 'original_study_id', 'power_residual']]
    residuals_df.to_csv(residuals_path, index=False)
    logger.info(f"Saved residuals to {residuals_path}")

    # 4. Build Random Effects Formula
    group_col, _ = build_random_effect_formula(validation)

    # 5. Fit Models
    if group_col:
        full_result = fit_full_lmm(df, group_col)
        reduced_result = fit_reduced_lmm(df, group_col)
    else:
        # Fallback if no valid groups (should be rare given validation)
        logger.warning("No valid groups. Fitting OLS for full and reduced models.")
        full_result = smf.ols("power_residual ~ year", data=df).fit()
        reduced_result = smf.ols("power_residual ~ 1", data=df).fit()

    # 6. Perform LRT
    lrt_results = perform_lrt(full_result, reduced_result)

    # 7. Extract Metrics
    metrics = extract_year_metrics(full_result)

    # 8. Save Results
    save_results(str(output_path), metrics, lrt_results, group_col)

    logger.info("Model fitting pipeline completed successfully.")

if __name__ == "__main__":
    main()