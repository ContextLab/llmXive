"""
Data‑quality reporting for the knot dataset.

This module:
* Loads the cleaned knot CSV.
* Computes null‑percentage statistics for the core invariant fields.
* Writes a human‑readable Markdown report to
 ``docs/reproducibility/data_quality_report.md``.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Dict, List

import pandas as pd

from reproducibility.logs import get_logger, log_operation

# ----------------------------------------------------------------------
# Public API – matches the contract declared in ``tasks.md``
# ----------------------------------------------------------------------
def load_cleaned_knots_data() -> pd.DataFrame:
    """
    Load the cleaned knot dataset.

    Returns
    -------
    pandas.DataFrame
        The dataframe read from ``data/processed/knots_cleaned.csv``.
    """
    data_path = Path("data/processed/knots_cleaned.csv")
    if not data_path.is_file():
        raise FileNotFoundError(f"Cleaned data not found at {data_path}")
    return pd.read_csv(data_path)

def compute_null_percentages(df: pd.DataFrame) -> Dict[str, float]:
    """
    Compute the percentage of missing values for each required invariant.

    Parameters
    ----------
    df: pandas.DataFrame
        The cleaned knot dataframe.

    Returns
    -------
    dict
        Mapping from column name to null percentage (0‑100).
    """
    required_fields = [
        "crossing_number",
        "braid_index",
        "hyperbolic_volume",
        "alternating",
    ]
    null_stats: Dict[str, float] = {}
    total = len(df)
    for col in required_fields:
        if col not in df.columns:
            # If a column is missing altogether we treat it as 100 % null.
            null_stats[col] = 100.0
            continue
        null_count = df[col].isna().sum()
        null_stats[col] = (null_count / total) * 100 if total > 0 else 0.0
    return null_stats

def _markdown_report(null_stats: Dict[str, float]) -> str:
    """
    Generate a Markdown report from the null‑percentage statistics.
    """
    lines: List[str] = [
        "# Data‑Quality Report",
        "",
        "This report documents the proportion of missing values for each "
        "required invariant field in the cleaned knot dataset.",
        "",
        "| Invariant | Null % |",
        "|-----------|--------|",
    ]
    for field, pct in sorted(null_stats.items()):
        lines.append(f"| {field} | {pct:.2f} |")
    lines.append("")
    lines.append(
        "*Generated on* "
        f"{datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}"
    )
    return "\n".join(lines)

def write_report(report_md: str, path: Path) -> None:
    """
    Write the Markdown report to *path*.

    Parameters
    ----------
    report_md: str
        The Markdown content.
    path: pathlib.Path
        Destination file path.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(report_md, encoding="utf-8")

@log_operation
def main() -> None:
    """
    Entry point used by the quick‑start pipeline.

    It loads the data, computes null percentages, writes the Markdown
    report, and records a log entry.
    """
    logger = get_logger(__name__)
    logger.log("data_quality_report_start", parameters={})

    df = load_cleaned_knots_data()
    null_stats = compute_null_percentages(df)
    report_md = _markdown_report(null_stats)

    output_path = Path("docs/reproducibility/data_quality_report.md")
    write_report(report_md, output_path)

    logger.log(
        "data_quality_report_complete",
        parameters={"output_path": str(output_path), "null_stats": null_stats},
    )

# Allow ``python -m code.analysis.data_quality_report`` execution
if __name__ == "__main__":
    main()
