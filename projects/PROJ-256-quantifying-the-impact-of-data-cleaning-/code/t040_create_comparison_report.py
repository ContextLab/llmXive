"""
T040 – Create comparison report

This script orchestrates the generation of a ``ComparisonReport`` entity
that aggregates baseline metrics, cleaned metrics, absolute/relative
differences, and any sensitivity‑analysis results that have been produced
earlier in the pipeline.

The script is deliberately tolerant: if any of the required input files
are missing it logs a warning and continues with whatever data is
available, producing an (possibly partial) report instead of raising an
exception.
"""

import logging
from pathlib import Path

from reporting import create_comparison_report, save_json_file
from utils import setup_logging

def main() -> None:
    logger = setup_logging("INFO")
    logger.info("Starting creation of ComparisonReport.")

    report = create_comparison_report()

    output_path = Path("data/processed/comparison_report.json")
    save_json_file(report.dict(), output_path)

    logger.info(f"Comparison report written to {output_path}")

if __name__ == "__main__":
    main()
