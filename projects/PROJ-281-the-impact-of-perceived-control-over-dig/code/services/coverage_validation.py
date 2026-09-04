"""
Coverage Validation Service for User Story 1.

Implements logic to verify >=95% scoring coverage by comparing
row counts of preprocessed_text.csv and scoring_results.csv.
Generates data/processed/coverage_report.json.
"""
import json
import logging
from pathlib import Path
from typing import Dict, Any

import pandas as pd

from code.config import CONFIG

logger = logging.getLogger(__name__)


def validate_coverage(preprocessed_path: Path, scoring_path: Path) -> Dict[str, Any]:
    """
    Compare row counts of preprocessed and scored data to verify coverage.

    Args:
        preprocessed_path: Path to data/processed/preprocessed_text.csv
        scoring_path: Path to data/processed/scoring_results.csv

    Returns:
        Dictionary containing coverage statistics and validation status.
    """
    if not preprocessed_path.exists():
        raise FileNotFoundError(f"Preprocessed file not found: {preprocessed_path}")
    if not scoring_path.exists():
        raise FileNotFoundError(f"Scoring results file not found: {scoring_path}")

    df_preprocessed = pd.read_csv(preprocessed_path)
    df_scoring = pd.read_csv(scoring_path)

    total_input_rows = len(df_preprocessed)
    scored_rows = len(df_scoring)

    if total_input_rows == 0:
        coverage_pct = 0.0
        is_valid = False
        reason = "Input dataset is empty"
    else:
        coverage_pct = (scored_rows / total_input_rows) * 100
        is_valid = coverage_pct >= 95.0
        reason = "Coverage threshold met" if is_valid else "Coverage threshold not met"

    report = {
        "total_input_rows": total_input_rows,
        "scored_rows": scored_rows,
        "coverage_percentage": round(coverage_pct, 2),
        "threshold_met": is_valid,
        "threshold_percentage": 95.0,
        "status": "PASS" if is_valid else "FAIL",
        "reason": reason,
        "preprocessed_file": str(preprocessed_path),
        "scoring_file": str(scoring_path)
    }

    logger.info(
        "Coverage validation: %d/%d rows (%.2f%%) - %s",
        scored_rows, total_input_rows, coverage_pct, report["status"]
    )

    return report


def run_coverage_validation() -> Dict[str, Any]:
    """
    Main entry point to run coverage validation pipeline.

    Reads preprocessed text and scoring results, validates coverage,
    and saves the report to data/processed/coverage_report.json.

    Returns:
        The generated coverage report dictionary.
    """
    preprocessed_path = CONFIG.DATA_PROCESSED_DIR / "preprocessed_text.csv"
    scoring_path = CONFIG.DATA_PROCESSED_DIR / "scoring_results.csv"
    output_path = CONFIG.DATA_PROCESSED_DIR / "coverage_report.json"

    logger.info("Starting coverage validation...")
    logger.info("Input: %s", preprocessed_path)
    logger.info("Input: %s", scoring_path)

    report = validate_coverage(preprocessed_path, scoring_path)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    logger.info("Coverage report saved to: %s", output_path)

    return report
