"""
Thin modeling step for T003.

This script fits a simple Linear Mixed‑Effects Model (LMM) on the
``user_track_pairs.parquet`` dataset produced by the aggregation step.
The model is:

    mean_vividness ~ adolescent_exposure_score + popularity + (1 | user_id)

The results are written to ``data/final/regression_summary.csv`` with the
columns required by the output contract:
    term, estimate, std_error, t_value, p_value, vif
"""

import logging
from pathlib import Path

import pandas as pd
import numpy as np
import statsmodels.api as sm
from statsmodels.regression.mixed_linear_model import MixedLM
from statsmodels.stats.outliers_influence import variance_inflation_factor

from config import get_project_root
from utils import get_logger, write_parquet

logger = get_logger(__name__)

def _fit_lmm(df: pd.DataFrame) -> MixedLM:
    """
    Fit the mixed‑effects model.

    Args:
        df: DataFrame containing the analysis variables.

    Returns:
        Fitted MixedLMResults object.
    """
    # Endogenous variable
    endog = df["mean_vividness"].astype(float)

    # Exogenous variables (add constant for intercept)
    exog = sm.add_constant(
        df[["adolescent_exposure_score", "popularity"]].astype(float)
    )

    # Grouping variable for random intercepts
    groups = df["user_id"]

    model = MixedLM(endog, exog, groups=groups)
    result = model.fit(reml=False)  # Use ML for easier statistic extraction
    return result

def _calculate_vif(df: pd.DataFrame) -> pd.Series:
    """
    Compute VIF for the fixed‑effects predictors (excluding the intercept).

    Args:
        df: DataFrame with the same columns used in the model.

    Returns:
        Series mapping predictor name -> VIF value.
    """
    X = df[["adolescent_exposure_score", "popularity"]].astype(float)
    X = sm.add_constant(X)
    vif_data = {}
    for i, col in enumerate(X.columns):
        if col == "const":
            vif_data[col] = np.nan
            continue
        vif = variance_inflation_factor(X.values, i)
        vif_data[col] = vif
    return pd.Series(vif_data)

def main() -> None:
    """
    Load the user‑track pair data, fit the LMM, compute VIF, and write the
    regression summary CSV.
    """
    root = get_project_root()
    input_path = root / "data" / "processed" / "user_track_pairs.parquet"
    output_path = root / "data" / "final" / "regression_summary.csv"

    logger.info(f"Loading user‑track pair data from {input_path}")
    df = pd.read_parquet(input_path)

    # Fit the model
    logger.info("Fitting Linear Mixed‑Effects Model")
    result = _fit_lmm(df)

    # Extract fixed‑effects summary
    params = result.params
    bse = result.bse
    tvalues = result.tvalues
    pvalues = result.pvalues

    # Compute VIF for predictors
    logger.info("Calculating VIF for fixed effects")
    vif_series = _calculate_vif(df)

    # Build the summary DataFrame
    summary_rows = []
    for term in params.index:
        summary_rows.append(
            {
                "term": term,
                "estimate": params[term],
                "std_error": bse[term],
                "t_value": tvalues[term],
                "p_value": pvalues[term],
                "vif": vif_series.get(term, np.nan),
            }
        )
    summary_df = pd.DataFrame(summary_rows)

    # Ensure column order matches contract
    summary_df = summary_df[
        ["term", "estimate", "std_error", "t_value", "p_value", "vif"]
    ]

    # Write CSV
    output_path.parent.mkdir(parents=True, exist_ok=True)
    summary_df.to_csv(output_path, index=False)
    logger.info(f"Regression summary written to {output_path}")

if __name__ == "__main__":
    main()
