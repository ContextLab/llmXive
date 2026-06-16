"""
validate_completeness.py

Checks that the cleaned knot dataset contains all required fields and that
no rows are completely empty.  A short Markdown report is written to
``docs/reproducibility/validation_status.md``.
"""

import json
from pathlib import Path

import pandas as pd

from reproducibility.logs import log_operation, get_logger
from analysis.data_quantities import load_cleaned_knots_data

REPORT_PATH = Path("docs/reproducibility/validation_status.md")


def _check_required_fields(df: pd.DataFrame) -> dict:
    """Return a dict mapping field names to the number of missing values."""
    required = [
        "knot_id",
        "crossing_number",
        "braid_index",
        "hyperbolic_volume",
        "alternating",
    ]
    missing = {col: int(df[col].isna().sum()) for col in required if col in df.columns}
    # Include any required columns that are altogether absent.
    absent = [col for col in required if col not in df.columns]
    for col in absent:
        missing[col] = "absent"
    return missing


def generate_report(missing_counts: dict) -> str:
    """Create a simple Markdown report."""
    lines = ["# Validation Status", "", "## Missing / Absent Fields", ""]
    if not missing_counts:
        lines.append("All required fields are present with no missing values.")
    else:
        for field, count in missing_counts.items():
            lines.append(f"- **{field}**: {count}")
    lines.append("")
    lines.append("## Overall Row Completeness")
    total_rows = len(df)
    empty_rows = df.isna().all(axis=1).sum()
    lines.append(f"- Total rows: {total_rows}")
    lines.append(f"- Fully empty rows: {empty_rows}")
    return "\n".join(lines)


def main() -> None:
    logger = get_logger()
    log_operation(operation="validate_completeness_start", logger=logger)

    df = load_cleaned_knots_data()
    missing_counts = _check_required_fields(df)
    report_md = generate_report(missing_counts)

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(report_md, encoding="utf-8")

    log_operation(
        operation="validate_completeness_complete",
        output_file=str(REPORT_PATH),
        status="success",
        logger=logger,
    )


if __name__ == "__main__":
    main()
