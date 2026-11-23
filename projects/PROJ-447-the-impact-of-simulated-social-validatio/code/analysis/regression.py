"""
Statistical modeling and association analysis module.

This module implements multiple linear regression with confounder adjustment,
Variance Inflation Factor (VIF) calculation for multicollinearity detection,
and ensures strict associational framing of results.
"""

import os
import json
import logging
from typing import Dict, Any, Optional, Tuple, List

import pandas as pd
import numpy as np
import statsmodels.api as sm
from statsmodels.stats.outliers_influence import variance_inflation_factor

from utils.logger import get_logger, log_pipeline_step, log_model_fit_start, log_model_fit_success, log_model_fit_error
from utils.constants import get_vif_threshold, get_significance_level
from utils.exceptions import CausalLanguageViolationError
from utils.cautions import scan_report_for_causal_language

logger = get_logger(__name__)


def fit_multiple_linear_regression(
    data: pd.DataFrame,
    outcome_col: str = "self_perception_score",
    predictor_cols: List[str] = None,
    confounder_cols: List[str] = None
) -> Tuple[sm.RegressionResultsWrapper, Dict[str, Any]]:
    """
    Fit a multiple linear regression model with optional confounders.

    Args:
        data: DataFrame containing the analysis data.
        outcome_col: Name of the outcome variable column.
        predictor_cols: List of primary predictor column names.
        confounder_cols: List of confounder column names to include.

    Returns:
        Tuple containing:
            - fitted_model: The fitted statsmodels regression results object.
            - results_dict: Dictionary with coefficients, p-values, and fit statistics.
    """
    if predictor_cols is None:
        predictor_cols = ["psv_score"]
    if confounder_cols is None:
        confounder_cols = ["age", "gender", "offline_relationships", "intrinsic_traits"]

    # Construct full feature list
    feature_cols = predictor_cols + confounder_cols
    available_features = [col for col in feature_cols if col in data.columns]

    if len(available_features) == 0:
        raise ValueError("No predictor columns found in the data.")

    X = data[available_features].dropna()
    y = data[outcome_col].loc[X.index].dropna()

    # Align indices
    common_idx = X.index.intersection(y.index)
    X = X.loc[common_idx]
    y = y.loc[common_idx]

    if len(X) < 10:
        raise ValueError(f"Insufficient samples for regression after dropping NaNs: {len(X)}")

    # Add intercept
    X_with_intercept = sm.add_constant(X)

    log_model_fit_start("Multiple Linear Regression")
    model = sm.OLS(y, X_with_intercept)
    results = model.fit()
    log_model_fit_success("Multiple Linear Regression")

    # Extract results
    coef_dict = {
        col: {
            "coef": float(results.params[col]),
            "std_err": float(results.bse[col]),
            "pvalue": float(results.pvalues[col]),
            "significant": bool(results.pvalues[col] < get_significance_level())
        }
        for col in X_with_intercept.columns
    }

    results_dict = {
        "coefficients": coef_dict,
        "r_squared": float(results.rsquared),
        "adj_r_squared": float(results.rsquared_adj),
        "f_statistic": float(results.fvalue),
        "f_pvalue": float(results.f_pvalue),
        "n_obs": int(results.nobs),
        "df_resid": int(results.df_resid)
    }

    return results, results_dict


def calculate_vif(data: pd.DataFrame, feature_cols: List[str]) -> Dict[str, float]:
    """
    Calculate Variance Inflation Factor (VIF) for each predictor.

    Args:
        data: DataFrame containing the data.
        feature_cols: List of column names to calculate VIF for.

    Returns:
        Dictionary mapping column names to their VIF values.
    """
    vif_data = {}
    X = data[feature_cols].dropna()

    # Drop rows with NaNs in any feature
    X = X.dropna()

    if len(X) < len(feature_cols) + 1:
        logger.warning("Insufficient data points to calculate VIF reliably.")
        return vif_data

    # Add constant for VIF calculation
    X_const = sm.add_constant(X)

    for col in feature_cols:
        if col not in X_const.columns:
            continue
        try:
            vif = variance_inflation_factor(X_const.values, list(X_const.columns).index(col))
            vif_data[col] = float(vif)
        except Exception as e:
            logger.warning(f"Could not calculate VIF for {col}: {e}")
            vif_data[col] = float('nan')

    return vif_data


