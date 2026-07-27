import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
import scipy.stats
import statsmodels.api as sm

logger = logging.getLogger(__name__)


def _infer_outcome_and_predictors(
    df: pd.DataFrame, outcome: Optional[str] = None, predictors: Optional[List[str]] = None
) -> Tuple[str, List[str]]:
    """
    Helper to infer ``outcome`` and ``predictors`` if they are not supplied.

    - If ``outcome`` is ``None``, the first column that is binary (contains only 0/1)
      is selected.  If no binary column exists, the last column is used.
    - If ``predictors`` is ``None``, all numeric columns except the outcome are used.
    """
    if outcome is None:
        # Look for a binary column.
        for col in df.columns:
            if set(df[col].dropna().unique()).issubset({0, 1}):
                outcome = col
                break
        else:
            outcome = df.columns[-1]  # fallback to last column

    if predictors is None:
        predictors = [
            c for c in df.select_dtypes(include=[np.number]).columns if c != outcome
        ]

    return outcome, predictors


def _run_t_test(df: pd.DataFrame, outcome: str, predictor: str) -> Dict[str, Any]:
    """
    Perform an independent two‑sample t‑test on ``outcome`` split by the median of
    ``predictor``.
    """
    median_val = df[predictor].median()
    group_a = df.loc[df[predictor] <= median_val, outcome].dropna()
    group_b = df.loc[df[predictor] > median_val, outcome].dropna()

    # Guard against empty groups.
    if len(group_a) < 2 or len(group_b) < 2:
        logger.warning(
            f"Insufficient data for t‑test on predictor '{predictor}'. Returning NaNs."
        )
        return {"p_value": np.nan, "ci": [np.nan, np.nan]}

    t_stat, p_value = scipy.stats.ttest_ind(group_a, group_b, equal_var=False)
    # 95% confidence interval for the difference in means.
    diff = group_a.mean() - group_b.mean()
    se = np.sqrt(group_a.var(ddof=1) / len(group_a) + group_b.var(ddof=1) / len(group_b))
    ci_low = diff - 1.96 * se
    ci_high = diff + 1.96 * se
    return {"p_value": float(p_value), "ci": [float(ci_low), float(ci_high)]}


def _run_linear_regression(
    df: pd.DataFrame, outcome: str, predictors: List[str]
) -> Dict[str, Any]:
    """
    Fit an OLS regression ``outcome ~ predictors`` and return R² and coefficient map.
    """
    X = df[predictors].copy()
    X = sm.add_constant(X, has_constant="add")
    y = df[outcome]

    # Drop rows with missing values.
    data = pd.concat([X, y], axis=1).dropna()
    if data.empty:
        logger.warning("No data left after dropping NA for regression. Returning NaNs.")
        return {"r_squared": np.nan, "coefficients": {}}

    X_clean = data[X.columns]
    y_clean = data[outcome]

    model = sm.OLS(y_clean, X_clean).fit()
    coeffs = {str(k): float(v) for k, v in model.params.items()}
    return {"r_squared": float(model.rsquared), "coefficients": coeffs}


def _analyze_dataframe(
    df: pd.DataFrame,
    outcome: Optional[str] = None,
    predictors: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Compute t‑test (using the first numeric predictor) and linear regression metrics
    for a single DataFrame.
    """
    outcome, predictors = _infer_outcome_and_predictors(df, outcome, predictors)

    # Use the first predictor for the t‑test (as a simple, deterministic choice).
    t_test_res = _run_t_test(df, outcome, predictors[0] if predictors else outcome)
    linreg_res = _run_linear_regression(df, outcome, predictors)

    return {"t_test": t_test_res, "linear_regression": linreg_res}


def run_baseline_analysis(
    *args,
    raw_dir: Optional[Union[str, os.PathLike]] = None,
    dataframe: Optional[pd.DataFrame] = None,
    outcome: Optional[str] = None,
    predictors: Optional[List[str]] = None,
    output_file: Optional[Union[str, os.PathLike]] = None,
    extra_kwargs_dict: Optional[Dict[str, Any]] = None,
    **kwargs,
) -> Dict[str, Any]:
    """
    Flexible entry point used throughout the project.

    Supported invocation patterns (all are accepted):

    1. ``run_baseline_analysis()`` – analyses all CSVs under the default raw directory
       (``data/raw``) and writes the aggregated JSON to ``data/processed/baseline_metrics.json``.

    2. ``run_baseline_analysis(dataframe=df)`` – analyses a single DataFrame and
       returns the metrics dictionary (no file written unless ``output_file`` is supplied).

    3. ``run_baseline_analysis(raw_dir='data/raw', output_file='data/processed/baseline_metrics.json')``
       – explicit paths.

    4. ``run_baseline_analysis('data/raw', 'data/processed/baseline_metrics.json')``
       – positional shortcut for ``raw_dir`` and ``output_file``.

    5. ``run_baseline_analysis(raw_dir, output_file, extra_kwargs_dict)`` – legacy signature.

    All additional keyword arguments are ignored but accepted for forward‑compatibility.
    """
    # Normalise positional arguments.
    if args:
        if len(args) >= 1 and raw_dir is None:
            raw_dir = args[0]
        if len(args) >= 2 and output_file is None:
            output_file = args[1]
        if len(args) >= 3 and extra_kwargs_dict is None:
            extra_kwargs_dict = args[2]

    # Merge any explicit dict supplied via ``extra_kwargs_dict``.
    if extra_kwargs_dict:
        # Allow callers to pass any of the named parameters inside the dict.
        raw_dir = extra_kwargs_dict.get("raw_dir", raw_dir)
        dataframe = extra_kwargs_dict.get("dataframe", dataframe)
        outcome = extra_kwargs_dict.get("outcome", outcome)
        predictors = extra_kwargs_dict.get("predictors", predictors)
        output_file = extra_kwargs_dict.get("output_file", output_file)

    # Default locations if not provided.
    if raw_dir is None:
        raw_dir = Path("data") / "raw"
    if output_file is None:
        output_file = Path("data") / "processed" / "baseline_metrics.json"

    raw_dir = Path(raw_dir)
    output_file = Path(output_file)

    results: Dict[str, Any] = {}

    if dataframe is not None:
        # Single DataFrame analysis.
        logger.info("Running baseline analysis on provided DataFrame.")
        results = _analyze_dataframe(dataframe, outcome, predictors)
    else:
        # Directory‑wide analysis – iterate over CSV files.
        logger.info(f"Running baseline analysis on all CSVs in {raw_dir}.")
        if not raw_dir.is_dir():
            raise FileNotFoundError(f"Raw data directory not found: {raw_dir}")

        csv_files = list(raw_dir.glob("*.csv"))
        if not csv_files:
            raise FileNotFoundError(f"No CSV files found in {raw_dir}")

        for csv_path in csv_files:
            df = pd.read_csv(csv_path)
            logger.debug(f"Analyzing {csv_path.name}")
            results[csv_path.name] = _analyze_dataframe(df, outcome, predictors)

    # Write results if an output path is supplied.
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    logger.info(f"Baseline analysis results written to {output_file}")

    return results