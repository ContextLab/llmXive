"""
Robustness and sensitivity analysis module.

This module re-runs regression analyses under varying conditions (outlier removal,
confounder inclusion/exclusion) to assess the stability of the primary coefficient.
"""

import os
import json
import logging
from typing import Dict, Any, List, Tuple, Optional

import pandas as pd
import numpy as np
import statsmodels.api as sm

from utils.logger import get_logger, log_pipeline_step
from utils.constants import get_stability_threshold, get_significance_level
from utils.exceptions import StabilityThresholdViolationError
from .regression import fit_multiple_linear_regression, calculate_vif, check_vif_results

logger = get_logger(__name__)


def remove_outliers_iqr(data: pd.DataFrame, column: str, multiplier: float = 1.5) -> pd.DataFrame:
    """
    Remove outliers based on the Interquartile Range (IQR) method.

    Args:
        data: Input DataFrame.
        column: Column name to check for outliers.
        multiplier: IQR multiplier for outlier bounds (default 1.5).

    Returns:
        DataFrame with outliers removed.
    """
    Q1 = data[column].quantile(0.25)
    Q3 = data[column].quantile(0.75)
    IQR = Q3 - Q1
    lower_bound = Q1 - (multiplier * IQR)
    upper_bound = Q3 + (multiplier * IQR)

    mask = (data[column] >= lower_bound) & (data[column] <= upper_bound)
    return data[mask].copy()


def winsorize_data(
    data: pd.DataFrame,
    column: str,
    limits: Tuple[float, float] = (0.05, 0.95)
) -> pd.DataFrame:
    """
    Winsorize a column by limiting extreme values.

    Args:
        data: Input DataFrame.
        column: Column name to winsorize.
        limits: Tuple of (lower_percentile, upper_percentile).

    Returns:
        DataFrame with winsorized column.
    """
    lower_limit = data[column].quantile(limits[0])
    upper_limit = data[column].quantile(limits[1])

    df_winsorized = data.copy()
    df_winsorized[column] = df_winsorized[column].clip(lower=lower_limit, upper=upper_limit)
    return df_winsorized


def run_single_regression(
    data: pd.DataFrame,
    outcome_col: str,
    predictor_col: str,
    confounder_cols: List[str],
    strategy_name: str
) -> Dict[str, Any]:
    """
    Run a single regression with specific data modifications.

    Args:
        data: Input DataFrame.
        outcome_col: Outcome variable column name.
        predictor_col: Primary predictor column name.
        confounder_cols: List of confounder column names.
        strategy_name: Name of the strategy applied.

    Returns:
        Dictionary with regression results.
    """
    try:
        _, results = fit_multiple_linear_regression(
            data, outcome_col, [predictor_col], confounder_cols
        )

        primary_coef = results['coefficients'][predictor_col]['coef']
        primary_pval = results['coefficients'][predictor_col]['pvalue']

        return {
            "strategy": strategy_name,
            "coefficient": float(primary_coef),
            "p_value": float(primary_pval),
            "significant": bool(primary_pval < get_significance_level()),
            "n_obs": results['n_obs']
        }
    except Exception as e:
        logger.warning(f"Strategy {strategy_name} failed: {e}")
        return {
            "strategy": strategy_name,
            "coefficient": None,
            "p_value": None,
            "significant": None,
            "n_obs": 0,
            "error": str(e)
        }


