"""
t032_permutation_null_fpr.py

Implements permutation-based null dataset generation for false‑positive rate (FPR)
estimation as required by task T032.

The script:
1. Scans ``data/raw`` for CSV files.
2. For each dataset it shuffles the outcome column (preserving predictor columns).
3. Runs the baseline analysis on the shuffled dataset using the existing
   ``run_baseline_analysis`` function.
4. Extracts all p‑values from the returned metrics and computes the proportion
   that are ≤ 0.05 (the false‑positive rate) for that dataset.
5. Aggregates per‑dataset FPRs and writes a summary JSON file to
   ``data/processed/null_fpr_metrics.json``.

The script can be executed directly:

    python code/t032_permutation_null_fpr.py

It will also be imported by other pipeline components if needed.
"""

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List

import numpy as np
import pandas as pd

# Import the flexible ``setup_logging`` defined in utils (it now accepts
# a variety of call signatures).
from utils import setup_logging

# ``run_baseline_analysis`` is the central analysis routine.  It already
# supports a flexible signature (dataframe, outcome, predictors, raw_dir,
# output_file, …) – we only need the dataframe form here.
from analysis import run_baseline_analysis

LOGGER = setup_logging(log_level="INFO")


def _identify_outcome_column(df: pd.DataFrame) -> str:
    """
    Heuristically pick an outcome/target column.

    Preference order:
    1. Column named exactly ``outcome`` or ``target`` (case‑insensitive).
    2. The first column if it is numeric or categorical.
    3. Raise ``ValueError`` if the DataFrame is empty.
    """
    if df.empty:
        raise ValueError("DataFrame is empty – cannot identify outcome column.")

    lower_cols = [c.lower() for c in df.columns]
    for name in ("outcome", "target", "y"):
        if name in lower_cols:
            return df.columns[lower_cols.index(name)]

    # Fallback to first column
    return df.columns[0]


def _shuffle_outcome(df: pd.DataFrame, outcome_col: str, rng: np.random.Generator) -> pd.DataFrame:
    """
    Return a new DataFrame where ``outcome_col`` has been permuted
    uniformly at random while all other columns remain unchanged.
    """
    shuffled = df[outcome_col].sample(frac=1, random_state=rng.integers(0, 2**32 - 1)).reset_index(drop=True)
    df_null = df.copy()
    df_null[outcome_col] = shuffled
    return df_null


def _extract_p_values(metrics: Dict[str, Any]) -> List[float]:
    """
    Recursively walk through the ``metrics`` dictionary and collect any
    numeric values that look like p‑values (i.e. keys containing ``p`` or
    ``p_value`` and values in the interval [0, 1]).
    """
    p_vals: List[float] = []

    def _walk(obj: Any):
        if isinstance(obj, dict):
            for k, v in obj.items():
                if isinstance(v, (float, int)) and "p" in k.lower():
                    # Guard against nonsensical values outside [0, 1]
                    if 0.0 <= float(v) <= 1.0:
                        p_vals.append(float(v))
                else:
                    _walk(v)
        elif isinstance(obj, list):
            for item in obj:
                _walk(item)

    _walk(metrics)
    return p_vals


def generate_null_fpr_metrics(
    raw_dir: Path = Path("data/raw"),
    output_file: Path = Path("data/processed/null_fpr_metrics.json"),
    significance_level: float = 0.05,
    random_seed: int = 42,
) -> Dict[str, Any]:
    """
    Generate null datasets by shuffling the outcome variable, run the baseline
    analysis on each, and compute the false‑positive rate (FPR).

    Parameters
    ----------
    raw_dir: Path
        Directory containing raw CSV datasets.
    output_file: Path
        Destination JSON file for the FPR results.
    significance_level: float
        Threshold for counting a p‑value as a false positive (default 0.05).
    random_seed: int
        Seed for reproducibility of the permutations.

    Returns
    -------
    dict
        Structure similar to::

            {
                "per_dataset": {
                    "dataset1.csv": {"fpr": 0.12, "num_tests": 5, "num_significant": 1},
                    "dataset2.csv": {"fpr": 0.20, "num_tests": 5, "num_significant": 1}
                },
                "overall_fpr": 0.16,
                "total_tests": 10,
                "total_significant": 2
            }
    """
    rng = np.random.default_rng(random_seed)

    if not raw_dir.exists():
        LOGGER.error("Raw data directory %s does not exist.", raw_dir)
        raise FileNotFoundError(f"Raw data directory {raw_dir} not found.")

    # Ensure the output parent directory exists
    output_file.parent.mkdir(parents=True, exist_ok=True)

    per_dataset: Dict[str, Dict[str, Any]] = {}
    total_tests = 0
    total_significant = 0

    csv_files = list(raw_dir.glob("*.csv"))
    if not csv_files:
        LOGGER.warning("No CSV files found in %s – null FPR metrics will be empty.", raw_dir)

    for csv_path in csv_files:
        try:
            df = pd.read_csv(csv_path)
            outcome_col = _identify_outcome_column(df)
            df_null = _shuffle_outcome(df, outcome_col, rng)

            # Run baseline analysis on the permuted dataset.
            # ``run_baseline_analysis`` returns a dict of metrics.
            metrics = run_baseline_analysis(dataframe=df_null)

            p_vals = _extract_p_values(metrics)
            num_tests = len(p_vals)
            num_significant = sum(p <= significance_level for p in p_vals)

            fpr = (num_significant / num_tests) if num_tests > 0 else 0.0

            per_dataset[csv_path.name] = {
                "fpr": round(fpr, 4),
                "num_tests": num_tests,
                "num_significant": num_significant,
            }

            total_tests += num_tests
            total_significant += num_significant

            LOGGER.info(
                "Processed null dataset %s – %d tests, %d significant (FPR=%.4f)",
                csv_path.name,
                num_tests,
                num_significant,
                fpr,
            )
        except Exception as exc:
            LOGGER.exception("Failed to process %s: %s", csv_path.name, exc)

    overall_fpr = (total_significant / total_tests) if total_tests > 0 else 0.0

    result = {
        "per_dataset": per_dataset,
        "overall_fpr": round(overall_fpr, 4),
        "total_tests": total_tests,
        "total_significant": total_significant,
    }

    # Write the JSON file
    with output_file.open("w", encoding="utf-8") as fp:
        json.dump(result, fp, indent=2)

    LOGGER.info("Null‑FPR metrics written to %s", output_file)
    return result


def main() -> None:
    """
    Entry‑point used by the quick‑start run‑book.  It simply forwards to
    ``generate_null_fpr_metrics`` with the default paths.
    """
    try:
        generate_null_fpr_metrics()
    except Exception as exc:
        LOGGER.error("Permutation null‑FPR generation failed: %s", exc)
        raise


if __name__ == "__main__":
    main()