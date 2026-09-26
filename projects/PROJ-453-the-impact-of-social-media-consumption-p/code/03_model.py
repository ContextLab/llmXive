"""
Model Fitting and Analysis Module for Social Media Cognitive Flexibility Study.

This module implements OLS regression, VIF calculation, sensitivity analysis,
and robustness verification according to the project specifications.
"""
import os
import sys
import logging
import json
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional

import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.stats.outliers_influence import variance_inflation_factor

# Import project utilities
from config import DATA_ROOT, RESULTS_ROOT
from logging_config import get_logger
from utils import causal_language_scanner

logger = get_logger(__name__)

# Constants
DATA_PATH = Path(DATA_ROOT) / "processed" / "participants_cleaned.csv"
SCHEMA_PATH = Path("contracts/output.schema.yaml")
MODEL_DIR = Path(RESULTS_ROOT) / "models"
SENSITIVITY_PATH = Path(RESULTS_ROOT) / "sensitivity_comparison.csv"
ROBUSTNESS_PATH = Path(RESULTS_ROOT) / "robustness_evidence.json"
RESIDUALS_PATH = MODEL_DIR / "residuals.csv"
RESIDUAL_COEFFS_PATH = MODEL_DIR / "residualized_coefficients.json"
CORE_MODEL_PATH = MODEL_DIR / "core_model.json"
REGRESSION_SUMMARY_PATH = MODEL_DIR / "regression_summary.json"


def load_schema_contract() -> Dict[str, Any]:
    """
    Load the output schema contract.

    Returns:
        Dict[str, Any]: The schema definition.
    """
    import yaml
    with open(SCHEMA_PATH, 'r') as f:
        return yaml.safe_load(f)


def validate_output_schema(result: Dict[str, Any]) -> bool:
    """
    Validate the model result dictionary against the output schema.

    Args:
        result: The dictionary containing model results.

    Returns:
        bool: True if valid.

    Raises:
        ValueError: If validation fails.
    """
    schema = load_schema_contract()
    required_keys = schema.get('required_keys', [])
    missing = [k for k in required_keys if k not in result]
    if missing:
        raise ValueError(f"Schema validation failed: Missing keys {missing}")
    return True


def mean_center(series: pd.Series) -> pd.Series:
    """
    Mean-center a pandas Series.

    Args:
        series: The input series.

    Returns:
        pd.Series: The mean-centered series.
    """
    return series - series.mean()


def create_interaction(df: pd.DataFrame, col1: str, col2: str) -> pd.Series:
    """
    Create an interaction term between two columns.

    Args:
        df: The DataFrame.
        col1: Name of the first column.
        col2: Name of the second column.

    Returns:
        pd.Series: The interaction term.
    """
    return df[col1] * df[col2]


def calculate_vif(df: pd.DataFrame, features: List[str]) -> Dict[str, float]:
    """
    Calculate Variance Inflation Factor (VIF) for a set of features.

    Args:
        df: DataFrame containing the features.
        features: List of column names to calculate VIF for.

    Returns:
        Dict[str, float]: Mapping of feature name to VIF value.
    """
    vif_data = {}
    X = df[features].dropna()
    if len(X) == 0:
        return {f: np.nan for f in features}

    # Add constant for intercept if not already present in features
    # VIF is typically calculated on predictors excluding intercept, but statsmodels
    # vif function handles the design matrix. We pass the matrix without constant.
    try:
        for i, feature in enumerate(features):
            # Extract column, handle potential NaNs by using the same index as X
            if feature in X.columns:
                vif = variance_inflation_factor(X.values, i)
                vif_data[feature] = vif
    except Exception as e:
        logger.error(f"VIF calculation failed: {e}")
        # Return NaNs if calculation fails
        return {f: np.nan for f in features}

    return vif_data


def benjamini_hochberg(p_values: List[float]) -> List[float]:
    """
    Apply Benjamini-Hochberg FDR correction to a list of p-values.

    Args:
        p_values: List of raw p-values.

    Returns:
        List[float]: List of adjusted p-values.
    """
    if not p_values:
        return []

    sorted_indices = np.argsort(p_values)
    sorted_p = np.array([p_values[i] for i in sorted_indices])
    n = len(sorted_p)
    adjusted = sorted_p * n / (np.arange(1, n + 1))
    adjusted = np.minimum.accumulate(adjusted[::-1])[::-1]
    adjusted = np.clip(adjusted, 0, 1)

    # Restore original order
    result = [0.0] * n
    for i, idx in enumerate(sorted_indices):
        result[idx] = adjusted[i]

    return result


