"""
Statistical analysis utilities.

This module currently implements the functions required by the unit
tests for linear regression with mass control and a thin wrapper that
runs the regression on a collection of chunked CSV files.
"""

import os
from pathlib import Path
from typing import List

import numpy as np
import pandas as pd
import statsmodels.api as sm

def linear_regression_with_mass_control(
    data: pd.DataFrame, outcome: str = "sfr"
) -> pd.DataFrame:
    """
    Perform OLS regression of a galaxy property on shape parameters while
    controlling for halo mass.

    The model is:
        outcome ~ triaxiality + b_a_ratio + mass

    The function returns a DataFrame with one row per predictor (including
    the mass term) containing regression statistics.

    Expected columns (as asserted in the test suite):
        - predictor
        - coefficient
        - p_value
        - r_squared
        - ci_lower
        - ci_upper

    NaN rows are dropped automatically.

    Args:
        data: DataFrame containing at least the columns
              ``triaxiality``, ``b_a_ratio``, ``mass`` and the outcome.
        outcome: Name of the dependent variable column (default ``sfr``).

    Returns:
        DataFrame with regression results.
    """
    # Drop rows with missing values in any of the required columns
    required_cols = ["triaxiality", "b_a_ratio", "mass", outcome]
    clean = data.dropna(subset=required_cols)

    if clean.empty:
        raise ValueError("No valid data rows after dropping NaNs.")

    y = clean[outcome].astype(float)
    X = clean[["triaxiality", "b_a_ratio", "mass"]].astype(float)

    # Add constant term for intercept
    X = sm.add_constant(X)

    model = sm.OLS(y, X).fit()

    # Extract statistics for each predictor (excluding the intercept)
    results = []
    for predictor in ["triaxiality", "b_a_ratio", "mass"]:
        coef = model.params[predictor]
        pval = model.pvalues[predictor]
        ci_lower, ci_upper = model.conf_int().loc[predictor]

        results.append(
            {
                "predictor": predictor,
                "coefficient": coef,
                "p_value": pval,
                "r_squared": model.rsquared,
                "ci_lower": ci_lower,
                "ci_upper": ci_upper,
            }
        )

    return pd.DataFrame(results)

def run_statistical_tests(
    chunks_dir: str, output_path: str, outcome: str = "sfr"
) -> None:
    """
    Iterate over CSV chunk files, run the mass‑controlled regression on each,
    and concatenate the results into a single CSV.

    Args:
        chunks_dir: Directory containing chunk CSV files (e.g. ``match_001.csv``).
        output_path: Destination CSV path for the aggregated regression results.
        outcome: Dependent variable column name used in the regression.
    """
    chunk_dir_path = Path(chunks_dir)
    if not chunk_dir_path.is_dir():
        raise FileNotFoundError(f"Chunk directory not found: {chunks_dir}")

    all_results: List[pd.DataFrame] = []

    for csv_file in sorted(chunk_dir_path.glob("*.csv")):
        df = pd.read_csv(csv_file)
        # The test data includes columns needed for regression
        reg_result = linear_regression_with_mass_control(df, outcome=outcome)
        # Annotate with source chunk for traceability (optional)
        reg_result["chunk"] = csv_file.name
        all_results.append(reg_result)

    if not all_results:
        # Create an empty file with the correct header
        pd.DataFrame(
            columns=[
                "predictor",
                "coefficient",
                "p_value",
                "r_squared",
                "ci_lower",
                "ci_upper",
                "chunk",
            ]
        ).to_csv(output_path, index=False)
        return

    final_df = pd.concat(all_results, ignore_index=True)
    final_df.to_csv(output_path, index=False)
