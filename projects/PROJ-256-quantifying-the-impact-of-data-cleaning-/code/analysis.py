import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
import scipy.stats
import statsmodels.api as sm

from .data_loader import load_datasets_from_raw  # type: ignore

logger = logging.getLogger(__name__)

def _validate_p_value(p: float) -> bool:
    """Return True if p‑value is a proper probability (0,1)."""
    return 0.0 < p < 1.0

def _compute_ci(series: pd.Series, confidence: float = 0.95) -> Tuple[float, float]:
    """Return two‑sided confidence interval for the mean of a series."""
    if series.empty:
        raise ValueError("Series is empty, cannot compute CI.")
    mean = series.mean()
    sem = scipy.stats.sem(series, ddof=1)
    df = len(series) - 1
    interval = scipy.stats.t.interval(confidence, df, loc=mean, scale=sem)
    return interval

def _run_t_test(outcome: pd.Series, predictor: pd.Series) -> Dict[str, Any]:
    """Perform independent two‑sample t‑test assuming equal variance."""
    # Drop NaNs to avoid errors
    outcome_clean = outcome.dropna()
    predictor_clean = predictor.dropna()
    # If predictor is binary, treat as group labels
    if predictor_clean.nunique() == 2:
        groups = [
            outcome_clean[predictor_clean == val] for val in predictor_clean.unique()
        ]
        t_stat, p_val = scipy.stats.ttest_ind(*groups, equal_var=True)
    else:
        # fallback to correlation test
        t_stat, p_val = scipy.stats.pearsonr(predictor_clean, outcome_clean)
    ci = _compute_ci(outcome_clean)
    return {"p_value": p_val, "ci": list(ci), "t_stat": float(t_stat)}

def _run_linear_regression(df: pd.DataFrame, outcome_col: str, predictor_cols: List[str]) -> Dict[str, Any]:
    """Fit OLS regression and return overall p‑value and R²."""
    X = df[predictor_cols].apply(pd.to_numeric, errors="coerce")
    y = pd.to_numeric(df[outcome_col], errors="coerce")
    X = sm.add_constant(X)  # intercept
    model = sm.OLS(y, X, missing="drop")
    results = model.fit()
    # Overall F‑test p‑value for the model
    p_val = results.f_pvalue
    r2 = results.rsquared
    return {"p_value": float(p_val), "r2": float(r2), "summary": results.summary().as_text()}

def _infer_columns(df: pd.DataFrame) -> Tuple[str, List[str]]:
    """Heuristic to pick outcome and predictor columns."""
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    if len(numeric_cols) < 2:
        raise ValueError("Not enough numeric columns for analysis.")
    # Choose the column with highest variance as outcome (simple heuristic)
    variances = df[numeric_cols].var()
    outcome = variances.idxmax()
    predictors = [c for c in numeric_cols if c != outcome]
    return outcome, predictors

def run_baseline_analysis(
    *args,
    dataframe: Optional[pd.DataFrame] = None,
    outcome: Optional[str] = None,
    predictors: Optional[List[str]] = None,
    raw_dir: Optional[str] = None,
    output_file: Optional[str] = None,
    extra_kwargs: Optional[Dict[str, Any]] = None,
    **kwargs,
) -> Union[Dict[str, Any], None]:
    """
    Flexible entry point used throughout the repository.

    Supported usage patterns:
    1. run_baseline_analysis(dataframe=df) -> returns metrics dict.
    2. run_baseline_analysis(dataframe=df, outcome='y', predictors=['x1','x2'])
    3. run_baseline_analysis(raw_dir='data/raw', output_file='data/processed/baseline_metrics.json')
    4. run_baseline_analysis('data/raw', 'data/processed/baseline_metrics.json')
    5. run_baseline_analysis(raw_dir, output_file, extra_kwargs_dict)
    """
    # Merge positional args for the common (raw_dir, output_file) pattern
    if not dataframe and len(args) >= 2:
        raw_dir = raw_dir or args[0]
        output_file = output_file or args[1]

    if dataframe is not None:
        # Single‑dataset mode
        df = dataframe.copy()
        if outcome is None or predictors is None:
            outcome, predictors = _infer_columns(df)
        # Compute t‑test between outcome and each predictor; keep first result for simplicity
        t_test_res = _run_t_test(df[outcome], df[predictors[0]])
        lr_res = _run_linear_regression(df, outcome, predictors)
        metrics = {
            "t_test": t_test_res,
            "linear_regression": lr_res,
        }
        # Validate values
        if not _validate_p_value(t_test_res["p_value"]):
            logger.warning("T‑test produced out‑of‑range p‑value: %s", t_test_res["p_value"])
        if not _validate_p_value(lr_res["p_value"]):
            logger.warning("Linear regression produced out‑of‑range p‑value: %s", lr_res["p_value"])
        return metrics

    # Directory‑batch mode
    if raw_dir is None:
        raise ValueError("Either a dataframe or raw_dir must be supplied.")
    raw_path = Path(raw_dir)
    if not raw_path.is_dir():
        raise FileNotFoundError(f"Raw data directory not found: {raw_dir}")

    all_metrics = {}
    for csv_file in raw_path.glob("*.csv"):
        try:
            df = pd.read_csv(csv_file)
            outcome, predictors = _infer_columns(df)
            t_test_res = _run_t_test(df[outcome], df[predictors[0]])
            lr_res = _run_linear_regression(df, outcome, predictors)
            all_metrics[csv_file.name] = {
                "t_test": t_test_res,
                "linear_regression": lr_res,
            }
        except Exception as e:
            logger.error("Failed to process %s: %s", csv_file.name, e)
            continue

    if output_file:
        out_path = Path(output_file)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with out_path.open("w") as f:
            json.dump(all_metrics, f, indent=2)
        logger.info("Baseline analysis written to %s", out_path)
        return None
    else:
        return all_metrics
