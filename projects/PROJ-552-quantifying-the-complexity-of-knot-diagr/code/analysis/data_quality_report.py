"""
Data‑quality reporting for the knot dataset.

This module loads the cleaned knot CSV, computes the percentage of null
values for each *required* invariant field, and writes a Markdown report
to ``docs/reproducibility/data_quality_report.md``.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Dict, List

import pandas as pd

from reproducibility.logs import log_operation, get_logger

__all__ = [
    "load_cleaned_knots_data",
    "compute_null_percentages",
    "write_report",
    "main",
]


@log_operation
def load_cleaned_knots_data(csv_path: Path | str = Path("data/processed/knots_cleaned.csv")) -> pd.DataFrame:
    """
    Load the cleaned knot records.

    Parameters
    ----------
    csv_path:
        Path to the cleaned CSV file.  Defaults to the location used by the
        rest of the pipeline.

    Returns
    -------
    pandas.DataFrame
        The dataset, with ``NaN`` representing missing values.
    """
    path = Path(csv_path)
    if not path.is_file():
        raise FileNotFoundError(f"Cleaned knot data not found at {path}")
    df = pd.read_csv(path)
    return df


def _required_fields() -> List[str]:
    """
    Return the list of invariant fields that must be present for the
    analysis.  The list mirrors the fields used elsewhere in the project.
    """
    return [
        "crossing_number",
        "braid_index",
        "volume",
        "alternating",
    ]


@log_operation
def compute_null_percentages(df: pd.DataFrame) -> Dict[str, float]:
    """
    Compute the percentage of null (missing) values for each required field.

    Parameters
    ----------
    df:
        DataFrame containing the cleaned knot records.

    Returns
    -------
    dict
        Mapping from field name to percentage of rows that are null.
    """
    required = _required_fields()
    total = len(df)
    if total == 0:
        raise ValueError("Dataset is empty – cannot compute null percentages.")
    nulls = {}
    for col in required:
        if col not in df.columns:
            raise KeyError(f"Required column '{col}' not found in dataset.")
        null_count = df[col].isna().sum()
        nulls[col] = (null_count / total) * 100.0
    return nulls


@log_operation(output_path_arg="report_path")
def write_report(
    null_percentages: Dict[str, float],
    report_path: Path | str = Path("docs/reproducibility/data_quality_report.md"),
) -> None:
    """
    Write a Markdown table summarising null percentages.

    Parameters
    ----------
    null_percentages:
        Mapping from field name to null percentage.
    report_path:
        Destination Markdown file.
    """
    report_path = Path(report_path)
    report_path.parent.mkdir(parents=True, exist_ok=True)

    lines = [
        "# Data Quality Report",
        "",
        "The table below shows the percentage of missing values for each "
        "required invariant field in the cleaned dataset.",
        "",
        "| Invariant | Null % |",
        "|-----------|--------|",
    ]
    for field, pct in sorted(null_percentages.items()):
        lines.append(f"| {field} | {pct:.2f} |")
    lines.append("")  # final newline

    report_path.write_text("\n".join(lines), encoding="utf-8")
    # Log the creation of the report for reproducibility.
    get_logger().log(
        operation="write_data_quality_report",
        status="success",
        output_file=str(report_path),
    )


@log_operation
def main() -> None:
    """
    End‑to‑end entry point used by the quickstart script.
    """
    df = load_cleaned_knots_data()
    nulls = compute_null_percentages(df)
    write_report(nulls)
