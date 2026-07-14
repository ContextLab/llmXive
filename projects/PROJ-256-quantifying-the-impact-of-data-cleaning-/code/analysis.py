import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
from scipy import stats

logger = logging.getLogger(__name__)

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------


def _perform_simple_analysis(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Perform a very simple statistical analysis on a dataframe.
    Currently we:
    * Choose the first two numeric columns (if they exist)
    * Run an independent two‑sample t‑test
    * Compute Cohen's d as an effect size
    * Return p‑value, 95 % CI for the mean difference, and effect size.

    This is deliberately lightweight – the goal of the repository is to
    illustrate the pipeline rather than provide a full statistical suite.
    """
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    if len(numeric_cols) < 2:
        logger.warning(
            "Not enough numeric columns for t‑test; returning empty metrics."
        )
        return {}

    col1, col2 = numeric_cols[:2]
    x, y = df[col1].dropna(), df[col2].dropna()
    if len(x) == 0 or len(y) == 0:
        logger.warning("One of the selected columns is empty after NA removal.")
        return {}

    # t‑test
    t_stat, p_val = stats.ttest_ind(x, y, equal_var=False)

    # Cohen's d
    pooled_std = np.sqrt(((x.std() ** 2) + (y.std() ** 2)) / 2)
    cohen_d = (x.mean() - y.mean()) / pooled_std if pooled_std != 0 else 0.0

    # 95 % CI for the difference of means (Welch's formula)
    se = np.sqrt(x.var(ddof=1) / len(x) + y.var(ddof=1) / len(y))
    df_welch = (x.var(ddof=1) / len(x) + y.var(ddof=1) / len(y)) ** 2 / (
        (x.var(ddof=1) ** 2) / (len(x) ** 2 * (len(x) - 1))
        + (y.var(ddof=1) ** 2) / (len(y) ** 2 * (len(y) - 1))
    )
    ci_low, ci_high = stats.t.interval(
        0.95, df=df_welch, loc=(x.mean() - y.mean()), scale=se
    )

    return {
        "t_test": {
            "statistic": float(t_stat),
            "p_value": float(p_val),
            "ci": [float(ci_low), float(ci_high)],
        },
        "effect_size": {"cohen_d": float(cohen_d)},
    }

# ----------------------------------------------------------------------
# Public API – flexible ``run_baseline_analysis``
# ----------------------------------------------------------------------


def run_baseline_analysis(*args: Any, **kwargs: Any) -> bool:
    """
    Flexible entry point used throughout the code base.

    Supported call signatures (all are accepted):
    1. run_baseline_analysis(raw_dir, output_file, config)
    2. run_baseline_analysis(raw_dir, output_file, analysis_config)
    3. run_baseline_analysis(dataframe=df, outcome='y', predictors=['x1','x2'],
                             group_col='g', output_file=Path(...))

    The function normalises the inputs, performs a very simple analysis
    for each CSV found in ``raw_dir`` (or directly on the supplied
    dataframe) and writes a JSON file with the results.

    Returns
    -------
    bool
        ``True`` if at least one dataset was processed successfully,
        ``False`` otherwise.
    """
    # Resolve positional arguments
    raw_dir = None
    output_file = None
    config_obj = None
    df = None
    outcome = None
    predictors = None
    group_col = None

    if len(args) >= 3:
        raw_dir, output_file, config_obj = args[:3]
    elif len(args) == 2:
        raw_dir, output_file = args[:2]

    # Keyword overrides / explicit arguments
    raw_dir = kwargs.get("raw_dir", raw_dir)
    output_file = kwargs.get("output_file", output_file)
    config_obj = kwargs.get("config", config_obj) or kwargs.get("analysis_config", config_obj)
    df = kwargs.get("dataframe", df)
    outcome = kwargs.get("outcome", outcome)
    predictors = kwargs.get("predictors", predictors)
    group_col = kwargs.get("group_col", group_col)

    # Normalise paths
    if isinstance(raw_dir, (str, Path)):
        raw_dir = Path(raw_dir)
    if isinstance(output_file, (str, Path)):
        output_file = Path(output_file)

    results: Dict[str, Any] = {}

    try:
        if df is not None:
            # Direct dataframe analysis
            logger.info("Running baseline analysis on supplied dataframe.")
            analysis = _perform_simple_analysis(df)
            if analysis:
                results["provided_dataframe"] = analysis
        else:
            # Walk through CSV files in raw_dir
            if raw_dir is None or not raw_dir.is_dir():
                logger.error("Raw data directory not provided or does not exist.")
                return False

            csv_files = list(raw_dir.glob("*.csv"))
            if not csv_files:
                logger.error(f"No CSV files found in {raw_dir}.")
                return False

            for csv_path in csv_files:
                try:
                    df_cur = pd.read_csv(csv_path)
                    logger.info(f"Analyzing dataset {csv_path.name}.")
                    analysis = _perform_simple_analysis(df_cur)
                    if analysis:
                        results[csv_path.stem] = analysis
                except Exception as e:
                    logger.exception(f"Failed to process {csv_path.name}: {e}")

        # Write results
        if output_file is None:
            logger.error("No output file specified for baseline metrics.")
            return False

        output_file.parent.mkdir(parents=True, exist_ok=True)
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)

        logger.info(f"Baseline analysis written to {output_file}.")
        return bool(results)

    except Exception as exc:
        logger.exception(f"Unexpected error during baseline analysis: {exc}")
        return False
