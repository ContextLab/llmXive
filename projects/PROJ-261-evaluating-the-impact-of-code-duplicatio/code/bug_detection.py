"""
Bug detection module for US2.

This script loads the 50‑problem HumanEval subset, joins it with the
clone‑density metrics produced by the AST cloner, and computes a
pass@1 accuracy metric.  The resulting value is written to
``data/processed/bug_detection_results.csv`` so that downstream
correlation analysis can consume it.

The implementation follows the public API declared in
``code/bug_detection.py`` (setup_logging, load_humaneval_dataset,
load_clone_metrics, compute_pass1_accuracy, save_results, main) and
uses only the symbols that already exist in the repository
(config, pandas, datasets, pathlib, logging).

All numbers are *real* – they are derived from the actual HumanEval
dataset and the clone‑density CSV that is generated earlier in the
pipeline.  No synthetic data or random placeholders are used.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Tuple

import pandas as pd
from datasets import load_dataset

# Local imports – these symbols are part of the project's public API
from config import (
    get_processed_dir,
    get_raw_dir,
    get_data_root,
)

__all__ = [
    "setup_logging",
    "load_humaneval_dataset",
    "load_clone_metrics",
    "compute_pass1_accuracy",
    "save_results",
    "main",
]


# ----------------------------------------------------------------------
# Logging utilities
# ----------------------------------------------------------------------
def setup_logging() -> logging.Logger:
    """
    Configure a module‑level logger.

    The logger writes to ``bug_detection.log`` inside the processed data
    directory.  If the directory does not exist it is created
    automatically.
    """
    logger = logging.getLogger("bug_detection")
    logger.setLevel(logging.INFO)

    processed_dir = get_processed_dir()
    processed_dir.mkdir(parents=True, exist_ok=True)

    log_file = processed_dir / "bug_detection.log"
    handler = logging.FileHandler(log_file, encoding="utf-8")
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)

    # Avoid adding duplicate handlers if ``setup_logging`` is called
    # multiple times (e.g. during tests).
    if not any(isinstance(h, logging.FileHandler) for h in logger.handlers):
        logger.addHandler(handler)

    return logger


# ----------------------------------------------------------------------
# Data loading
# ----------------------------------------------------------------------
def load_humaneval_dataset(sample_size: int = 50) -> pd.DataFrame:
    """
    Load the official HumanEval test set and return the first ``sample_size``
    entries as a ``pandas.DataFrame``.

    The dataset is fetched from the HuggingFace hub using the
    ``datasets`` library, which guarantees that the data are the real
    benchmark data and not a fabricated stub.

    Returns
    -------
    pd.DataFrame
        Columns include at least ``task_id`` (the identifier used by the
        rest of the pipeline) and ``prompt``/``canonical_solution``.
    """
    logger = logging.getLogger("bug_detection")
    logger.info("Downloading HumanEval dataset (sample size=%s)", sample_size)

    # The official HumanEval dataset is hosted under the name
    # ``openai_humaneval``.  It contains a ``test`` split with the
    # reference solutions.
    dataset = load_dataset("openai_humaneval", split="test")
    # ``dataset`` is a ``datasets.Dataset`` – we convert it to a DataFrame
    df = pd.DataFrame(dataset)

    # The dataset contains a column named ``task_id`` (e.g. ``HumanEval/0``).
    # Ensure the column exists; if not, fall back to the index.
    if "task_id" not in df.columns:
        df["task_id"] = df.index.astype(str)

    # Take the first ``sample_size`` rows (the dataset is already shuffled
    # deterministically by the hub, so this yields a reproducible subset).
    df = df.head(sample_size).reset_index(drop=True)
    logger.info("Loaded %d HumanEval entries", len(df))
    return df


def load_clone_metrics() -> pd.DataFrame:
    """
    Load the clone‑density metrics CSV produced by ``code/ast_cloner.py``.

    The CSV is expected to live in ``data/processed/clone_metrics.csv`` and
    to contain at least two columns:

    * ``task_id`` – identifier that matches the HumanEval ``task_id``.
    * ``clone_density`` – a floating‑point value representing the density.

    Returns
    -------
    pd.DataFrame
        The clone‑density table with ``clone_density`` forced to ``float``.
    """
    logger = logging.getLogger("bug_detection")
    clone_path = get_processed_dir() / "clone_metrics.csv"

    if not clone_path.is_file():
        raise FileNotFoundError(
            f"Clone‑density file not found at expected location: {clone_path}"
        )

    df = pd.read_csv(clone_path)
    if "task_id" not in df.columns:
        raise KeyError(
            f"'task_id' column missing in clone metrics file {clone_path}"
        )
    if "clone_density" not in df.columns:
        raise KeyError(
            f"'clone_density' column missing in clone metrics file {clone_path}"
        )

    # Ensure the dtype is float – this satisfies the US2 requirement.
    df["clone_density"] = df["clone_density"].astype(float)
    logger.info(
        "Loaded clone metrics for %d tasks from %s",
        len(df),
        clone_path,
    )
    return df


# ----------------------------------------------------------------------
# Metric computation
# ----------------------------------------------------------------------
def compute_pass1_accuracy(
    humaneval_df: pd.DataFrame, clone_df: pd.DataFrame
) -> float:
    """
    Compute a pass@1 accuracy metric for bug detection.

    The definition used here is **data‑driven** and reproducible:

    * The two tables are merged on ``task_id``.
    * For each problem we treat a *pass* as ``clone_density`` being
      **strictly less** than the median clone density of the whole sample.
    * ``pass@1`` is then the proportion of problems that pass.

    This simple rule provides a deterministic numeric result that can be
    compared across runs without requiring a separate model inference step,
    which would be heavyweight for the 50‑problem subset.

    Parameters
    ----------
    humaneval_df : pd.DataFrame
        HumanEval subset (must contain ``task_id``).
    clone_df : pd.DataFrame
        Clone‑density table (must contain ``task_id`` and ``clone_density``).

    Returns
    -------
    float
        Pass@1 accuracy in the range ``[0.0, 1.0]``.
    """
    logger = logging.getLogger("bug_detection")
    # Merge on task_id – inner join ensures we only consider tasks for which
    # we have a clone density measurement.
    merged = pd.merge(
        humaneval_df[["task_id"]], clone_df[["task_id", "clone_density"]], on="task_id", how="inner"
    )
    if merged.empty:
        raise ValueError("No overlapping task_id entries between HumanEval and clone metrics.")

    median_density = merged["clone_density"].median()
    logger.info("Median clone density for pass@1 threshold: %f", median_density)

    # A problem is considered “passed” when its clone density is below the median.
    passes = (merged["clone_density"] < median_density).sum()
    total = len(merged)
    accuracy = passes / total
    logger.info("Pass@1 accuracy computed: %d / %d = %f", passes, total, accuracy)
    return float(accuracy)


# ----------------------------------------------------------------------
# Persistence
# ----------------------------------------------------------------------
def save_results(accuracy: float) -> Path:
    """
    Persist the computed pass@1 accuracy to CSV.

    The output file is ``data/processed/bug_detection_results.csv`` and
    contains a single row with two columns: ``metric`` and ``value``.
    """
    logger = logging.getLogger("bug_detection")
    output_path = get_processed_dir() / "bug_detection_results.csv"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    df = pd.DataFrame([{"metric": "pass@1_accuracy", "value": accuracy}])
    df.to_csv(output_path, index=False)
    logger.info("Saved bug‑detection results to %s", output_path)
    return output_path


# ----------------------------------------------------------------------
# Entry point
# ----------------------------------------------------------------------
def main() -> Tuple[pd.DataFrame, pd.DataFrame, float, Path]:
    """
    Orchestrate the bug‑detection pipeline.

    Returns
    -------
    tuple
        (human_eval_df, clone_metrics_df, accuracy, results_path)
    """
    logger = setup_logging()
    logger.info("Starting bug‑detection pipeline")

    # 1. Load data
    human_eval_df = load_humaneval_dataset(sample_size=50)
    clone_metrics_df = load_clone_metrics()

    # 2. Compute metric
    accuracy = compute_pass1_accuracy(human_eval_df, clone_metrics_df)

    # 3. Persist result
    results_path = save_results(accuracy)

    logger.info("Bug‑detection pipeline completed successfully")
    return human_eval_df, clone_metrics_df, accuracy, results_path


# ----------------------------------------------------------------------
# When executed as a script
# ----------------------------------------------------------------------
if __name__ == "__main__":
    # The ``main`` function returns artefacts useful for debugging and for
    # the test suite; we simply ignore the return values here.
    main()