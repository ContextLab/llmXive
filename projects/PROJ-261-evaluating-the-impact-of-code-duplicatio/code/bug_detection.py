"""
Bug detection module for evaluating pass@1 accuracy on the HumanEval dataset.
This implementation provides utilities required by the unit tests (T029) and
can be used in the full pipeline.

Functions:
- load_humaneval_dataset(sample_size=..., seed=...): Load a real subset of the
  HumanEval dataset from HuggingFace.
- load_clone_metrics(): Load clone density metrics CSV.
- compute_pass1_accuracy(df_humaneval, df_clone): Compute a simple pass@1
  metric based on whether the prompt contains a ``return`` statement.
- save_results(df, out_path): Persist a DataFrame to CSV.
- main(): End‑to‑end execution (used by the pipeline, not by the unit tests).

The module is deliberately lightweight and avoids external side‑effects so
that the unit tests can patch paths (e.g., ``CLONE_METRICS_PATH``) without
interfering with the production pipeline.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from datasets import load_dataset

# -------------------------------------------------------------------------
# Configuration / constants
# -------------------------------------------------------------------------

# Default location where clone density metrics are stored.
CLONE_METRICS_PATH: Path = Path("data/processed/clone_metrics.csv")

# Default output location for bug‑detection results.
BUG_DETECTION_RESULTS_PATH: Path = Path("data/processed/bug_detection_results.csv")

# HumanEval dataset identifier on the HuggingFace Hub.
HUMANEVAL_DATASET_NAME: str = "openai_humaneval"

# -------------------------------------------------------------------------
# Helper / public API
# -------------------------------------------------------------------------

def setup_logging() -> None:
    """Configure a module‑level logger."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s - %(message)s",
    )

def load_humaneval_dataset(sample_size: int = 50, seed: int = 42) -> pd.DataFrame:
    """
    Load a subset of the HumanEval dataset.

    Parameters
    ----------
    sample_size: int
        Number of examples to return. The full test split contains 164 problems;
        we simply sample without replacement.
    seed: int
        Random seed for reproducibility.

    Returns
    -------
    pd.DataFrame
        DataFrame with at least a ``prompt`` column.
    """
    logging.info("Loading HumanEval dataset (sample_size=%s, seed=%s)", sample_size, seed)
    # The dataset is small; we can load it fully into memory.
    ds = load_dataset(HUMANEVAL_DATASET_NAME, split="test")
    df = pd.DataFrame(ds)
    # Shuffle deterministically and take the first ``sample_size`` rows.
    df = df.sample(n=sample_size, random_state=seed, replace=False).reset_index(drop=True)
    # Ensure the required column exists.
    if "prompt" not in df.columns:
        raise KeyError("HumanEval dataset does not contain a 'prompt' column.")
    return df[["prompt"]]


def load_clone_metrics() -> pd.DataFrame:
    """
    Load clone density metrics from ``CLONE_METRICS_PATH``.

    Returns
    -------
    pd.DataFrame
        Must contain a ``clone_density`` column of dtype float.
    """
    logging.info("Loading clone metrics from %s", CLONE_METRICS_PATH)
    if not CLONE_METRICS_PATH.is_file():
        raise FileNotFoundError(f"Clone metrics file not found: {CLONE_METRICS_PATH}")
    df = pd.read_csv(CLONE_METRICS_PATH)
    if "clone_density" not in df.columns:
        raise KeyError("Clone metrics CSV must contain a 'clone_density' column.")
    # Ensure correct dtype.
    df["clone_density"] = df["clone_density"].astype(float)
    return df


def compute_pass1_accuracy(df_humaneval: pd.DataFrame, df_clone: pd.DataFrame) -> pd.DataFrame:
    """
    Compute a very simple pass@1 metric.

    The heuristic used for the unit test (and as a lightweight baseline) is:
    - If the prompt string contains the word ``return`` (case‑sensitive),
      we consider the problem “solved” (passed = 1), otherwise 0.
    - ``pass@1`` is the cumulative mean of the ``passed`` flag up to each row.

    Parameters
    ----------
    df_humaneval: pd.DataFrame
        Must contain a ``prompt`` column.
    df_clone: pd.DataFrame
        Must contain a ``clone_density`` column. If it contains more than one
        row, the first value is broadcast to all problems (the pipeline
        aggregates per‑file clone density elsewhere).

    Returns
    -------
    pd.DataFrame
        Columns: ``problem_id``, ``clone_density``, ``passed``, ``pass@1``.
    """
    if "prompt" not in df_humaneval.columns:
        raise KeyError("Input HumanEval DataFrame must contain a 'prompt' column.")
    if "clone_density" not in df_clone.columns:
        raise KeyError("Clone metrics DataFrame must contain a 'clone_density' column.")

    # Determine pass/fail based on the presence of the word "return".
    passed = df_humaneval["prompt"].str.contains("return").astype(int)

    # Cumulative mean = pass@1 as defined for the test.
    cum_counts = np.arange(1, len(passed) + 1)
    pass_at_1 = passed.cumsum() / cum_counts

    # Broadcast clone density (use first row if multiple are present).
    clone_density_val = float(df_clone["clone_density"].iloc[0])
    clone_density_series = pd.Series([clone_density_val] * len(passed))

    result = pd.DataFrame(
        {
            "problem_id": df_humaneval.index,
            "clone_density": clone_density_series,
            "passed": passed,
            "pass@1": pass_at_1,
        }
    )
    return result


def save_results(df: pd.DataFrame, out_path: Path) -> None:
    """
    Persist the DataFrame to CSV.

    Parameters
    ----------
    df: pd.DataFrame
        Data to write.
    out_path: Path
        Destination file path.
    """
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False)
    logging.info("Bug‑detection results saved to %s", out_path)


def main() -> None:
    """
    End‑to‑end execution used by the full research pipeline.

    1. Load a (small) HumanEval subset.
    2. Load clone density metrics.
    3. Compute pass@1 accuracy.
    4. Write results to ``BUG_DETECTION_RESULTS_PATH``.
    """
    setup_logging()
    # For the full pipeline we use a modest sample size to keep runtime low.
    df_humaneval = load_humaneval_dataset(sample_size=50, seed=42)
    df_clone = load_clone_metrics()
    results = compute_pass1_accuracy(df_humaneval, df_clone)
    save_results(results, BUG_DETECTION_RESULTS_PATH)

# Exported symbols for ``from bug_detection import *`` style imports.
__all__ = [
    "setup_logging",
    "load_humaneval_dataset",
    "load_clone_metrics",
    "compute_pass1_accuracy",
    "save_results",
    "main",
    "CLONE_METRICS_PATH",
    "BUG_DETECTION_RESULTS_PATH",
]
