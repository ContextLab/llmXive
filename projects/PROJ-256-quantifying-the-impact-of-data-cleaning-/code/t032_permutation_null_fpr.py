"""
T032 – Permutation Null FPR Estimation

This script generates null datasets by shuffling the outcome variable while
keeping all predictor columns fixed.  For each null dataset it runs the same
baseline statistical analysis used elsewhere in the project and records the
p‑value from the t‑test.  The false‑positive rate (FPR) is then computed as
the proportion of null analyses where the p‑value is ≤ 0.05.

Output
------
data/processed/null_fpr_metrics.json
    {
        "false_positive_rate": 0.123,
        "p_values": [0.23, 0.04, ...],
        "num_datasets": 5
    }
"""

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List

import numpy as np
import pandas as pd

from analysis import run_baseline_analysis
from config import get_config
from utils import setup_logging, pin_random_seed

LOGGER = setup_logging()


def _load_dataset_paths(raw_dir: Path) -> List[Path]:
    """Return a list of CSV files in the raw data directory."""
    if not raw_dir.is_dir():
        LOGGER.error("Raw data directory does not exist: %s", raw_dir)
        return []
    return sorted([p for p in raw_dir.iterdir() if p.suffix.lower() == ".csv"])


def _determine_outcome_and_predictors(df: pd.DataFrame) -> (str, List[str]):
    """
    Heuristic to pick an outcome column:
    * Prefer a column named 'target' or 'y'
    * Otherwise fall back to the first column
    Predictors are all remaining columns.
    """
    possible = [c for c in ["target", "y"] if c in df.columns]
    outcome = possible[0] if possible else df.columns[0]
    predictors = [c for c in df.columns if c != outcome]
    return outcome, predictors


def _shuffle_outcome(df: pd.DataFrame, outcome_col: str) -> pd.DataFrame:
    """Return a copy of ``df`` with the outcome column shuffled."""
    df_null = df.copy()
    shuffled = np.random.permutation(df_null[outcome_col].values)
    df_null[outcome_col] = shuffled
    return df_null


def _run_null_analysis(df: pd.DataFrame, outcome: str, predictors: List[str]) -> Dict[str, Any]:
    """
    Run the baseline analysis on a null dataset.  The ``run_baseline_analysis``
    helper in ``code/analysis.py`` already accepts a dataframe together with
    explicit outcome/predictor arguments, so we forward them.
    """
    try:
        result = run_baseline_analysis(
            dataframe=df,
            outcome=outcome,
            predictors=predictors,
        )
        return result
    except Exception as e:
        LOGGER.exception("Baseline analysis failed on null dataset: %s", e)
        return {}


def main() -> None:
    """
    Entry‑point for the permutation‑null FPR estimation.
    """
    # Ensure reproducibility
    cfg = get_config()
    seed = int(cfg.get("RANDOM_SEED", 42))
    pin_random_seed(seed)

    raw_dir = Path(cfg.get("RAW_DATA_PATH", "data/raw"))
    output_path = Path(cfg.get("PROCESSED_DATA_PATH", "data/processed"))
    output_path.mkdir(parents=True, exist_ok=True)

    dataset_paths = _load_dataset_paths(raw_dir)
    if not dataset_paths:
        LOGGER.warning("No CSV datasets found in %s – nothing to process.", raw_dir)
        return

    p_values: List[float] = []

    for csv_path in dataset_paths:
        LOGGER.info("Processing dataset %s", csv_path.name)
        try:
            df = pd.read_csv(csv_path)
        except Exception as e:
            LOGGER.error("Failed to read %s: %s", csv_path, e)
            continue

        outcome, predictors = _determine_outcome_and_predictors(df)
        df_null = _shuffle_outcome(df, outcome)

        analysis_res = _run_null_analysis(df_null, outcome, predictors)
        if not analysis_res:
            continue

        # Expected schema: {'t_test': {'p_value': ...}, ...}
        t_test = analysis_res.get("t_test", {})
        p_val = t_test.get("p_value")
        if isinstance(p_val, (float, int)):
            p_values.append(float(p_val))
        else:
            LOGGER.warning(
                "Missing or non‑numeric p_value for %s – skipping.", csv_path.name
            )

    # Compute false‑positive rate
    fpr = sum(1 for p in p_values if p <= 0.05) / max(len(p_values), 1)

    result: Dict[str, Any] = {
        "false_positive_rate": round(fpr, 5),
        "p_values": [round(p, 5) for p in p_values],
        "num_datasets": len(p_values),
    }

    output_file = output_path / "null_fpr_metrics.json"
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2)
        LOGGER.info("Null FPR metrics written to %s", output_file)
    except Exception as e:
        LOGGER.error("Failed to write null FPR metrics: %s", e)


if __name__ == "__main__":
    main()
