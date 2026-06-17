"""Validate that all required fields are present in the cleaned dataset."""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from reproducibility.logs import log_operation, get_logger
from analysis.data_quantities import load_cleaned_knots_data


REQUIRED_FIELDS = {
    "name",
    "crossing_number",
    "braid_index",
    "volume",
    "alternating",
}


def generate_report() -> dict:
    logger = get_logger()
    logger.info("Generating completeness validation report")
    df = load_cleaned_knots_data()
    missing = {field for field in REQUIRED_FIELDS if field not in df.columns}
    report = {
        "total_records": len(df),
        "missing_fields": list(missing),
        "all_fields_present": len(missing) == 0,
    }
    out_path = Path("docs/reproducibility/completeness_report.json")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(report, indent=2))
    logger.info(f"Completeness report written to {out_path}")
    return report


def main() -> None:
    generate_report()


if __name__ == "__main__":
    main()