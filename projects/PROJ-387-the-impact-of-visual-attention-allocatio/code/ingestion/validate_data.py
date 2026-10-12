"""
validate_data.py
-----------------
Implements data validation for the ingestion pipeline, including the
required T016 logic: if required variables are missing the script halts
with exit code 1 and logs the message
`DATA_BLOCKER: Missing required variables`.

The script performs three validation steps:
  1. Required column presence (T016)
  2. Data‑quality metrics (track loss ≤ 5 % and calibrated eye‑tracker)
  3. Valence‑label annotation validation

On successful validation a quality report is written to
`data/eye-tracking/quality_report.md`. All logging is performed via the
project‑wide logger obtained from ``utils.logger``.
"""

import sys
import argparse
import json
from pathlib import Path
from typing import Dict, Any

import pandas as pd

# Project utilities
from utils.logger import get_logger
from ingestion.load_data import load_data

log = get_logger(__name__)


# ----------------------------------------------------------------------
# Validation helpers
# ----------------------------------------------------------------------

REQUIRED_COLUMNS = {
    "fixation_duration",
    "saccade_amplitude",
    "gaze_distribution",
    "recall_accuracy",
    "valence_label",
}


def validate_columns(df: pd.DataFrame, logger: Any) -> bool:
    """
    Validate that the DataFrame contains all required columns.

    Returns
    -------
    bool
        True if all required columns are present, False otherwise.
    """
    missing = REQUIRED_COLUMNS.difference(df.columns)
    if missing:
        logger.error(
            "DATA_BLOCKER: Missing required variables (%s)",
            ", ".join(sorted(missing)),
        )
        # Immediate halt as required by T016
        sys.exit(1)
        return False
    logger.info("All required columns are present.")
    return True


def validate_data_quality_metrics(df: pd.DataFrame, logger: Any) -> bool:
    """
    Validate data quality metrics:
      * Track loss ≤ 5 %
      * Calibrated eye‑tracker status is True

    Returns
    -------
    bool
        True if metrics are within acceptable limits, False otherwise.
    """
    # Expect boolean 'calibrated' column and numeric 'track_loss' (fraction)
    if "track_loss" not in df.columns or "calibrated" not in df.columns:
        logger.error("DATA_BLOCKER: Quality metric columns missing.")
        sys.exit(1)

    # Track loss is expressed as a boolean in the sample (False = no loss);
    # we treat any True as loss. For numeric fractions we compare to 0.05.
    if df["track_loss"].dtype == bool:
        loss_fraction = df["track_loss"].mean()  # proportion of True (loss)
    else:
        loss_fraction = df["track_loss"].astype(float).mean()

    if loss_fraction > 0.05:
        logger.error(
            "DATA_BLOCKER: Track loss %.2f exceeds 5%% threshold.", loss_fraction
        )
        sys.exit(1)

    if not df["calibrated"].all():
        logger.error("DATA_BLOCKER: One or more participants are uncalibrated.")
        sys.exit(1)

    logger.info("Data quality metrics passed (track loss %.2f, calibrated).", loss_fraction)
    return True


def validate_valence_labels(df: pd.DataFrame, logger: Any) -> bool:
    """
    Validate that valence labels exist and follow a standardized scale.

    Returns
    -------
    bool
        True if validation passes, False otherwise.
    """
    if "valence_label" not in df.columns:
        logger.error("DATA_BLOCKER: Valence label column missing.")
        sys.exit(1)

    # Simple scale check: values must be one of Positive, Negative, Neutral
    allowed = {"Positive", "Negative", "Neutral"}
    invalid = set(df["valence_label"].unique()) - allowed
    if invalid:
        logger.error(
            "DATA_BLOCKER: Valence labels contain unexpected categories: %s",
            ", ".join(sorted(invalid)),
        )
        sys.exit(1)

    logger.info("Valence label validation passed.")
    return True


def write_quality_report(report_data: Dict[str, Any], logger: Any) -> None:
    """
    Write a markdown quality report to ``data/eye-tracking/quality_report.md``.
    The report contains a JSON‑encoded summary for easy downstream parsing.
    """
    report_path = Path("data/eye-tracking/quality_report.md")
    report_path.parent.mkdir(parents=True, exist_ok=True)

    with report_path.open("w", encoding="utf-8") as f:
        f.write("# Data Quality Report\n\n")
        f.write("```json\n")
        json.dump(report_data, f, indent=2)
        f.write("\n```\n")

    logger.info("Wrote quality report to %s", report_path)


# ----------------------------------------------------------------------
# Main entry point
# ----------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate eye‑tracking dataset for required variables and quality."
    )
    parser.add_argument(
        "--input",
        type=str,
        required=True,
        help="Path to the raw CSV/EDF file to validate.",
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    if not input_path.is_file():
        log.error("DATA_BLOCKER: Input file not found: %s", input_path)
        sys.exit(1)

    # Load the dataset (delegates to ingestion.load_data)
    df = load_data(str(input_path))
    if df is None or df.empty:
        log.error("DATA_BLOCKER: Loaded dataset is empty or could not be read.")
        sys.exit(1)

    # 1) Required columns (T016)
    validate_columns(df, log)

    # 2) Data‑quality metrics (T014)
    validate_data_quality_metrics(df, log)

    # 3) Valence label validation (T015)
    validate_valence_labels(df, log)

    # If we reach this point all checks passed – write the quality report.
    report_summary = {
        "required_columns": sorted(list(REQUIRED_COLUMNS)),
        "track_loss_fraction": (
            df["track_loss"].mean()
            if df["track_loss"].dtype != bool
            else df["track_loss"].astype(int).mean()
        ),
        "calibrated": bool(df["calibrated"].all()),
        "valence_categories": sorted(df["valence_label"].unique()),
    }
    write_quality_report(report_summary, log)

    log.info("Data validation completed successfully.")
    sys.exit(0)


if __name__ == "__main__":
    main()