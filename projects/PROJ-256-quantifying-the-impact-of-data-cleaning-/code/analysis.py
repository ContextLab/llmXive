import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd
from scipy import stats
import statsmodels.api as sm

logger = logging.getLogger(__name__)

def _load_dataframe_from_path(path: Union[str, Path]) -> pd.DataFrame:
    """Load the first CSV file found in the given directory."""
    path = Path(path)
    if path.is_file():
        return pd.read_csv(path)
    if path.is_dir():
        for file in sorted(path.iterdir()):
            if file.suffix.lower() == ".csv":
                return pd.read_csv(file)
    raise FileNotFoundError(f"No CSV file found in {path}")

def _default_outcome_and_predictors(df: pd.DataFrame) -> Tuple[str, List[str]]:
    """Pick a sensible default outcome column and predictor columns."""
    # Prefer a binary column named 'target' or 'outcome'
    possible_outcomes = [c for c in df.columns if c.lower() in {"target", "outcome", "label"}]
    if possible_outcomes:
        outcome = possible_outcomes[0]
    else:
        # Fallback to the first column
        outcome = df.columns[0]
    predictors = [c for c in df.columns if c != outcome and np.issubdtype(df[c].dtype, np.number)]
    if not predictors:
        # If no numeric predictors, use all non‑outcome columns as categorical predictors
        predictors = [c for c in df.columns if c != outcome]
    return outcome, predictors

def _run_regression(df: pd.DataFrame, outcome: str, predictor: str) -> Dict[str, Any]:
    """Run a simple OLS regression of outcome ~ predictor."""
    X = sm.add_constant(df[[predictor]].astype(float))
    y = df[outcome].astype(float)
    model = sm.OLS(y, X, missing='drop')
    results = model.fit()
    coef = results.params[predictor]
    p_value = results.pvalues[predictor]
    conf_int = results.conf_int().loc[predictor].tolist()
    return {
        "coefficient": float(coef),
        "p_value": float(p_value),
        "ci": [float(conf_int[0]), float(conf_int[1])],
    }

def _run_ttest(df: pd.DataFrame, outcome: str, predictor: str) -> Dict[str, Any]:
    """If outcome is binary, perform a t‑test between the two groups for the predictor."""
    if df[outcome].nunique() != 2:
        return {}
    groups = df.groupby(outcome)[predictor]
    try:
        t_stat, p_val = stats.ttest_ind(groups.get_group(df[outcome].unique()[0]),
                                       groups.get_group(df[outcome].unique()[1]),
                                       equal_var=False, nan_policy='omit')
        # Compute Cohen's d
        mean1, mean2 = groups.get_group(df[outcome].unique()[0]).mean(), groups.get_group(df[outcome].unique()[1]).mean()
        var1, var2 = groups.get_group(df[outcome].unique()[0]).var(), groups.get_group(df[outcome].unique()[1]).var()
        n1, n2 = groups.get_group(df[outcome].unique()[0]).size, groups.get_group(df[outcome].unique()[1]).size
        pooled_sd = np.sqrt(((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2))
        cohen_d = (mean1 - mean2) / pooled_sd if pooled_sd != 0 else 0.0
        return {
            "t_stat": float(t_stat),
            "p_value": float(p_val),
            "cohen_d": float(cohen_d),
        }
    except Exception as e:
        logger.debug(f"T‑test failed for predictor {predictor}: {e}")
        return {}

def run_baseline_analysis(*args, **kwargs) -> Dict[str, Any]:
    """
    Flexible baseline analysis entry point.

    Supported signatures (all are accepted):
    1. run_baseline_analysis(dataframe=df, outcome='y', predictors=[...])
    2. run_baseline_analysis(df)                     # df is a DataFrame
    3. run_baseline_analysis(raw_dir, output_file)
    4. run_baseline_analysis(raw_dir, output_file, config)
    5. run_baseline_analysis()                       # uses env config defaults
    """
    # Resolve positional arguments
    raw_dir = None
    output_file = None
    config = None
    dataframe = None
    outcome = None
    predictors = None

    # Positional handling
    if args:
        # If first positional arg is a DataFrame, treat it as dataframe mode
        if isinstance(args[0], pd.DataFrame):
            dataframe = args[0]
            if len(args) > 1:
                outcome = args[1] if isinstance(args[1], str) else None
            if len(args) > 2:
                predictors = args[2] if isinstance(args[2], (list, tuple)) else None
        else:
            # Assume first is raw_dir, second is output_file, third optional config
            raw_dir = args[0]
            if len(args) > 1:
                output_file = args[1]
            if len(args) > 2:
                config = args[2]

    # Keyword overrides
    if 'dataframe' in kwargs:
        dataframe = kwargs['dataframe']
    if 'outcome' in kwargs:
        outcome = kwargs['outcome']
    if 'predictors' in kwargs:
        predictors = kwargs['predictors']
    if 'raw_dir' in kwargs:
        raw_dir = kwargs['raw_dir']
    if 'output_file' in kwargs:
        output_file = kwargs['output_file']
    if 'config' in kwargs:
        config = kwargs['config']

    # Load dataframe if we have a raw_dir but no dataframe yet
    if dataframe is None and raw_dir is not None:
        dataframe = _load_dataframe_from_path(raw_dir)

    if dataframe is None:
        raise ValueError("No data provided to run_baseline_analysis.")

    # Determine outcome & predictors if not supplied
    if outcome is None or predictors is None:
        outcome, predictors = _default_outcome_and_predictors(dataframe)

    metrics: Dict[str, Any] = {"outcome": outcome, "predictors": {}}

    for pred in predictors:
        pred_metrics: Dict[str, Any] = {}

        # Regression
        try:
            reg = _run_regression(dataframe, outcome, pred)
            pred_metrics["regression"] = reg
        except Exception as e:
            logger.debug(f"Regression failed for {pred}: {e}")

        # t‑test (only if binary outcome)
        ttest_res = _run_ttest(dataframe, outcome, pred)
        if ttest_res:
            pred_metrics["t_test"] = ttest_res

        metrics["predictors"][pred] = pred_metrics

    # Write to file if an explicit output path is given
    if output_file:
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(metrics, f, indent=2)
        logger.info(f"Baseline analysis written to {output_path}")

    return metrics