def check_vif_results(vif_results: Dict[str, float], threshold: Optional[float] = None) -> Dict[str, Any]:
    """
    Compare VIF results against a threshold and determine pass/fail status.

    Args:
        vif_results: Dictionary of VIF values per feature.
        threshold: VIF threshold value (defaults to config).

    Returns:
        Dictionary with comparison results.
    """
    if threshold is None:
        threshold = get_vif_threshold()

    status = "PASS"
    violations = []

    for col, vif_val in vif_results.items():
        if np.isnan(vif_val):
            continue
        if vif_val > threshold:
            status = "FAIL"
            violations.append({"feature": col, "vif": vif_val, "threshold": threshold})

    return {
        "threshold": threshold,
        "overall_status": status,
        "violations": violations,
        "vif_values": vif_results
    }


def generate_associational_report(
    results_dict: Dict[str, Any],
    model_type: str = "Multiple Linear Regression"
) -> str:
    """
    Generate a report string ensuring strictly associational language.

    Args:
        results_dict: Dictionary containing model results.
        model_type: Type of model used.

    Returns:
        Formatted report string.

    Raises:
        CausalLanguageViolationError: If causal language is detected.
    """
    report_lines = [
        f"=== {model_type} Results ===",
        f"R-squared: {results_dict['r_squared']:.4f}",
        f"Adjusted R-squared: {results_dict['adj_r_squared']:.4f}",
        f"F-statistic: {results_dict['f_statistic']:.4f} (p={results_dict['f_pvalue']:.4f})",
        f"Observations: {results_dict['n_obs']}",
        "",
        "Coefficients:"
    ]

    for feature, stats in results_dict['coefficients'].items():
        sig_marker = "*" if stats['significant'] else ""
        report_lines.append(
            f"  {feature}: coef={stats['coef']:.4f}, p={stats['pvalue']:.4f} {sig_marker}"
        )

    report_text = "\n".join(report_lines)

    # Check for causal language
    trigger_words = scan_report_for_causal_language(report_text)
    if trigger_words:
        raise CausalLanguageViolationError(
            f"Causal language detected in report: {trigger_words}. "
            "All findings must be framed associationally."
        )

    return report_text


def run_analysis(
    data: pd.DataFrame,
    outcome_col: str = "self_perception_score",
    predictor_cols: List[str] = None,
    confounder_cols: List[str] = None,
    output_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Run the full regression analysis pipeline including VIF and reporting.

    Args:
        data: DataFrame containing the analysis data.
        outcome_col: Name of the outcome variable column.
        predictor_cols: List of primary predictor column names.
        confounder_cols: List of confounder column names.
        output_path: Optional path to save results JSON.

    Returns:
        Dictionary containing all analysis results.
    """
    log_pipeline_step("Starting regression analysis")

    try:
        # Fit model
        _, model_results = fit_multiple_linear_regression(
            data, outcome_col, predictor_cols, confounder_cols
        )

        # Calculate VIF
        feature_cols = (predictor_cols or ["psv_score"]) + (confounder_cols or [])
        vif_values = calculate_vif(data, feature_cols)
        vif_comparison = check_vif_results(vif_values)

        # Generate report (validates language)
        report = generate_associational_report(model_results)

        # Compile results
        full_results = {
            "model_results": model_results,
            "vif_results": vif_comparison,
            "report": report
        }

        if output_path:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(full_results, f, indent=2)
            logger.info(f"Regression results saved to {output_path}")

        log_pipeline_step("Regression analysis completed successfully")
        return full_results

    except Exception as e:
        log_model_fit_error("Regression analysis", str(e))
        logger.error(f"Regression analysis failed: {e}", exc_info=True)
        raise


def main() -> None:
    """
    Main entry point for the regression analysis module.
    Loads processed data, runs analysis, and saves results.
    """
    logger.info("Executing main() for regression analysis")

    from pathlib import Path
    base_dir = Path(__file__).resolve().parents[2]
    data_path = base_dir / "data" / "processed" / "pipeline_data.csv"
    output_path = base_dir / "data" / "processed" / "model_results.json"

    if not data_path.exists():
        logger.error(f"Data file not found: {data_path}. Cannot run analysis.")
        return

    logger.info(f"Loading data from {data_path}")
    data = pd.read_csv(data_path)

    run_analysis(
        data,
        outcome_col="self_perception_score",
        predictor_cols=["psv_score"],
        confounder_cols=["age", "gender", "offline_relationships", "intrinsic_traits"],
        output_path=str(output_path)
    )


if __name__ == "__main__":
    main()
