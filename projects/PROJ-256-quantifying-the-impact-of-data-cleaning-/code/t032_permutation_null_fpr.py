"""
Permutation Null FPR Generation (Task T032)

This script generates null datasets by shuffling the outcome variable while
keeping predictor variables fixed. For each dataset found in the processed
data directory, it runs the baseline analysis on the permuted data and
records the resulting metrics. The final JSON file is written to
``data/processed/null_fpr_metrics.json`` as required by the project
specifications.

The implementation is deliberately tolerant:
* If a CSV file cannot be read or does not contain at least two columns,
  it is skipped with a warning.
* The outcome column is inferred as the last column in the DataFrame.
* The script uses the flexible ``run_baseline_analysis`` function from
  ``code.analysis`` which accepts a variety of call signatures.
* Logging is set up via the project's ``setup_logging`` utility, which
  tolerates any argument pattern.
"""

import json
import logging
import os
from pathlib import Path
from typing import Dict, Any, List

import numpy as np
import pandas as pd

# Project imports – these exist in the repository according to the API surface.
from analysis import run_baseline_analysis
from utils import setup_logging, pin_random_seed

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
PROCESSED_DATA_DIR = Path("data/processed")
NULL_FPR_OUTPUT = PROCESSED_DATA_DIR / "null_fpr_metrics.json"
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def _load_csv_files(directory: Path) -> List[Path]:
    """Return a list of CSV files in ``directory``."""
    if not directory.is_dir():
        logging.warning("Processed data directory %s does not exist.", directory)
        return []
    return sorted([p for p in directory.iterdir() if p.suffix.lower() == ".csv"])

def _shuffle_outcome(df: pd.DataFrame, outcome_col: str) -> pd.DataFrame:
    """Return a copy of ``df`` with the outcome column shuffled."""
    df_null = df.copy()
    shuffled = np.random.permutation(df_null[outcome_col].values)
    df_null[outcome_col] = shuffled
    return df_null

def _run_analysis_on_null(df: pd.DataFrame, outcome: str, predictors: List[str]) -> Dict[str, Any]:
    """
    Run the project's baseline analysis on a null (shuffled) dataset.

    The ``run_baseline_analysis`` function has a flexible signature; we
    provide the most explicit keyword arguments that are known to work.
    """
    try:
        metrics = run_baseline_analysis(
            dataframe=df,
            outcome=outcome,
            predictors=predictors,
        )
        return metrics
    except Exception as exc:
        logging.error(
            "Baseline analysis failed on null dataset (outcome=%s). Error: %s",
            outcome,
            exc,
        )
        return {}

# ----------------------------------------------------------------------
# Core generation logic
# ----------------------------------------------------------------------
def generate_null_fpr_metrics(
    processed_dir: Path = PROCESSED_DATA_DIR,
    output_path: Path = NULL_FPR_OUTPUT,
) -> None:
    """
    Generate null‑dataset FPR metrics for every CSV file in ``processed_dir``
    and write the aggregated results to ``output_path``.
    """
    logger = logging.getLogger(__name__)
    logger.info("Starting permutation null FPR generation.")
    pin_random_seed(42)  # deterministic shuffling for reproducibility

    csv_files = _load_csv_files(processed_dir)
    if not csv_files:
        logger.warning("No CSV files found in %s; null FPR metrics will be empty.", processed_dir)

    all_metrics: Dict[str, Any] = {}

    for csv_path in csv_files:
        logger.info("Processing file %s", csv_path.name)
        try:
            df = pd.read_csv(csv_path)
        except Exception as exc:
            logger.error("Failed to read %s: %s", csv_path, exc)
            continue

        if df.shape[1] < 2:
            logger.warning(
                "File %s has fewer than 2 columns; cannot determine outcome/predictors. Skipping.",
                csv_path.name,
            )
            continue

        # Infer outcome as the last column, predictors as all others.
        outcome_col = df.columns[-1]
        predictor_cols = list(df.columns[:-1])

        logger.debug(
            "Inferred outcome column '%s' and %d predictor columns.",
            outcome_col,
            len(predictor_cols),
        )

        # Create null dataset by shuffling the outcome.
        df_null = _shuffle_outcome(df, outcome_col)

        # Run analysis on the null dataset.
        metrics = _run_analysis_on_null(df_null, outcome_col, predictor_cols)

        # Store under a key derived from the original filename (without extension).
        dataset_key = csv_path.stem
        all_metrics[dataset_key] = metrics

    # Ensure the output directory exists.
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Write JSON with pretty formatting for readability.
    try:
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(all_metrics, f, indent=2, sort_keys=True)
        logger.info("Null FPR metrics written to %s", output_path)
    except Exception as exc:
        logger.error("Failed to write null FPR metrics to %s: %s", output_path, exc)

# ----------------------------------------------------------------------
# Script entry point
# ----------------------------------------------------------------------
def main() -> None:
    """
    Entry point for ``python code/t032_permutation_null_fpr.py``.
    Sets up logging and triggers the null‑FPR generation.
    """
    # The project's ``setup_logging`` utility tolerates any signature.
    logger = setup_logging(LOG_LEVEL)
    if isinstance(logger, logging.Logger):
        logging.getLogger().setLevel(logger.level)
    generate_null_fpr_metrics()

if __name__ == "__main__":
    main()
