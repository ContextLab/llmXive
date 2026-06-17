"""
Validation of dataset completeness.

The module now imports the corrected ``log_operation`` decorator which
supplies a default ``operation_name``.
"""

import json
from pathlib import Path

import pandas as pd
from reproducibility.logs import log_operation, get_logger
from analysis.data_quantities import load_cleaned_knots_data

@log_operation(operation_name="generate_report", output_path_arg="output_path")
def generate_report(output_path: Path) -> None:
    """
    Generate a JSON report summarising the number of records and missing fields.
    """
    df = load_cleaned_knots_data()
    report = {
        "total_records": len(df),
        "missing_per_field": {col: int(df[col].isna().sum()) for col in df.columns},
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

def main() -> None:
    logger = get_logger(__name__)  # type: ignore[arg-type]
    report_path = Path("data/validation/completeness_report.json")
    generate_report(report_path)
    logger.info(f"Completeness report written to {report_path}")

if __name__ == "__main__":
    main()