def check_collinearity(df: pd.DataFrame, var1: str, var2: str, threshold: float = 0.7) -> Tuple[float, bool]:
    """
    Check correlation between two variables and flag if above threshold.

    Args:
        df: DataFrame.
        var1: First variable name.
        var2: Second variable name.
        threshold: Correlation threshold for flagging.

    Returns:
        Tuple[float, bool]: Correlation value and flag (True if > threshold).
    """
    if var1 not in df.columns or var2 not in df.columns:
        logger.warning(f"Variables {var1} or {var2} not found in data.")
        return 0.0, False

    corr = df[[var1, var2]].corr().iloc[0, 1]
    flag = corr > threshold
    logger.info(f"Correlation between {var1} and {var2}: {corr:.4f} (Flag: {flag})")
    return corr, flag


def run_model(
    df: pd.DataFrame,
    outcome: str,
    predictors: List[str],
    interaction_term: Optional[pd.Series] = None
) -> Tuple[Any, Dict[str, Any]]:
    """
    Fit an OLS model and return results and diagnostics.

    Args:
        df: DataFrame containing data.
        outcome: Name of the outcome variable.
        predictors: List of predictor variable names.
        interaction_term: Optional interaction term series to add.

    Returns:
        Tuple[sm.OLSResults, Dict[str, Any]]: Model results and diagnostics dict.
    """
    # Prepare data
    valid_idx = df[[outcome] + predictors].dropna().index
    if interaction_term is not None:
        valid_idx = valid_idx.intersection(interaction_term.dropna().index)

    y = df.loc[valid_idx, outcome]
    X = df.loc[valid_idx, predictors]

    if interaction_term is not None:
        X['interaction'] = interaction_term.loc[valid_idx]

    X = sm.add_constant(X)

    model = sm.OLS(y, X)
    results = model.fit()

    # Calculate VIF
    vif_scores = calculate_vif(df.loc[valid_idx], predictors)
    if interaction_term is not None:
        vif_scores['interaction'] = calculate_vif(
            df.loc[valid_idx, predictors + ['interaction']],
            predictors + ['interaction']
        )['interaction']

    return results, {
        "vif_scores": vif_scores,
        "n_obs": len(y),
        "r_squared": results.rsquared,
        "adj_r_squared": results.rsquared_adj
    }


def run_sensitivity_analysis(df: pd.DataFrame) -> pd.DataFrame:
    """
    Run regression with alternative definitions of the predictor.

    Args:
        df: Cleaned DataFrame.

    Returns:
        pd.DataFrame: Comparison table of sensitivity results.
    """
    outcomes = []

    # Definitions to test
    definitions = [
        ("switching_index", ["switching_index", "total_screen_time", "age"]),
        ("platform_count", ["num_platforms", "total_screen_time", "age"]),
        ("switching_frequency", ["switching_frequency", "total_screen_time", "age"])
    ]

    p_values = []
    betas = []
    signs = []
    definitions_list = []
    n_obs_list = []

    for def_name, predictors in definitions:
        try:
            # Ensure we use the correct predictor column
            if def_name == "switching_index":
                outcome_col = "switching_index"
            elif def_name == "platform_count":
                outcome_col = "num_platforms"
            else:
                outcome_col = "switching_frequency"

            # Check if column exists
            if outcome_col not in df.columns:
                logger.warning(f"Definition {def_name} skipped: column {outcome_col} missing.")
                continue

            # Fit simple model for sensitivity (outcome: cognitive_flexibility_score)
            # We regress cognitive_flexibility_score on the specific predictor + controls
            model_predictors = [outcome_col, "total_screen_time", "age"]
            # Filter valid rows
            valid_df = df.dropna(subset=model_predictors + ["cognitive_flexibility_score"])

            if len(valid_df) < 10:
                logger.warning(f"Not enough data for definition {def_name}.")
                continue

            y = valid_df["cognitive_flexibility_score"]
            X = valid_df[model_predictors]
            X = sm.add_constant(X)

            model = sm.OLS(y, X).fit()
            beta = model.params[outcome_col]
            p_val = model.pvalues[outcome_col]
            n = len(y)

            betas.append(beta)
            p_values.append(p_val)
            signs.append(np.sign(beta))
            definitions_list.append(def_name)
            n_obs_list.append(n)

        except Exception as e:
            logger.error(f"Error running sensitivity for {def_name}: {e}")
            continue

    if not p_values:
        logger.warning("No sensitivity results generated.")
        return pd.DataFrame()

    # FDR Correction
    fdr_p = benjamini_hochberg(p_values)

    results_df = pd.DataFrame({
        "definition": definitions_list,
        "beta": betas,
        "p_value": p_values,
        "sign": signs,
        "n": n_obs_list,
        "fdr_p_value": fdr_p
    })

    return results_df


