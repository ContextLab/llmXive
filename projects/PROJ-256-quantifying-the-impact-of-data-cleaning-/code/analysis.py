import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import numpy as np
import pandas as pd
from scipy import stats
import statsmodels.api as sm

logger = logging.getLogger(__name__)

def _load_first_csv_from_dir(directory: Union[str, Path]) -> pd.DataFrame:
    """Load the first CSV file found in *directory*."""
    directory = Path(directory)
    csv_files = list(directory.glob("*.csv"))
    if not csv_files:
        raise FileNotFoundError(f"No CSV files found in {directory}")
    return pd.read_csv(csv_files[0])

def _default_split_groups(series: pd.Series) -> List[pd.Series]:
    """
    Split a numeric series into two groups based on the median.
    """
    median = series.median()
    group_low = series[series <= median]
    group_high = series[series > median]
    return [group_low, group_high]

def _t_test(series: pd.Series) -> Dict[str, Any]:
    """
    Perform a two‑sample t‑test on the provided series split by median.
    Returns a dictionary with p‑value and a 95 % confidence interval for the
    difference of means.
    """
    g1, g2 = _default_split_groups(series)
    t_stat, p_val = stats.ttest_ind(g1, g2, equal_var=False)

    # Confidence interval for difference of means
    diff = g1.mean() - g2.mean()
    se = np.sqrt(g1.var(ddof=1) / len(g1) + g2.var(ddof=1) / len(g2))
    ci_low, ci_high = stats.t.interval(
        0.95, df=min(len(g1), len(g2)) - 1, loc=diff, scale=se
    )
    return {"p_value": float(p_val), "ci": [float(ci_low), float(ci_high)], "t_stat": float(t_stat)}

def _linear_regression(outcome: pd.Series, predictors: pd.DataFrame) -> Dict[str, Any]:
    """
    Fit an OLS regression (outcome ~ predictors) and return p‑value for the
    overall model (F‑test) and R².
    """
    X = sm.add_constant(predictors, has_constant="add")
    model = sm.OLS(outcome, X, missing="drop")
    results = model.fit()
    p_val = float(results.f_pvalue) if hasattr(results, "f_pvalue") else np.nan
    r2 = float(results.rsquared) if hasattr(results, "rsquared") else np.nan
    return {"p_value": p_val, "r_squared": r2, "f_stat": float(results.fvalue) if hasattr(results, "fvalue") else np.nan}

def run_baseline_analysis(*args, **kwargs) -> Dict[str, Any]:
    """
    Flexible baseline analysis entry point.

    Supported calling patterns:
    1. run_baseline_analysis(dataframe=df, outcome='y', predictors=['x1','x2'])
    2. run_baseline_analysis(dataframe=df)  # outcome = first column, predictors = rest
    3. run_baseline_analysis(raw_dir='data/raw', output_file='data/processed/baseline_metrics.json')
    4. run_baseline_analysis('data/raw', 'data/processed/baseline_metrics.json')
    5. run_baseline_analysis('data/raw', output_file='data/processed/baseline_metrics.json')
    """
    # Resolve arguments
    dataframe: Optional[pd.DataFrame] = kwargs.get("dataframe")
    raw_dir: Optional[Union[str, Path]] = None
    output_file: Optional[Union[str, Path]] = None

    # Positional handling
    if args:
        # If first positional is a DataFrame we treat it as dataframe
        if isinstance(args[0], pd.DataFrame):
            dataframe = args[0]
            # possible second positional could be outcome or predictors – ignore for simplicity
        else:
            raw_dir = args[0]
            if len(args) > 1:
                output_file = args[1]

    # Keyword overrides
    if "raw_dir" in kwargs:
        raw_dir = kwargs["raw_dir"]
    if "output_file" in kwargs:
        output_file = kwargs["output_file"]

    # Load dataframe if not supplied
    if dataframe is None:
        if raw_dir is None:
            raise ValueError("Either a dataframe or raw_dir must be provided.")
        dataframe = _load_first_csv_from_dir(raw_dir)

    # Determine outcome and predictors
    outcome_col: str = kwargs.get("outcome")
    predictor_cols: List[str] = kwargs.get("predictors", [])

    if outcome_col is None:
        # Use the first column as outcome
        outcome_col = dataframe.columns[0]
    if not predictor_cols:
        predictor_cols = [c for c in dataframe.columns if c != outcome_col]

    outcome_series = dataframe[outcome_col]
    predictors_df = dataframe[predictor_cols]

    # Perform statistical analyses
    t_test_res = _t_test(outcome_series)
    linreg_res = _linear_regression(outcome_series, predictors_df)

    result: Dict[str, Any] = {
        "t_test": t_test_res,
        "linear_regression": linreg_res,
        "metadata": {
            "outcome": outcome_col,
            "predictors": predictor_cols,
            "row_count": int(dataframe.shape[0]),
            "column_count": int(dataframe.shape[1]),
        },
    }

    # Persist if required
    if output_file:
        out_path = Path(output_file)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with out_path.open("w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)
        logger.info("Baseline analysis written to %s", out_path)

    return result
