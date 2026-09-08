"""
Analysis module providing statistical utilities for the project.
Implements t-test, linear regression, and a flexible baseline analysis
function that can accept either a DataFrame directly or raw data directory
specifications. Designed to satisfy the unit tests in
`tests/unit/test_analysis.py`.
"""

import json
import logging
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats
import statsmodels.api as sm

logger = logging.getLogger(__name__)


def run_t_test(df: pd.DataFrame, outcome_col: str, group_col: str) -> dict:
    """
    Perform Welch's two‑sample t‑test between two groups.

    Parameters
    ----------
    df : pd.DataFrame
        Data containing the outcome and grouping columns.
    outcome_col : str
        Name of the numeric outcome variable.
    group_col : str
        Name of the column indicating group membership. Must contain exactly two
        distinct values.

    Returns
    -------
    dict
        Dictionary with keys ``p_value`` and ``effect_size`` (Cohen's d).
    """
    groups = df[group_col].unique()
    if len(groups) != 2:
        raise ValueError("Exactly two groups are required for a t‑test.")

    # Separate the two groups, dropping missing values.
    g1 = df.loc[df[group_col] == groups[0], outcome_col].dropna()
    g2 = df.loc[df[group_col] == groups[1], outcome_col].dropna()

    # Welch's t‑test (unequal variances).
    t_stat, p_value = stats.ttest_ind(g1, g2, equal_var=False)

    # Cohen's d using pooled standard deviation of the two groups.
    n1, n2 = len(g1), len(g2)
    if n1 < 2 or n2 < 2:
        effect_size = 0.0
    else:
        var1, var2 = g1.var(ddof=1), g2.var(ddof=1)
        pooled_sd = np.sqrt(((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2))
        if pooled_sd == 0:
            effect_size = 0.0
        else:
            effect_size = (g1.mean() - g2.mean()) / pooled_sd

    logger.debug(
        "t‑test completed: t=%.4f, p=%.6f, Cohen's d=%.4f", t_stat, p_value, effect_size
    )
    return {"p_value": float(p_value), "effect_size": float(effect_size)}


def run_linear_regression(df: pd.DataFrame, outcome_col: str, covariate_cols: list) -> dict:
    """
    Fit an OLS linear regression model.

    Parameters
    ----------
    df : pd.DataFrame
        Data containing the outcome and covariate columns.
    outcome_col : str
        Name of the dependent variable.
    covariate_cols : list
        List of column names to be used as independent variables.

    Returns
    -------
    dict
        Dictionary with keys ``p_value`` (overall model F‑test) and
        ``r_squared``.
    """
    if not covariate_cols:
        raise ValueError("At least one covariate column must be provided.")

    X = df[covariate_cols].copy()
    X = sm.add_constant(X)  # adds intercept term
    y = df[outcome_col]

    model = sm.OLS(y, X, missing="drop").fit()

    # Overall model significance via the F‑test.
    p_value = float(model.f_pvalue) if hasattr(model, "f_pvalue") else None
    r_squared = float(model.rsquared)

    logger.debug(
        "Linear regression completed: R²=%.4f, overall p=%.6f", r_squared, p_value
    )
    return {"p_value": p_value, "r_squared": r_squared}


def _load_raw_dataset(raw_dir: str) -> pd.DataFrame:
    """
    Load the first CSV file found in ``raw_dir``.

    Raises
    ------
    FileNotFoundError
        If no CSV files are present.
    """
    raw_path = Path(raw_dir)
    for csv_path in raw_path.glob("*.csv"):
        logger.info("Loading raw dataset from %s", csv_path)
        return pd.read_csv(csv_path)
    raise FileNotFoundError(f"No CSV files found in raw directory: {raw_dir}")


def run_baseline_analysis(*args, **kwargs) -> dict:
    """
    Flexible baseline analysis entry point.

    Supported calling patterns (all are accepted):

    1. ``run_baseline_analysis(dataframe=df)`` – direct DataFrame input.
    2. ``run_baseline_analysis(df)`` – positional DataFrame.
    3. ``run_baseline_analysis(raw_dir='data/raw', output_file='out.json')``
    4. ``run_baseline_analysis('data/raw', 'out.json')``
    5. ``run_baseline_analysis(raw_dir, output_file, extra_kwargs_dict)`` – extra
       kwargs are ignored but kept for backward compatibility.

    The function returns a dictionary containing at least a ``p_value`` key
    (from the t‑test or regression, whichever is applicable).  If ``output_file``
    is provided, the result is written as JSON to that path.
    """
    df = None
    raw_dir = None
    output_file = None

    # ----------------------------------------------------------------------
    # Resolve arguments
    # ----------------------------------------------------------------------
    if "dataframe" in kwargs:
        df = kwargs["dataframe"]
    elif args:
        first = args[0]
        if isinstance(first, pd.DataFrame):
            df = first
        else:
            raw_dir = first
            if len(args) > 1:
                output_file = args[1]
    # explicit keyword overrides
    if df is None and "raw_dir" in kwargs:
        raw_dir = kwargs["raw_dir"]
    if "output_file" in kwargs:
        output_file = kwargs["output_file"]

    # ----------------------------------------------------------------------
    # Load DataFrame if needed
    # ----------------------------------------------------------------------
    if df is None:
        if raw_dir is None:
            raise ValueError("Either a DataFrame or a raw_dir must be supplied.")
        df = _load_raw_dataset(raw_dir)

    # ----------------------------------------------------------------------
    # Perform analyses
    # ----------------------------------------------------------------------
    result = {}

    # Attempt t‑test if the expected columns exist.
    if "outcome" in df.columns and "group" in df.columns:
        result.update(run_t_test(df, "outcome", "group"))

    # Perform a regression using all numeric columns except the outcome.
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    covariates = [c for c in numeric_cols if c != "outcome"]
    if covariates:
        result.update(run_linear_regression(df, "outcome", covariates))

    # ----------------------------------------------------------------------
    # Optional JSON export
    # ----------------------------------------------------------------------
    if output_file:
        out_path = Path(output_file)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(result, indent=2))
        logger.info("Baseline analysis results written to %s", out_path)

    return result


__all__ = [
    "run_t_test",
    "run_linear_regression",
    "run_baseline_analysis",
]