def run_sensitivity_analysis(
    data: pd.DataFrame,
    outcome_col: str = "self_perception_score",
    predictor_col: str = "psv_score",
    confounder_cols: List[str] = None,
    outlier_strategies: List[str] = None,
    output_path: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Run full sensitivity analysis across outlier strategies and confounder states.

    Args:
        data: Input DataFrame.
        outcome_col: Outcome variable column name.
        predictor_col: Primary predictor column name.
        confounder_cols: List of confounder column names.
        outlier_strategies: List of outlier strategies ('none', 'iqr', 'winsorize').
        output_path: Optional path to save results JSON.

    Returns:
        List of dictionaries containing results for each strategy.
    """
    if confounder_cols is None:
        confounder_cols = ["age", "gender", "offline_relationships", "intrinsic_traits"]
    if outlier_strategies is None:
        outlier_strategies = ["none", "iqr", "winsorize"]

    log_pipeline_step("Starting sensitivity analysis")
    results_list = []

    # Define the 3x2 matrix of runs
    strategies = []

    for outlier_strategy in outlier_strategies:
        # State 1: With confounders
        strategies.append({
            "name": f"{outlier_strategy}_with_confounders",
            "data": data,
            "outlier_method": outlier_strategy,
            "include_confounders": True
        })
        # State 2: Without confounders
        strategies.append({
            "name": f"{outlier_strategy}_without_confounders",
            "data": data,
            "outlier_method": outlier_strategy,
            "include_confounders": False
        })

    for strat in strategies:
        current_data = strat["data"]

        # Apply outlier method
        if strat["outlier_method"] == "iqr":
            current_data = remove_outliers_iqr(current_data, predictor_col)
            strat_name = strat["name"]
        elif strat["outlier_method"] == "winsorize":
            current_data = winsorize_data(current_data, predictor_col)
            strat_name = strat["name"]
        else:
            strat_name = strat["name"]

        # Determine confounders
        active_confounders = confounder_cols if strat["include_confounders"] else []

        # Run regression
        result = run_single_regression(
            current_data, outcome_col, predictor_col, active_confounders, strat_name
        )
        results_list.append(result)

    # Save results
    if output_path:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results_list, f, indent=2)
        logger.info(f"Sensitivity analysis results saved to {output_path}")

    log_pipeline_step("Sensitivity analysis completed")
    return results_list


def check_stability(
    results: List[Dict[str, Any]],
    threshold: Optional[float] = None
) -> Dict[str, Any]:
    """
    Check if coefficient variation exceeds the stability threshold.

    Args:
        results: List of sensitivity analysis results.
        threshold: Stability threshold (defaults to config).

    Returns:
        Dictionary with stability check results.
    """
    if threshold is None:
        threshold = get_stability_threshold()

    # Filter valid coefficients
    valid_coefs = [r['coefficient'] for r in results if r['coefficient'] is not None]

    if len(valid_coefs) < 2:
        logger.warning("Insufficient valid results to check stability.")
        return {"status": "UNKNOWN", "reason": "Insufficient valid results"}

    max_coef = max(valid_coefs)
    min_coef = min(valid_coefs)
    variation = max_coef - min_coef

    # Calculate relative variation if mean is non-zero
    mean_coef = np.mean(valid_coefs)
    if abs(mean_coef) > 1e-6:
        relative_variation = abs(variation / mean_coef)
    else:
        relative_variation = variation

    status = "PASS" if relative_variation <= threshold else "FAIL"

    check_result = {
        "threshold": threshold,
        "variation": float(variation),
        "relative_variation": float(relative_variation),
        "max_coef": float(max_coef),
        "min_coef": float(min_coef),
        "status": status
    }

    if status == "FAIL":
        raise StabilityThresholdViolationError(
            f"Coefficient variation ({relative_variation:.4f}) exceeds threshold ({threshold}). "
            "Results are not stable."
        )

    return check_result


def main() -> None:
    """
    Main entry point for the sensitivity analysis module.
    """
    logger.info("Executing main() for sensitivity analysis")

    from pathlib import Path
    base_dir = Path(__file__).resolve().parents[2]
    data_path = base_dir / "data" / "processed" / "pipeline_data.csv"
    output_path = base_dir / "data" / "processed" / "sensitivity_analysis.json"

    if not data_path.exists():
        logger.error(f"Data file not found: {data_path}. Cannot run analysis.")
        return

    logger.info(f"Loading data from {data_path}")
    data = pd.read_csv(data_path)

    results = run_sensitivity_analysis(
        data,
        outcome_col="self_perception_score",
        predictor_col="psv_score",
        confounder_cols=["age", "gender", "offline_relationships", "intrinsic_traits"],
        output_path=str(output_path)
    )

    # Check stability
    try:
        stability_check = check_stability(results)
        logger.info(f"Stability check result: {stability_check['status']}")
    except StabilityThresholdViolationError as e:
        logger.error(f"Stability threshold violated: {e}")
        raise


if __name__ == "__main__":
    main()
