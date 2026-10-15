"""
T003 Implementation: Compute retention rate, flag anomalies,
create zero‑inflation and analysis subsets, and write summary metadata.
This script is intended to be run after the preprocessing step that
produces `data/processed/cleaned_delays.csv`.
"""
import json
import logging
import pandas as pd

from llmxive_toolkit import paths, get_logger
from utils import PipelineError

# Initialize logger
log = get_logger(__name__)

def main():
    """
    Main entry point for the T003 summary and subset generation.
    """
    # Load the cleaned delays CSV
    cleaned_path = paths.data("processed", "cleaned_delays.csv")
    log.info(f"Loading cleaned data from {cleaned_path}")
    try:
        df = pd.read_csv(cleaned_path)
    except FileNotFoundError as e:
        log.error(f"Cleaned delays file not found: {e}")
        raise

    # Verify required columns exist
    required_columns = {"total_delay", "is_data_error"}
    missing = required_columns - set(df.columns)
    if missing:
        raise PipelineError(f"Missing expected columns in cleaned data: {missing}")

    # Compute basic statistics
    total_records = len(df)
    data_error_count = int(df["is_data_error"].sum())
    valid_records = total_records - data_error_count
    retention_rate = valid_records / total_records if total_records > 0 else 0.0

    log.info(f"Total records: {total_records}")
    log.info(f"Data‑error records: {data_error_count}")
    log.info(f"Valid records: {valid_records}")
    log.info(f"Retention rate: {retention_rate:.4%}")

    # Enforce retention threshold
    if retention_rate < 0.95:
        raise PipelineError(
            f"Retention rate below 95 % (got {retention_rate:.2%})"
        )

    # Write summary JSON
    summary = {
        "total_records": total_records,
        "valid_records": valid_records,
        "retention_rate": retention_rate,
    }
    summary_path = paths.results("summary.json")
    summary_path.parent.mkdir(parents=True, exist_ok=True)
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2)
    log.info(f"Summary written to {summary_path}")

    # Zero‑inflation subset (remove rows where total_delay == 0)
    df_no_zero = df[df["total_delay"] != 0].copy()
    zero_path = paths.data("processed", "cleaned_delays_no_zero.csv")
    df_no_zero.to_csv(zero_path, index=False)
    log.info(f"Zero‑inflation subset written to {zero_path} ({len(df_no_zero)} rows)")

    # Analysis set (exclude rows flagged as data errors)
    df_analysis = df[~df["is_data_error"]].copy()
    analysis_path = paths.data("processed", "analysis_set.csv")
    df_analysis.to_csv(analysis_path, index=False)
    log.info(f"Analysis set written to {analysis_path} ({len(df_analysis)} rows)")

if __name__ == "__main__":
    main()