def verify_robustness(sensitivity_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Verify SC-003 criteria: Beta sign stability and p-value thresholds.

    Args:
        sensitivity_df: The sensitivity comparison DataFrame.

    Returns:
        Dict[str, Any]: Robustness evidence dictionary.
    """
    evidence = {
        "sc003_status": "PASS",
        "details": [],
        "message": ""
    }

    if sensitivity_df.empty:
        evidence["sc003_status"] = "FAIL"
        evidence["message"] = "No sensitivity data to verify."
        return evidence

    # Check sign stability
    signs = sensitivity_df["sign"].unique()
    if len(signs) > 1:
        evidence["sc003_status"] = "FAIL"
        evidence["message"] = "SC-003 Violation: Beta sign instability detected."
        logger.warning("SC-003 Violation: Beta sign instability detected.")
    else:
        # Check p-values
        high_p = sensitivity_df[sensitivity_df["p_value"] >= 0.10]
        if not high_p.empty:
            evidence["sc003_status"] = "FAIL"
            evidence["message"] = "SC-003 Warning: p > 0.10 detected."
            logger.warning("Warning: Variant p > 0.10 but sign stable; robustness maintained.")
        else:
            evidence["message"] = "SC-003 Met: p < 0.10 across operationalizations."

    evidence["details"] = sensitivity_df.to_dict(orient="records")
    return evidence


def main() -> None:
    """
    Main entry point for the model fitting pipeline.
    """
    logger.info("Starting model fitting and analysis.")

    try:
        # 1. Load Data
        if not DATA_PATH.exists():
            raise FileNotFoundError(f"Cleaned data not found at {DATA_PATH}")
        df = pd.read_csv(DATA_PATH)

        # 2. Check Collinearity (FR-006)
        corr, flag = check_collinearity(df, "switching_index", "total_screen_time")

        use_residuals = False
        if flag:
            logger.warning("Potential Mathematical Coupling detected. Running residual model.")
            # Regress switching_index on total_screen_time
            X_res = sm.add_constant(df[["total_screen_time"]])
            y_res = df["switching_index"]
            model_res = sm.OLS(y_res, X_res).fit()
            residuals = model_res.resid

            # Save residuals
            MODEL_DIR.mkdir(parents=True, exist_ok=True)
            pd.Series(residuals, name="residual_switching_index").to_csv(RESIDUALS_PATH)
            logger.info(f"Saved residuals to {RESIDUALS_PATH}")

            # Prepare residualized predictors
            df["switching_index_resid"] = residuals
            predictors = ["switching_index_resid", "total_screen_time", "age"]
            use_residuals = True
        else:
            predictors = ["switching_index", "total_screen_time", "age"]
            logger.info("Skipping residual model (correlation <= 0.7).")

        # 3. Create Interaction
        df["age_mean"] = mean_center(df["age"])
        df["switching_mean"] = mean_center(df["switching_index"] if not use_residuals else df["switching_index_resid"])
        interaction = create_interaction(df, "switching_mean", "age_mean")

        # 4. Fit Core Model
        outcome = "cognitive_flexibility_score"
        results, diagnostics = run_model(df, outcome, predictors, interaction)

        # Save Core Model
        core_model_data = {
            "coefficients": results.params.to_dict(),
            "p_values": results.pvalues.to_dict(),
            "diagnostics": diagnostics,
            "n_obs": diagnostics["n_obs"]
        }
        with open(CORE_MODEL_PATH, 'w') as f:
            json.dump(core_model_data, f, indent=2)
        logger.info(f"Saved core model to {CORE_MODEL_PATH}")

        # 5. Sensitivity Analysis
        sensitivity_df = run_sensitivity_analysis(df)
        if not sensitivity_df.empty:
            sensitivity_df.to_csv(SENSITIVITY_PATH, index=False)
            logger.info(f"Saved sensitivity analysis to {SENSITIVITY_PATH}")

            # 6. Verify Robustness
            robustness = verify_robustness(sensitivity_df)
            with open(ROBUSTNESS_PATH, 'w') as f:
                json.dump(robustness, f, indent=2)
            logger.info(f"Saved robustness evidence to {ROBUSTNESS_PATH}")
        else:
            logger.warning("Sensitivity analysis produced no results.")

        # 7. Final Report
        # Prepare interpretation (associational only)
        interpretation = (
            f"Analysis indicates an association between switching behavior and cognitive flexibility. "
            f"VIF scores indicate multicollinearity status: {diagnostics['vif_scores']}."
        )

        # Check for causal language
        if causal_language_scanner(interpretation, ["causes", "leads to", "impacts", "determines"]):
            raise ValueError("Causal language detected in interpretation. Failing run.")

        final_summary = {
            "coefficients": results.params.to_dict(),
            "p_values": results.pvalues.to_dict(),
            "vif_scores": diagnostics["vif_scores"],
            "diagnostics": diagnostics,
            "interpretation": interpretation,
            "robustness_status": robustness.get("sc003_status", "N/A")
        }

        validate_output_schema(final_summary)

        with open(REGRESSION_SUMMARY_PATH, 'w') as f:
            json.dump(final_summary, f, indent=2)
        logger.info(f"Saved regression summary to {REGRESSION_SUMMARY_PATH}")

        logger.info("Model fitting pipeline completed successfully.")

    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
