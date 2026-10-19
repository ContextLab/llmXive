"""
Top‑level driver that orchestrates the coupling‑function computation
and a thin baseline regression on Dst using only the coupling functions.
This script expects that the aligned hourly dataset already exists at
``data/processed/aligned_hourly.parquet``.
"""

import json
from pathlib import Path

import pandas as pd
import statsmodels.api as sm

from code.analysis.coupling_functions import (
    compute_all_coupling_functions,
    get_coupling_function_columns,
)
from code.utils.logging import get_logger, log_duration


logger = get_logger(__name__)


@log_duration
def main() -> None:
    """
    Execute the minimal pipeline required for Task T005:

    1. Load the aligned hourly dataset (real or synthetic) from
       ``data/processed/aligned_hourly.parquet``.
    2. Compute all coupling functions and write the enriched dataset to
       ``data/processed/with_coupling.parquet``.
    3. Fit a baseline OLS regression predicting Dst from the coupling
       function columns only.
    4. Write the regression coefficients (including intercept) to a JSON
       file ``data/artifacts/baseline_coupling_regression.json``.
    """
    aligned_path = Path("data/processed/aligned_hourly.parquet")
    if not aligned_path.is_file():
        raise FileNotFoundError(
            f"Aligned data not found at {aligned_path}. "
            "Run the alignment step before executing the main driver."
        )

    # 1. Load aligned data
    logger.info("Loading aligned hourly data from %s", aligned_path)
    df = pd.read_parquet(aligned_path)

    # 2. Compute coupling functions
    logger.info("Computing coupling functions")
    df = compute_all_coupling_functions(df)

    with_coupling_path = Path("data/processed/with_coupling.parquet")
    logger.info("Saving dataset with coupling functions to %s", with_coupling_path)
    df.to_parquet(with_coupling_path, index=False)

    # 3. Baseline regression: Dst ~ coupling functions
    required_cols = set(get_coupling_function_columns()) | {"Dst"}
    missing = required_cols - set(df.columns)
    if missing:
        raise KeyError(f"Missing columns required for regression: {missing}")

    X = df[list(get_coupling_function_columns())]
    X = sm.add_constant(X)  # add intercept
    y = df["Dst"]

    logger.info("Fitting baseline OLS regression (Dst ~ coupling functions)")
    model = sm.OLS(y, X, missing="drop").fit()

    coeffs = model.params.to_dict()
    regression_path = Path("data/artifacts/baseline_coupling_regression.json")
    logger.info("Writing regression coefficients to %s", regression_path)
    regression_path.parent.mkdir(parents=True, exist_ok=True)
    with open(regression_path, "w", encoding="utf-8") as f:
        json.dump(coeffs, f, indent=2)

    logger.info("Task T005 completed successfully.")


if __name__ == "__main__":
    main()
