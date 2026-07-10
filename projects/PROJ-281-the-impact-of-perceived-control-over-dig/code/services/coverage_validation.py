"""
Coverage validation logic for User Story 1.

Verifies that >=95% of rows from the preprocessed text file
(data/processed/preprocessed_text.csv) have corresponding entries
in the scoring results file (data/processed/scoring_results.csv).
Generates a coverage report at data/processed/coverage_report.json.
"""
import json
import logging
from pathlib import Path
from typing import Dict, Any

import pandas as pd

from code.config import CONFIG

logger = logging.getLogger(__name__)

def validate_coverage() -> Dict[str, Any]:
    """
    Compare row counts of preprocessed_text.csv and scoring_results.csv.
    Returns a dictionary with coverage metrics.

    Raises:
        FileNotFoundError: If required input files are missing.
        ValueError: If coverage is below the 95% threshold.
    """
    preprocessed_path = CONFIG.DATA_PROCESSED_DIR / "preprocessed_text.csv"
    scoring_path = CONFIG.DATA_PROCESSED_DIR / "scoring_results.csv"
    report_path = CONFIG.DATA_PROCESSED_DIR / "coverage_report.json"

    if not preprocessed_path.exists():
        raise FileNotFoundError(f"Preprocessed text file not found: {preprocessed_path}")
    if not scoring_path.exists():
        raise FileNotFoundError(f"Scoring results file not found: {scoring_path}")

    df_preprocessed = pd.read_csv(preprocessed_path)
    df_scoring = pd.read_csv(scoring_path)

    total_preprocessed = len(df_preprocessed)
    total_scoring = len(df_scoring)

    if total_preprocessed == 0:
        coverage_pct = 0.0
        is_success = False
        message = "No rows in preprocessed text file."
    else:
        # Calculate coverage based on the assumption that scoring results
        # are a subset of preprocessed text (filtered by quality/confidence).
        # The task requires verifying that >=95% of preprocessed rows are scored.
        # This implies that the filtering steps (T014a, T016) should not remove
        # more than 5% of the data.
        coverage_pct = (total_scoring / total_preprocessed) * 100
        is_success = coverage_pct >= 95.0
        message = "Coverage threshold met." if is_success else "Coverage threshold NOT met."

        logger.info(f"Preprocessed rows: {total_preprocessed}")
        logger.info(f"Scoring rows: {total_scoring}")
        logger.info(f"Coverage: {coverage_pct:.2f}%")

    report = {
        "preprocessed_count": total_preprocessed,
        "scoring_count": total_scoring,
        "coverage_percentage": round(coverage_pct, 4),
        "threshold_percentage": 95.0,
        "is_success": is_success,
        "message": message,
        "timestamp": CONFIG.RUN_TIMESTAMP.isoformat()
    }

    # Ensure directory exists
    report_path.parent.mkdir(parents=True, exist_ok=True)

    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    logger.info(f"Coverage report saved to {report_path}")

    if not is_success:
        raise ValueError(f"Coverage validation failed: {coverage_pct:.2f}% < 95.0%")

    return report

def run_coverage_validation() -> None:
    """
    Entry point for the coverage validation script.
    """
    logging.basicConfig(level=logging.INFO)
    try:
        validate_coverage()
        logger.info("Coverage validation completed successfully.")
    except FileNotFoundError as e:
        logger.error(f"File missing: {e}")
        raise
    except ValueError as e:
        logger.error(f"Validation failed: {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error during coverage validation: {e}")
        raise

if __name__ == "__main__":
    run_coverage_validation()
