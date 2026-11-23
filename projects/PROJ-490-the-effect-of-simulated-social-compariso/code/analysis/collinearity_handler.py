import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

import pandas as pd
import numpy as np
from statsmodels.stats.outliers_influence import VarianceInflationFactor
import statsmodels.api as sm

from utils.logger import get_logger
from utils.validators import validate_json_against_schema

logger = get_logger(__name__)

def calculate_vif(df: pd.DataFrame, predictor_cols: List[str]) -> Dict[str, float]:
    """
    Calculate Variance Inflation Factor (VIF) for each predictor.

    Args:
        df: DataFrame containing predictor variables.
        predictor_cols: List of column names to calculate VIF for.

    Returns:
        Dictionary mapping column names to their VIF values.
    """
    logger.info(f"Calculating VIF for predictors: {predictor_cols}")

    # Ensure we have valid data (no NaNs for VIF calculation)
    subset = df[predictor_cols].dropna()

    if subset.empty:
        logger.warning("No valid data rows for VIF calculation.")
        return {col: float('nan') for col in predictor_cols}

    # Add constant for intercept
    X = sm.add_constant(subset)

    vif_results = {}
    for i, col in enumerate(predictor_cols):
        # VIF for a variable is calculated by regressing it against all other variables
        # Using the VarianceInflationFactor class from statsmodels
        try:
            vif = VarianceInflationFactor(X, col).vif
            vif_results[col] = float(vif)
        except Exception as e:
            logger.error(f"Error calculating VIF for {col}: {e}")
            vif_results[col] = float('nan')

    logger.info(f"VIF calculated: {vif_results}")
    return vif_results

def check_collinearity_flags(vif_results: Dict[str, float], threshold: float = 5.0) -> Tuple[bool, List[str]]:
    """
    Check if any VIF values exceed the collinearity threshold.

    Args:
        vif_results: Dictionary of VIF values per predictor.
        threshold: VIF threshold for flagging collinearity (default 5.0).

    Returns:
        Tuple of (flag_triggered, list_of_flagged_columns).
    """
    flagged = [col for col, vif in vif_results.items() if not np.isnan(vif) and vif >= threshold]
    flag_triggered = len(flagged) > 0

    if flag_triggered:
        logger.warning(f"Collinearity detected! VIF >= {threshold} for: {flagged}")
    else:
        logger.info(f"No collinearity detected (threshold={threshold}).")

    return flag_triggered, flagged

def generate_descriptive_framing(flagged_cols: List[str], all_coeffs: Dict[str, Any]) -> str:
    """
    Generate a descriptive framing for the results when collinearity is present.

    Args:
        flagged_cols: List of columns with high VIF.
        all_coeffs: Dictionary of all regression coefficients.

    Returns:
        Descriptive string framing the results.
    """
    if not flagged_cols:
        return "No collinearity concerns detected. Independent effects can be discussed."

    warning_msg = (
        f"Collinearity detected in the following variables: {', '.join(flagged_cols)}. "
        f"VIF values for these predictors were >= 5.0. "
        f"As a result, we frame these results descriptively as associations. "
        f"We avoid claiming independent causal effects for these specific variables due to "
        f"the potential for variance inflation and unstable coefficient estimates."
    )
    return warning_msg

def run_collinearity_analysis(
    df: pd.DataFrame,
    predictor_cols: List[str],
    threshold: float = 5.0
) -> Tuple[Dict[str, float], bool, List[str]]:
    """
    Run the full collinearity analysis pipeline.

    Args:
        df: DataFrame with data.
        predictor_cols: List of predictor variable names.
        threshold: VIF threshold.

    Returns:
        Tuple of (vif_results, flag_triggered, flagged_cols).
    """
    vif_results = calculate_vif(df, predictor_cols)
    flag_triggered, flagged_cols = check_collinearity_flags(vif_results, threshold)
    return vif_results, flag_triggered, flagged_cols

