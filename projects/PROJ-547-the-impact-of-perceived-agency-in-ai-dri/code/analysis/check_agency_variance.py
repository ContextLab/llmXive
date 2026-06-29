"""Check variance of agency scores before regression.

This script reads a CSV file containing an ``agency_score`` column,
computes the variance of the scores, logs the result, and aborts the
pipeline with a logged error if the variance is below a configurable
threshold (default ``1e-6``).

It is intended to be run as a preprocessing guard before any regression
analysis (US3). The abort is performed by raising a ``PipelineError``
which is caught in ``main`` and logged via ``log_and_exit`` to ensure a
non‑zero exit status.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from logging.pipeline_logger import get_logger, log_dict
from utils.error_handler import PipelineError, log_and_exit


def check_variance(scores_path: Path, threshold: float = 1e-6) -> None:
    """Validate variance of the ``agency_score`` column.

    Args:
        scores_path: Path to the CSV file produced by the agency‑scoring
            pipeline (``data/processed/agency_scores.csv``).
        threshold: Minimum acceptable variance. If the observed variance is
            strictly less than this value, a ``PipelineError`` is raised.

    Raises:
        PipelineError: If the file does not exist, the required column is
            missing, or the variance is below ``threshold``.
    """
    logger = get_logger(__name__)

    if not scores_path.is_file():
        logger.error(f"Agency scores file not found: {scores_path}")
        raise PipelineError(f"File not found: {scores_path}")

    # Load scores
    df = pd.read_csv(scores_path)

    if "agency_score" not in df.columns:
        logger.error("Column 'agency_score' missing from input data.")
        raise PipelineError("Missing 'agency_score' column.")

    # Compute variance (pandas uses unbiased estimator by default)
    variance = df["agency_score"].var()
    log_dict(logger, {"agency_score_variance": variance})

    if variance < threshold:
        logger.error(
            f"Zero‑variance detected (variance={variance:.2e}) "
            f"below threshold {threshold:.2e}."
        )
        raise PipelineError(
            f"Variance {variance:.2e} below acceptable threshold {threshold:.2e}."
        )
    else:
        logger.info(f"Agency score variance OK: {variance:.6f}")


def main() -> None:
    """Entry point for command‑line execution."""
    parser = argparse.ArgumentParser(
        description="Detect zero‑variance agency scores before regression."
    )
    parser.add_argument(
        "scores_path",
        type=Path,
        help="Path to the agency scores CSV (e.g., data/processed/agency_scores.csv).",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=1e-6,
        help="Minimum acceptable variance (default: 1e-6).",
    )
    args = parser.parse_args()

    try:
        check_variance(args.scores_path, threshold=args.threshold)
    except PipelineError as exc:
        # Ensure the error is logged and the process exits with a non‑zero code.
        log_and_exit(str(exc), exit_code=1)


if __name__ == "__main__":
    main()
