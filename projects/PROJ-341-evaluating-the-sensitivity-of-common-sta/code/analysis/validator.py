"""
Real‑world dataset validator.

Downloads three public small‑sample datasets (UCI Breast Cancer, UCI Wine,
and OpenML Adult) and runs a simple statistical test on each. The resulting
p‑values are written to ``data/simulation/real_data_pvalues.csv`` for later
bootstrapping and validation steps.

The Adult dataset is loaded via a chunked streaming approach to honour the
*Large Dataset Rule* (Task T044). No full‑dataset materialisation occurs.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import List, Dict, Any

import pandas as pd
from scipy import stats

# Project‑specific utilities
from code.simulation.logging_config import get_logger
from code.analysis.openml_loader import load_adult_dataset_chunked

# ucimlrepo is already a declared dependency
from ucimlrepo import fetch_dataset

logger = get_logger(__name__)


def _download_uciml_dataset(dataset_id: int, name: str) -> pd.DataFrame:
    """
    Download a UCI dataset using ``ucimlrepo`` and return it as a DataFrame.

    Parameters
    ----------
    dataset_id: int
        The identifier used by the ``ucimlrepo`` package.
    name: str
        Human‑readable name for logging.

    Returns
    -------
    pd.DataFrame
        The loaded dataset.
    """
    logger.log("uciml_download_start", dataset_id=dataset_id, name=name)
    # ``fetch_dataset`` returns a tuple (data, metadata). We only need the data.
    data, _ = fetch_dataset(dataset_id)
    df = pd.DataFrame(data)
    logger.log("uciml_download_complete", rows=len(df), name=name)
    return df


def _run_simple_test(df: pd.DataFrame, dataset_name: str) -> List[Dict[str, Any]]:
    """
    Run a very simple statistical test on the provided DataFrame.

    The heuristic is:
    * If at least two numeric columns exist → two‑sample t‑test on the
      first two columns.
    * Otherwise, if at least two categorical columns exist → chi‑squared
      test on the cross‑tabulation of the first two columns.
    * If neither condition is met, the dataset is skipped.

    Returns a list of result dictionaries suitable for CSV output.
    """
    results: List[Dict[str, Any]] = []
    numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
    categorical_cols = df.select_dtypes(exclude=["number"]).columns.tolist()

    if len(numeric_cols) >= 2:
        col1, col2 = numeric_cols[:2]
        logger.log(
            "running_ttest",
            dataset=dataset_name,
            columns=[col1, col2],
        )
        # Drop NaNs for a fair comparison
        x = df[col1].dropna()
        y = df[col2].dropna()
        if len(x) == 0 or len(y) == 0:
            logger.log("ttest_skipped_no_data", dataset=dataset_name)
            return results
        t_stat, p_val = stats.ttest_ind(x, y, equal_var=False)
        results.append(
            {
                "dataset_id": dataset_name,
                "test_type": "t-test",
                "p_value": p_val,
            }
        )
    elif len(categorical_cols) >= 2:
        col1, col2 = categorical_cols[:2]
        logger.log(
            "running_chi2",
            dataset=dataset_name,
            columns=[col1, col2],
        )
        contingency = pd.crosstab(df[col1], df[col2])
        if contingency.empty:
            logger.log("chi2_skipped_empty", dataset=dataset_name)
            return results
        chi2, p_val, _, _ = stats.chi2_contingency(contingency)
        results.append(
            {
                "dataset_id": dataset_name,
                "test_type": "chi-squared",
                "p_value": p_val,
            }
        )
    else:
        logger.log("no_suitable_columns", dataset=dataset_name)

    return results


def _write_real_pvalues(results: List[Dict[str, Any]]) -> None:
    """
    Write the list of result dictionaries to the canonical CSV location.
    Overwrites any existing file to keep the pipeline deterministic.
    """
    output_path = Path("data/simulation/real_data_pvalues.csv")
    os.makedirs(output_path.parent, exist_ok=True)

    logger.log("real_pvalues_write_start", path=str(output_path), rows=len(results))

    df = pd.DataFrame(results)
    df.to_csv(output_path, index=False)

    logger.log("real_pvalues_write_complete", path=str(output_path), rows=len(df))


def main() -> None:
    """
    Entry point for the validation step (Task T044).

    The function orchestrates:
    1. Downloading the Breast Cancer and Wine datasets via ``ucimlrepo``.
    2. Loading the Adult dataset from OpenML using a chunked approach.
    3. Running a simple statistical test on each dataset.
    4. Persisting the resulting p‑values to disk.
    """
    logger.log("validation_start")

    all_results: List[Dict[str, Any]] = []

    # 1. UCI Breast Cancer (ID 197)
    breast_df = _download_uciml_dataset(197, "Breast Cancer")
    all_results.extend(_run_simple_test(breast_df, "Breast Cancer"))

    # 2. UCI Wine (ID 198)
    wine_df = _download_uciml_dataset(198, "Wine")
    all_results.extend(_run_simple_test(wine_df, "Wine"))

    # 3. OpenML Adult (ID 1590) – loaded chunk‑wise
    adult_df = load_adult_dataset_chunked(max_rows=5_000, chunksize=10_000)
    all_results.extend(_run_simple_test(adult_df, "Adult"))

    # Persist results
    _write_real_pvalues(all_results)

    logger.log("validation_complete", total_results=len(all_results))


if __name__ == "__main__":
    main()
