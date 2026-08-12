import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
from scipy import stats
import statsmodels.api as sm

logger = logging.getLogger(__name__)

def _compute_cohens_d(group1: np.ndarray, group2: np.ndarray) -> float:
    """
    Compute Cohen's d using the pooled standard deviation of the two groups.
    """
    n1, n2 = len(group1), len(group2)
    if n1 == 0 or n2 == 0:
        return float("nan")
    s1, s2 = np.var(group1, ddof=1), np.var(group2, ddof=1)
    pooled_sd = np.sqrt(((n1 - 1) * s1 + (n2 - 1) * s2) / (n1 + n2 - 2))
    if pooled_sd == 0:
        return 0.0
    return (np.mean(group1) - np.mean(group2)) / pooled_sd

def _ci_for_mean_diff(group1: np.ndarray, group2: np.ndarray, confidence: float = 0.95) -> Tuple[float, float]:
    """
    Compute the confidence interval for the difference of means using the
    standard error of the difference.
    """
    diff = np.mean(group1) - np.mean(group2)
    se = np.sqrt(np.var(group1, ddof=1) / len(group1) + np.var(group2, ddof=1) / len(group2))
    if se == 0:
        return diff, diff
    h = se * stats.t.ppf((1 + confidence) / 2.0, df=min(len(group1), len(group2)) - 1)
    return diff - h, diff + h

def _run_analysis_on_dataframe(
    df: pd.DataFrame,
    outcome: Optional[str] = None,
    predictors: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Perform a single‑variable t‑test (outcome vs. each predictor) and linear
    regression for the first predictor.  The function returns a dictionary
    containing the p‑value, 95 % CI and effect size for the first predictor
    (or NaNs if the computation cannot be performed).
    """
    # Determine outcome and predictor columns
    if outcome is None:
        outcome = df.columns[0]
    if predictors is None:
        predictors = [c for c in df.columns if c != outcome]

    if not predictors:
        logger.warning("No predictor columns found in dataframe.")
        return {}

    predictor = predictors[0]

    # Ensure numeric data
    try:
        y = pd.to_numeric(df[outcome], errors="coerce").dropna().values
        x = pd.to_numeric(df[predictor], errors="coerce").dropna().values
    except Exception as e:
        logger.error(f"Failed to coerce columns to numeric: {e}")
        return {}

    # Align lengths
    min_len = min(len(y), len(x))
    y, x = y[:min_len], x[:min_len]

    # t‑test (independent samples).  If the outcome is binary we treat it as group labels.
    if set(np.unique(y)) <= {0, 1}:
        # Split predictor by outcome groups
        group0 = x[y == 0]
        group1 = x[y == 1]
        if len(group0) == 0 or len(group1) == 0:
            t_p = float("nan")
            ci = (float("nan"), float("nan"))
            d = float("nan")
        else:
            t_res = stats.ttest_ind(group0, group1, equal_var=False)
            t_p = float(t_res.pvalue)
            ci = _ci_for_mean_diff(group0, group1)
            d = _compute_cohens_d(group0, group1)
    else:
        # Treat as paired samples (fallback)
        t_res = stats.ttest_rel(y, x)
        t_p = float(t_res.pvalue)
        ci = _ci_for_mean_diff(y, x)
        d = _compute_cohens_d(y, x)

    # Linear regression using statsmodels (predictor -> outcome)
    try:
        X = sm.add_constant(x)
        model = sm.OLS(y, X).fit()
        reg_p = float(model.pvalues[1]) if len(model.pvalues) > 1 else float("nan")
    except Exception:
        reg_p = float("nan")

    result = {
        "t_test": {
            "p_value": round(t_p, 5) if not np.isnan(t_p) else None,
            "ci": [round(ci[0], 5), round(ci[1], 5)] if not any(np.isnan(ci)) else None,
            "effect_size": round(d, 5) if not np.isnan(d) else None,
        },
        "linear_regression": {
            "p_value": round(reg_p, 5) if not np.isnan(reg_p) else None,
        },
    }
    return result

def run_baseline_analysis(*args, **kwargs) -> Dict[str, Any]:
    """
    Flexible entry point used throughout the code base.

    Accepted calling patterns (all are supported):
        run_baseline_analysis()
        run_baseline_analysis(dataframe=df)
        run_baseline_analysis(dataframe=df, outcome='y', predictors=['x1','x2'])
        run_baseline_analysis(raw_dir='data/raw', output_file='data/processed/baseline_metrics.json')
        run_baseline_analysis('data/raw', 'data/processed/baseline_metrics.json')
        run_baseline_analysis(raw_dir, output_file, extra_kwargs_dict)

    The function returns a dictionary of metrics.  If ``output_file`` is supplied,
    the metrics are also written to that JSON file.
    """
    # Resolve positional arguments
    raw_dir = None
    output_file = None
    dataframe = None
    outcome = None
    predictors = None

    # Positional handling
    if args:
        # First positional arg could be a DataFrame or a raw_dir string
        if isinstance(args[0], pd.DataFrame):
            dataframe = args[0]
        elif isinstance(args[0], str):
            raw_dir = args[0]

    if len(args) > 1:
        if isinstance(args[1], str):
            output_file = args[1]

    # Keyword handling (overwrites positional if present)
    raw_dir = kwargs.get("raw_dir", raw_dir)
    output_file = kwargs.get("output_file", output_file)
    dataframe = kwargs.get("dataframe", dataframe)
    outcome = kwargs.get("outcome", outcome)
    predictors = kwargs.get("predictors", predictors)

    # If a dataframe is supplied, analyse it directly
    if isinstance(dataframe, pd.DataFrame):
        metrics = _run_analysis_on_dataframe(dataframe, outcome, predictors)
        if output_file:
            Path(output_file).parent.mkdir(parents=True, exist_ok=True)
            with open(output_file, "w") as fp:
                json.dump(metrics, fp, indent=2)
        return metrics

    # Otherwise load datasets from raw_dir
    if raw_dir is None:
        raise ValueError("Either a dataframe or raw_dir must be provided.")

    raw_path = Path(raw_dir)
    if not raw_path.is_dir():
        raise FileNotFoundError(f"Raw directory not found: {raw_dir}")

    all_metrics: Dict[str, Any] = {}
    for file in raw_path.glob("*.csv"):
        try:
            df = pd.read_csv(file)
            ds_name = file.stem
            all_metrics[ds_name] = _run_analysis_on_dataframe(df, outcome, predictors)
        except Exception as e:
            logger.error(f"Failed to process {file.name}: {e}")

    if output_file:
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, "w") as fp:
            json.dump(all_metrics, fp, indent=2)

    return all_metrics

def main():
    """
    Simple command‑line entry point mirroring the behaviour of the original
    script.  It runs baseline analysis on the default raw directory and writes
    the results to the default processed location.
    """
    default_raw = "data/raw"
    default_out = "data/processed/baseline_metrics.json"
    run_baseline_analysis(raw_dir=default_raw, output_file=default_out)
