"""
T003 – Apply strict‑tolerance outlier rule (FR‑004) to the sweep results.

This script reads ``data/processed/mc_results.csv`` (produced by the theta sweep),
recomputes the outlier flag using the rule

    outlier_flag = eigenvalue_top > empirical_bulk_edge + 0.05

and writes a new CSV file ``data/processed/validated_sweep_results.csv`` that
contains all original columns plus the freshly computed ``outlier_flag`` column.

The script can be run directly:

    python code/analysis/apply_outlier_rule.py

or with explicit paths:

    python code/analysis/apply_outlier_rule.py --input path/to/mc_results.csv \\
                                              --output path/to/validated.csv
"""

import argparse
import logging
import sys
from pathlib import Path

import pandas as pd

# Project utilities – they are part of the repository and expose the canonical
# data directory locations.
from utils.config import get_project_paths, ensure_directories

__all__ = ["apply_outlier_rule", "main"]


def _setup_logging() -> logging.Logger:
    """Configure a simple console logger."""
    logger = logging.getLogger("apply_outlier_rule")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(
            logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        )
        logger.addHandler(handler)
    return logger


def apply_outlier_rule(
    input_csv: Path, output_csv: Path, logger: logging.Logger | None = None
) -> None:
    """
    Apply FR‑004 to ``input_csv`` and write the enriched table to ``output_csv``.

    Parameters
    ----------
    input_csv: Path
        Path to the original ``mc_results.csv`` produced by the sweep.
    output_csv: Path
        Destination path for the validated CSV (must include the filename).
    logger: optional Logger
        If supplied, progress messages are emitted; otherwise a default logger is used.
    """
    if logger is None:
        logger = _setup_logging()

    logger.info(f"Reading sweep results from {input_csv}")
    df = pd.read_csv(input_csv)

    # Verify required columns exist – this will raise a clear error if the file
    # is malformed, satisfying the “fail loudly” policy.
    required = {"eigenvalue_top", "empirical_bulk_edge"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(
            f"Input CSV is missing required columns for outlier detection: {missing}"
        )

    logger.info("Computing outlier_flag using strict tolerance (value > edge + 0.05)")
    df["outlier_flag"] = df["eigenvalue_top"] > (df["empirical_bulk_edge"] + 0.05)

    # Ensure the output directory exists.
    output_csv.parent.mkdir(parents=True, exist_ok=True)

    logger.info(f"Writing validated results to {output_csv}")
    df.to_csv(output_csv, index=False)
    logger.info("Done.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Re‑compute outlier flags for the theta sweep (FR‑004)."
    )
    parser.add_argument(
        "--input",
        type=str,
        default=None,
        help="Path to mc_results.csv (default: project processed/mc_results.csv).",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Path for validated_sweep_results.csv "
        "(default: project processed/validated_sweep_results.csv).",
    )
    return parser.parse_args()


def main() -> int:
    logger = _setup_logging()
    # Ensure the standard project directories exist (processed, logs, …)
    ensure_directories()

    paths = get_project_paths()
    args = parse_args()

    input_path = (
        Path(args.input)
        if args.input
        else paths["processed"] / "mc_results.csv"
    )
    output_path = (
        Path(args.output)
        if args.output
        else paths["processed"] / "validated_sweep_results.csv"
    )

    try:
        apply_outlier_rule(input_path, output_path, logger)
        return 0
    except Exception as exc:  # pragma: no cover – caught by the runtime
        logger.error(f"Failed to apply outlier rule: {exc}", exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
