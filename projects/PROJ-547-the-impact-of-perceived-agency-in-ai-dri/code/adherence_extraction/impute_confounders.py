"""
Imputation script for confounder variables in the adherence extraction pipeline.

This script reads a CSV file containing adherence metrics (which may include
missing confounder columns), attempts to impute missing values using
``sklearn.impute.IterativeImputer`` (with a maximum of 5 iterations), and
falls back to a complete‑case analysis if imputation fails.  In both cases a
bias‑assessment report is generated to document how the data changed during
processing.

The script follows the project's logging conventions by using the
``pipeline_logger`` utilities.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Union

import pandas as pd
from sklearn.experimental import enable_iterative_imputer  # noqa: F401
from sklearn.impute import IterativeImputer

from logging.pipeline_logger import get_logger, log_dict

__all__ = ["impute_confounders", "main"]


def _generate_bias_report(
    original_df: pd.DataFrame,
    processed_df: pd.DataFrame,
    method: str,
    rows_before: int,
    rows_after: int,
) -> dict:
    """
    Create a simple bias‑assessment report.

    The report contains:
      * the method used (iterative imputer or complete‑case),
      * row counts before/after processing,
      * mean differences for each numeric column (imputed vs original).

    Returns a dictionary ready to be JSON‑encoded.
    """
    # Compute mean differences only for numeric columns
    numeric_cols = original_df.select_dtypes(include=["number"]).columns
    mean_original = original_df[numeric_cols].mean()
    mean_processed = processed_df[numeric_cols].mean()
    mean_diff = (mean_processed - mean_original).to_dict()

    report = {
        "method": method,
        "rows_before": rows_before,
        "rows_after": rows_after,
        "mean_difference": mean_diff,
    }
    return report


def impute_confounders(
    input_path: Union[str, Path],
    output_path: Union[str, Path],
    bias_report_path: Union[str, Path],
) -> None:
    """
    Impute missing confounder values in ``input_path`` and write results.

    Parameters
    ----------
    input_path: Path or str
        CSV file containing the adherence metrics with possible missing values.
    output_path: Path or str
        Destination CSV file for the imputed (or complete‑case) dataset.
    bias_report_path: Path or str
        Path to a JSON file that records the bias‑assessment report.
    """
    logger = get_logger(__name__)
    logger.info("Starting confounder imputation")
    log_dict(logger, {"input_path": str(input_path), "output_path": str(output_path)})

    input_path = Path(input_path)
    output_path = Path(output_path)
    bias_report_path = Path(bias_report_path)

    # Load data
    df = pd.read_csv(input_path)
    rows_before = len(df)

    # Identify columns with missing data
    missing_cols = df.columns[df.isnull().any()].tolist()
    if not missing_cols:
        logger.info("No missing values detected – copying input to output unchanged")
        df.to_csv(output_path, index=False)
        report = _generate_bias_report(df, df, "none_needed", rows_before, rows_before)
        bias_report_path.write_text(json.dumps(report, indent=2))
        log_dict(logger, {"bias_report": report})
        return

    # Attempt iterative imputation
    try:
        logger.info("Attempting IterativeImputer")
        imputer = IterativeImputer(max_iter=5, random_state=0)
        imputed_array = imputer.fit_transform(df)
        imputed_df = pd.DataFrame(imputed_array, columns=df.columns)
        method_used = "iterative_imputer"
    except Exception as exc:  # pragma: no cover – defensive fallback
        logger.warning(
            "IterativeImputer failed ( %s ). Falling back to complete‑case analysis.",
            exc,
        )
        imputed_df = df.dropna()
        method_used = "complete_case"

    rows_after = len(imputed_df)

    # Write imputed dataset
    imputed_df.to_csv(output_path, index=False)
    logger.info("Imputed data written", extra={"output_path": str(output_path)})

    # Build and write bias report
    report = _generate_bias_report(
        original_df=df,
        processed_df=imputed_df,
        method=method_used,
        rows_before=rows_before,
        rows_after=rows_after,
    )
    bias_report_path.write_text(json.dumps(report, indent=2))
    logger.info("Bias assessment report written", extra={"bias_report_path": str(bias_report_path)})
    log_dict(logger, {"bias_report": report})


def _build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Impute missing confounder columns for adherence metrics."
    )
    parser.add_argument(
        "-i",
        "--input",
        required=True,
        type=Path,
        help="Path to the CSV file containing raw adherence metrics (may have missing values).",
    )
    parser.add_argument(
        "-o",
        "--output",
        required=True,
        type=Path,
        help="Path where the imputed CSV will be saved.",
    )
    parser.add_argument(
        "-b",
        "--bias-report",
        required=True,
        type=Path,
        help="Path to a JSON file that will contain the bias‑assessment report.",
    )
    return parser


def main() -> None:  # pragma: no cover
    """
    Command‑line entry point.

    Example
    -------
    python -m adherence_extraction.impute_confounders \\
        -i data/processed/adherence_metrics.csv \\
        -o data/processed/adherence_metrics_imputed.csv \\
        -b data/processed/imputation_bias_report.json
    """
    parser = _build_arg_parser()
    args = parser.parse_args()
    impute_confounders(args.input, args.output, args.bias_report)


if __name__ == "__main__":  # pragma: no cover
    main()