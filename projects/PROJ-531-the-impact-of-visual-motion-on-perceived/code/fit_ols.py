"""
T021 – Fit Ordinary Least Squares regression

This script reads the analysis-ready dataset, fits an OLS regression model,
and writes the results to `data/results/ols.json`. The output JSON contains
the model coefficients, standard errors, raw p‑values, and a placeholder
`cv_metrics` field for later cross‑validation updates.
"""

import json
import sys

import pandas as pd
import statsmodels.api as sm

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)


def load_data(csv_path):
    """Load the analysis‑ready CSV."""
    try:
        df = pd.read_csv(csv_path)
        log.info(f"Loaded data from {csv_path} with shape {df.shape}")
        return df
    except Exception as e:
        log.error(f"Failed to load data from {csv_path}: {e}")
        raise


def fit_ols(df, target_col="agency_score"):
    """
    Fit an OLS regression model.

    Returns a dict with:
        - coefficients: mapping feature → coefficient (including intercept as "const")
        - standard_errors: mapping feature → standard error
        - p_values: mapping feature → raw p‑value
    """
    # Identify predictor columns (exclude target and any non‑numeric columns)
    predictor_cols = [c for c in df.columns if c != target_col and pd.api.types.is_numeric_dtype(df[c])]
    X = df[predictor_cols]
    y = df[target_col]

    # Add constant term for intercept
    X_const = sm.add_constant(X, has_constant='add')

    model = sm.OLS(y, X_const).fit()

    results = {
        "coefficients": model.params.to_dict(),
        "standard_errors": model.bse.to_dict(),
        "p_values": model.pvalues.to_dict(),
    }
    log.info("OLS fitting complete.")
    return results


def main():
    # Paths
    input_path = paths.data("processed", "analysis_ready.csv")
    output_path = paths.data("results", "ols.json")

    # Load data
    df = load_data(input_path)

    # Fit OLS
    ols_results = fit_ols(df)

    # Add placeholder cv_metrics (to be filled later by cross‑validation step)
    ols_results["cv_metrics"] = {
        "r2_mean": None,
        "r2_std": None,
        "rmse_mean": None
    }

    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write JSON
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(ols_results, f, indent=2, sort_keys=True)
    log.info(f"OLS results written to {output_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
