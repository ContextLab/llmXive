import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import numpy as np
import pandas as pd
import scipy.stats as stats
import statsmodels.api as sm

logger = logging.getLogger(__name__)

def _compute_column_metrics(
    df: pd.DataFrame, column: str
) -> Dict[str, Any]:
    """
    Compute t‑test, 95 % CI and Cohen's d for a single numeric column.
    The column is split into two halves (first vs second) to form the two
    groups required for the test.
    """
    series = df[column].dropna()
    if series.empty:
        return {}

    # Split into two groups
    midpoint = len(series) // 2
    group1 = series.iloc[:midpoint]
    group2 = series.iloc[midpoint:]

    # Guard against empty groups
    if group1.empty or group2.empty:
        return {}

    # t‑test
    t_res = stats.ttest_ind(group1, group2, equal_var=False)
    p_value = float(t_res.pvalue)

    # Mean difference and CI
    diff = float(group1.mean() - group2.mean())
    n1, n2 = len(group1), len(group2)
    var1, var2 = group1.var(ddof=1), group2.var(ddof=1)
    se = np.sqrt(var1 / n1 + var2 / n2)
    ci_low = diff - 1.96 * se
    ci_high = diff + 1.96 * se

    # Cohen's d using pooled std
    s_pooled = np.sqrt(((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2))
    cohen_d = diff / s_pooled if s_pooled != 0 else 0.0

    return {
        "t_test": {
            "p_value": round(p_value, 5),
            "ci": [round(ci_low, 5), round(ci_high, 5)],
            "statistic": round(t_res.statistic, 5),
        },
        "cohen_d": round(cohen_d, 5),
    }

def run_baseline_analysis(
    *args,
    **kwargs,
) -> Dict[str, Any]:
    """
    Flexible entry point used throughout the codebase.

    Supported usage patterns:
      - run_baseline_analysis(dataframe=df)
      - run_baseline_analysis(dataframe=df, outcome='y', predictors=['x1'])
      - run_baseline_analysis(raw_dir='data/raw', output_file='data/processed/baseline_metrics.json')
      - run_baseline_analysis('data/raw', 'data/processed/baseline_metrics.json')
      - run_baseline_analysis(raw_dir, output_file, extra_kwargs_dict)
    The function returns a dict mapping dataset identifiers to their
    column‑wise metrics.
    """
    # Resolve arguments
    dataframe = kwargs.get("dataframe")
    raw_dir = kwargs.get("raw_dir")
    output_file = kwargs.get("output_file")
    extra_kwargs = kwargs.get("extra_kwargs_dict", {})

    # Positional handling
    if len(args) == 2 and isinstance(args[0], (str, Path)):
        raw_dir = str(args[0])
        output_file = str(args[1])
    elif len(args) == 1 and isinstance(args[0], pd.DataFrame):
        dataframe = args[0]

    # If a dataframe is supplied, analyse it directly
    if dataframe is not None:
        datasets = {"provided_dataframe": dataframe}
    else:
        # Load all CSV files from the raw directory
        raw_dir_path = Path(raw_dir or "data/raw")
        if not raw_dir_path.is_dir():
            logger.error(f"Raw data directory '{raw_dir_path}' does not exist.")
            return {}
        csv_files = list(raw_dir_path.glob("*.csv"))
        if not csv_files:
            logger.error(f"No CSV files found in '{raw_dir_path}'.")
            return {}

        datasets = {}
        for csv_path in csv_files:
            try:
                df = pd.read_csv(csv_path)
                datasets[csv_path.stem] = df
            except Exception as e:
                logger.warning(f"Failed to read '{csv_path}': {e}")

    # Compute metrics per dataset
    all_metrics: Dict[str, Any] = {}
    for ds_name, df in datasets.items():
        column_metrics: Dict[str, Any] = {}
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            metrics = _compute_column_metrics(df, col)
            if metrics:
                column_metrics[col] = metrics
        if column_metrics:
            all_metrics[ds_name] = column_metrics

    # Write to output if requested
    if output_file:
        out_path = Path(output_file)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        with out_path.open("w") as fp:
            json.dump(all_metrics, fp, indent=2)
        logger.info(f"Baseline metrics written to {out_path}")

    return all_metrics

def main():
    """
    Entry point used by ``python -m code.analysis``.
    Executes a baseline analysis on the default raw directory and writes
    the results to ``data/processed/baseline_metrics.json``.
    """
    run_baseline_analysis(
        raw_dir="data/raw",
        output_file="data/processed/baseline_metrics.json",
    )

if __name__ == "__main__":
    main()