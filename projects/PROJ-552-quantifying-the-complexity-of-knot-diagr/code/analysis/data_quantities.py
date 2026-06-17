"""
Utilities for loading processed knot data and computing basic data‑quality metrics.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, Any

import pandas as pd

DEFAULT_CLEANED_PATH = Path("data/processed/knots_cleaned.csv")


def load_cleaned_knots_data(data_path: Path | str = DEFAULT_CLEANED_PATH) -> pd.DataFrame:
    """
    Load the cleaned knot dataset.

    Parameters
    ----------
    data_path : Path | str, optional
        Path to the cleaned CSV file. If omitted, the default location
        ``data/processed/knots_cleaned.csv`` is used.

    Returns
    -------
    pd.DataFrame
        DataFrame containing the cleaned knot records.
    """
    path = Path(data_path)
    if not path.is_file():
        raise FileNotFoundError(f"Cleaned knot data not found at {path}")
    return pd.read_csv(path)


def calculate_null_percentages_per_field(df: pd.DataFrame) -> Dict[str, float]:
    """
    Compute the percentage of null values for each column in the DataFrame.

    Parameters
    ----------
    df : pd.DataFrame
        The DataFrame to analyse.

    Returns
    -------
    Dict[str, float]
        Mapping from column name to null‑percentage (0‑100).
    """
    total = len(df)
    return {
        col: (df[col].isna().sum() / total) * 100.0 for col in df.columns
    }


def generate_data_quantities_report(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Produce a simple report summarising the dataset size and null statistics.
    """
    report = {
        "record_count": len(df),
        "null_percentages": calculate_null_percentages_per_field(df),
    }
    return report


def write_data_quantities_report_md(report: Dict[str, Any], output_path: Path | str) -> None:
    """
    Write a markdown report containing basic data‑quantity information.
    """
    out_path = Path(output_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Data Quantities Report",
        "",
        f"- **Total records:** {report['record_count']}",
        "",
        "## Null percentages per field",
    ]
    for col, pct in report["null_percentages"].items():
        lines.append(f"- {col}: {pct:.2f}%")
    out_path.write_text("\n".join(lines))


def main() -> None:
    """
    Entry‑point used by the run‑book. Loads the cleaned data, generates a report,
    and writes the markdown file to the expected location.
    """
    df = load_cleaned_knots_data()
    report = generate_data_quantities_report(df)
    write_data_quantities_report_md(report, Path("docs/reproducibility/data_quantities.md"))


if __name__ == "__main__":
    main()
