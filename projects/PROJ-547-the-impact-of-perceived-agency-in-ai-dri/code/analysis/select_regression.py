"""
Regression model selector for US3.

This module provides a utility function that, given an outcome vector ``y``
and a covariate matrix ``X`` (including the required confounders), selects
an appropriate regression model based on the statistical nature of ``y``:

* **Binary outcome** (0/1) → Logistic regression (scikit‑learn)
* **Proportion outcome** (values in (0, 1)) → Beta regression (statsmodels GLM)
* **Continuous outcome** → Ordinary Least Squares (statsmodels OLS)

The function also logs the selection decision using the project's
``pipeline_logger``.
"""

from __future__ import annotations

import argparse
import pickle
from pathlib import Path
from typing import Tuple

import pandas as pd
from sklearn.linear_model import LogisticRegression
import statsmodels.api as sm
from statsmodels.genmod.families import Beta

from logging.pipeline_logger import get_logger, log_dict

logger = get_logger(__name__)

def _detect_outcome_type(y: pd.Series) -> str:
    """
    Detect the statistical type of the outcome variable.

    Returns one of ``'binary'``, ``'proportion'`` or ``'continuous'``.
    """
    unique_vals = pd.Series(y.dropna().unique())
    # Binary: exactly two unique values and they are 0/1 (or True/False)
    if set(unique_vals) <= {0, 1, True, False} and len(unique_vals) == 2:
        return "binary"
    # Proportion: all values strictly between 0 and 1 (no exact 0/1)
    if y.between(0, 1, inclusive="neither").all():
        return "proportion"
    # Fallback to continuous
    return "continuous"

def select_regression(
    y: pd.Series, X: pd.DataFrame
) -> Tuple[str, object]:
    """
    Choose and fit an appropriate regression model.

    Parameters
    ----------
    y : pd.Series
        Outcome variable.
    X : pd.DataFrame
        Covariates (including the required confounders:
        age, gender, baseline severity, prior therapy).

    Returns
    -------
    model_type : str
        One of ``'logistic'``, ``'beta'`` or ``'ols'``.
    fitted_model : object
        The fitted model instance.
    """
    # Ensure X has an intercept column for statsmodels
    X_with_const = sm.add_constant(X, has_constant="add")
    outcome_type = _detect_outcome_type(y)

    logger.info(f"Detected outcome type: {outcome_type}")
    log_dict({"outcome_type": outcome_type, "n_samples": len(y)})

    if outcome_type == "binary":
        # scikit‑learn LogisticRegression expects 2‑D array
        model = LogisticRegression(solver="lbfgs", max_iter=1000)
        model.fit(X, y)
        model_type = "logistic"
    elif outcome_type == "proportion":
        # Beta regression via GLM; y must be strictly (0,1)
        if (y <= 0).any() or (y >= 1).any():
            raise ValueError(
                "Beta regression requires outcomes strictly between 0 and 1."
            )
        glm = sm.GLM(y, X_with_const, family=Beta())
        model = glm.fit()
        model_type = "beta"
    else:  # continuous
        ols = sm.OLS(y, X_with_const)
        model = ols.fit()
        model_type = "ols"

    logger.info(f"Selected model: {model_type}")
    log_dict({"selected_model": model_type})

    return model_type, model

def main() -> None:
    """
    Command‑line interface.

    Usage:
        python -m analysis.select_regression \\
            --input data/processed/merged_data.csv \\
            --outcome agency_score \\
            --model-output models/selected_model.pkl
    """
    parser = argparse.ArgumentParser(
        description="Select and fit a regression model based on outcome type."
    )
    parser.add_argument(
        "--input",
        type=Path,
        required=True,
        help="Path to merged CSV containing outcome and confounders.",
    )
    parser.add_argument(
        "--outcome",
        type=str,
        required=True,
        help="Column name of the outcome variable.",
    )
    parser.add_argument(
        "--model-output",
        type=Path,
        required=True,
        help="File path where the fitted model will be serialized (pickle).",
    )
    args = parser.parse_args()

    df = pd.read_csv(args.input)
    if args.outcome not in df.columns:
        raise ValueError(f"Outcome column '{args.outcome}' not found in input data.")

    y = df[args.outcome]
    # Expected confounder columns (the pipeline guarantees they exist)
    confounders = ["age", "gender", "baseline_severity", "prior_therapy"]
    missing = [c for c in confounders if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required confounder columns: {missing}")

    X = df[confounders]

    model_type, model = select_regression(y, X)

    # Ensure the output directory exists
    args.model_output.parent.mkdir(parents=True, exist_ok=True)

    with open(args.model_output, "wb") as f:
        pickle.dump({"model_type": model_type, "model": model}, f)

    logger.info(f"Model serialized to {args.model_output}")
    log_dict({"model_output_path": str(args.model_output), "model_type": model_type})

if __name__ == "__main__":
    main()