def update_diagnostics_with_collinearity(
    diagnostics: Dict[str, Any],
    vif_results: Dict[str, float],
    flag_triggered: bool,
    flagged_cols: List[str],
    all_coeffs: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Update the model diagnostics dictionary with collinearity information.

    Args:
        diagnostics: Existing diagnostics dictionary.
        vif_results: Calculated VIF values.
        flag_triggered: Whether collinearity was flagged.
        flagged_cols: List of flagged columns.
        all_coeffs: Regression coefficients.

    Returns:
        Updated diagnostics dictionary.
    """
    if "assumptions" not in diagnostics:
        diagnostics["assumptions"] = {}

    diagnostics["assumptions"]["vif_max"] = max(v for v in vif_results.values() if not np.isnan(v)) if vif_results else 0.0
    diagnostics["assumptions"]["vif_details"] = vif_results

    if flag_triggered:
        diagnostics["collinearity_warning"] = generate_descriptive_framing(flagged_cols, all_coeffs)
        logger.warning("Updated diagnostics with collinearity warning.")
    else:
        diagnostics["collinearity_warning"] = None

    return diagnostics

def main():
    """
    Main entry point for collinearity analysis task.
    Reads imputed data, runs VIF analysis, and updates model_diagnostics.json.
    """
    config_path = Path("code/data/config.py")
    # Assuming config is imported or paths are standard
    project_root = Path(__file__).parent.parent.parent
    data_processed_path = project_root / "data" / "processed"
    imputed_file = data_processed_path / "imputed_data.csv"
    diagnostics_file = data_processed_path / "model_diagnostics.json"

    if not imputed_file.exists():
        logger.error(f"Imputed data file not found: {imputed_file}. Cannot run collinearity analysis.")
        return

    # Load imputed data
    df = pd.read_csv(imputed_file)
    logger.info(f"Loaded imputed data with shape: {df.shape}")

    # Define predictors based on the ANCOVA model:
    # Outcome: post_self_esteem
    # Covariate: pre_self_esteem
    # Predictors: avatar_condition, comparison_tendency, interaction
    # For VIF, we check the predictors used in the regression formula.
    # Formula typically: post ~ pre + avatar + comparison + avatar*comparison
    # VIF is calculated on the independent variables: pre, avatar, comparison (and interaction if included as a separate term)
    # To be safe, we include all independent variables.
    predictor_cols = ["pre_self_esteem", "avatar_condition", "comparison_tendency"]

    # If interaction is a pre-calculated column, include it.
    # Usually interaction is created on the fly in the formula, but if it exists in DF:
    if "interaction" in df.columns:
        predictor_cols.append("interaction")

    # Run analysis
    vif_results, flag_triggered, flagged_cols = run_collinearity_analysis(df, predictor_cols)

    # Load existing diagnostics if available
    diagnostics = {}
    if diagnostics_file.exists():
        with open(diagnostics_file, "r") as f:
            diagnostics = json.load(f)
        logger.info("Loaded existing diagnostics.")
    else:
        logger.info("No existing diagnostics file found. Creating new one.")

    # Mock coefficients for framing ( ideally we load from regression_coefficients.csv )
    coeffs_file = data_processed_path / "regression_coefficients.csv"
    all_coeffs = {}
    if coeffs_file.exists():
        coeffs_df = pd.read_csv(coeffs_file)
        all_coeffs = coeffs_df.to_dict(orient='records')
    else:
        logger.warning("Regression coefficients file not found. Using empty dict for framing.")

    # Update diagnostics
    updated_diagnostics = update_diagnostics_with_collinearity(
        diagnostics,
        vif_results,
        flag_triggered,
        flagged_cols,
        all_coeffs
    )

    # Save updated diagnostics
    with open(diagnostics_file, "w") as f:
        json.dump(updated_diagnostics, f, indent=2)

    logger.info(f"Collinearity analysis complete. Updated diagnostics saved to {diagnostics_file}")
    return updated_diagnostics

if __name__ == "__main__":
    main()
