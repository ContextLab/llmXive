"""
Non-linearity analysis module for detecting quadratic effects in social validation data.

This module fits quadratic regression models to determine if the relationship between
Perceived Social Validation (PSV) and Self-Perception is non-linear.
"""

import os
import json
import logging
from typing import Dict, Any, Optional, Tuple

import pandas as pd
import numpy as np
import statsmodels.api as sm

from utils.logger import get_logger, log_pipeline_step
from utils.constants import get_significance_level

logger = get_logger(__name__)


def fit_quadratic_model(
    data: pd.DataFrame,
    outcome_col: str = "self_perception_score",
    predictor_col: str = "psv_score"
) -> Tuple[sm.RegressionResultsWrapper, Dict[str, Any]]:
    """
    Fit a quadratic regression model: Y = β0 + β1*X + β2*X^2 + ε

    Args:
        data: DataFrame containing the analysis data.
        outcome_col: Name of the outcome variable column.
        predictor_col: Name of the primary predictor variable column.

    Returns:
        Tuple containing:
            - fitted_model: The fitted statsmodels regression results object.
            - results_dict: Dictionary with coefficients, p-values, and significance status.
    """
    if predictor_col not in data.columns or outcome_col not in data.columns:
        raise ValueError(f"Columns '{predictor_col}' or '{outcome_col}' not found in data.")

    X = data[predictor_col].dropna()
    y = data[outcome_col].loc[X.index].dropna()

    if len(X) == 0:
        raise ValueError("No valid data points after dropping NaNs for quadratic fit.")

    # Create squared term
    X_squared = X ** 2
    X_matrix = pd.DataFrame({
        'intercept': 1,
        'X': X,
        'X_sq': X_squared
    })

    model = sm.OLS(y, X_matrix)
    results = model.fit()

    coef_x = results.params['X']
    coef_x_sq = results.params['X_sq']
    pval_x = results.pvalues['X']
    pval_x_sq = results.pvalues['X_sq']
    sig_level = get_significance_level()

    results_dict = {
        "coefficients": {
            "intercept": float(results.params['intercept']),
            "linear_term": float(coef_x),
            "quadratic_term": float(coef_x_sq)
        },
        "p_values": {
            "linear_term": float(pval_x),
            "quadratic_term": float(pval_x_sq)
        },
        "is_quadratic_significant": bool(pval_x_sq < sig_level),
        "r_squared": float(results.rsquared),
        "adj_r_squared": float(results.rsquared_adj)
    }

    logger.info(f"Quadratic model fit complete. Quadratic term p-value: {pval_x_sq:.4f}")
    return results, results_dict


def run_nonlinearity_analysis(
    data: pd.DataFrame,
    outcome_col: str = "self_perception_score",
    predictor_col: str = "psv_score",
    output_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Run the full non-linearity analysis pipeline.

    Args:
        data: DataFrame containing the analysis data.
        outcome_col: Name of the outcome variable column.
        predictor_col: Name of the primary predictor variable column.
        output_path: Optional path to save the results JSON file.

    Returns:
        Dictionary containing the analysis results.
    """
    log_pipeline_step("Starting non-linearity analysis")

    try:
        results_obj, results_dict = fit_quadratic_model(
            data, outcome_col, predictor_col
        )

        if output_path:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(results_dict, f, indent=2)
            logger.info(f"Non-linearity results saved to {output_path}")

        log_pipeline_step("Non-linearity analysis completed successfully")
        return results_dict

    except Exception as e:
        logger.error(f"Non-linearity analysis failed: {e}", exc_info=True)
        raise


def main() -> None:
    """
    Main entry point for the non-linearity analysis module.
    Loads processed data, runs analysis, and saves results.
    """
    logger.info("Executing main() for nonlinearity analysis")

    # Determine paths relative to project root
    base_dir = Path(__file__).resolve().parents[2]
    data_path = base_dir / "data" / "processed" / "pipeline_data.csv"
    output_path = base_dir / "data" / "processed" / "nonlinearity_results.json"

    if not data_path.exists():
        logger.error(f"Data file not found: {data_path}. Cannot run analysis.")
        return

    logger.info(f"Loading data from {data_path}")
    data = pd.read_csv(data_path)

    run_nonlinearity_analysis(
        data,
        outcome_col="self_perception_score",
        predictor_col="psv_score",
        output_path=str(output_path)
    )


if __name__ == "__main__":
    main()
