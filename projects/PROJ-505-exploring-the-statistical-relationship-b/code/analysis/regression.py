import os
import sys
import json
import warnings
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List

import pandas as pd
import numpy as np
from statsmodels.formula.api import ols
from statsmodels.stats.outliers_influence import variance_inflation_factor

from utils.logging import AnalysisError, get_logger
from config import get_config


def _validate_data(df: pd.DataFrame, required_cols: List[str], target_col: str) -> None:
    """Validate that the dataframe contains all required columns and the target."""
    missing = set(required_cols + [target_col]) - set(df.columns)
    if missing:
        raise AnalysisError(f"Missing required columns: {missing}")


def _build_formula(target: str, predictors: List[str]) -> str:
    """Construct the regression formula string."""
    return f"{target} ~ " + " + ".join(predictors)


def _calculate_vif(model, predictors: List[str]) -> pd.DataFrame:
    """Calculate Variance Inflation Factor for each predictor."""
    vif_data = pd.DataFrame()
    vif_data["feature"] = predictors
    vif_data["VIF"] = [
        variance_inflation_factor(model.model.exog, i + 1)
        for i in range(len(predictors))
    ]
    return vif_data


def _fit_model(target: str, predictors: List[str], df: pd.DataFrame) -> Any:
    """Fit an OLS model and return the result."""
    formula = _build_formula(target, predictors)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        return ols(formula, data=df).fit()


def _extract_metrics(
    target: str,
    baseline_model: Any,
    full_model: Any,
    vif_data: pd.DataFrame,
    logger: Any,
) -> Dict[str, Any]:
    """Extract regression metrics and VIF warnings."""
    high_vif = vif_data[vif_data["VIF"] >= 5]
    if not high_vif.empty:
        logger.warning(f"High VIF detected for {target}: {high_vif.to_dict()}")

    return {
        "baseline_r2": float(baseline_model.rsquared),
        "full_r2": float(full_model.rsquared),
        "delta_r2": float(full_model.rsquared - baseline_model.rsquared),
        "coefficients": full_model.params.to_dict(),
        "p_values": full_model.pvalues.to_dict(),
        "vif": high_vif.to_dict(),
    }


def run_regression_analysis(data_path: Path, output_path: Path) -> Dict[str, Any]:
    """
    Run regression analysis for Dst and Kp against coupling functions
    and composition ratios.
    """
    logger = get_logger()
    cfg = get_config()

    # Load data
    if not data_path.exists():
        raise AnalysisError(f"Input data file not found: {data_path}")
    df = pd.read_csv(data_path, parse_dates=["timestamp"])

    # Configuration
    composition_cols = ["O_Fe", "He_H", "C_O"]
    coupling_cols = ["epsilon", "newell", "v_bs", "v_bt"]
    targets = ["Dst", "Kp"]
    all_predictors = coupling_cols + composition_cols

    results = {}

    for target in targets:
        if target not in df.columns:
            logger.warning(f"Target {target} not found in data.")
            continue

        # Validate data
        _validate_data(df, all_predictors, target)

        # Fit baseline model
        baseline_model = _fit_model(target, coupling_cols, df)

        # Fit full model
        full_model = _fit_model(target, all_predictors, df)

        # Calculate VIF
        vif_data = _calculate_vif(full_model, all_predictors)

        # Extract and store metrics
        results[target] = _extract_metrics(
            target, baseline_model, full_model, vif_data, logger
        )

    # Save results
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2, default=str)

    logger.info(f"Regression results saved to {output_path}")
    return results


def get_coupling_function_columns() -> List[str]:
    """Return the list of coupling function column names."""
    return ["epsilon", "newell", "v_bs", "v_bt"]


def main() -> None:
    """Entry point for regression analysis."""
    logger = get_logger()
    cfg = get_config()
    input_path = cfg["data_processed"] / "aligned_data.csv"
    output_path = cfg["data_artifacts"] / "regression_results.json"
    run_regression_analysis(input_path, output_path)


if __name__ == "__main__":
    main()