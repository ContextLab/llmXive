import os
import sys
import csv
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional

from code.utils.logging import get_logger
from code.utils.config import get_data_path, get_output_path

logger = get_logger(__name__)

def verify_csv_artifact(path: Path, required_columns: List[str]) -> Dict[str, Any]:
    """
    Verify that a CSV artifact exists, is non-empty, and contains the required columns.
    Returns a validation report dictionary.
    """
    report = {
        "path": str(path),
        "exists": False,
        "is_empty": True,
        "columns_match": False,
        "row_count": 0,
        "missing_columns": [],
        "valid": False
    }

    if not path.exists():
        logger.error(f"CSV artifact not found: {path}")
        return report

    report["exists"] = True

    try:
        with open(path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames

            if not headers:
                logger.error(f"CSV file is empty or has no headers: {path}")
                return report

            report["is_empty"] = False
            report["row_count"] = sum(1 for _ in reader)

            if report["row_count"] == 0:
                logger.warning(f"CSV file has headers but no data rows: {path}")
                return report

            missing = [col for col in required_columns if col not in headers]
            if missing:
                report["missing_columns"] = missing
                logger.error(f"Missing required columns in {path}: {missing}")
            else:
                report["columns_match"] = True

            report["valid"] = len(missing) == 0

    except Exception as e:
        logger.error(f"Error reading CSV {path}: {e}")
        return report

    return report

def verify_log_artifact(path: Path, min_lines: int = 0) -> Dict[str, Any]:
    """
    Verify that a log artifact exists and has at least min_lines lines.
    Returns a validation report dictionary.
    """
    report = {
        "path": str(path),
        "exists": False,
        "line_count": 0,
        "min_lines_met": False,
        "valid": False
    }

    if not path.exists():
        logger.error(f"Log artifact not found: {path}")
        return report

    report["exists"] = True

    try:
        with open(path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            report["line_count"] = len(lines)

            if report["line_count"] >= min_lines:
                report["min_lines_met"] = True
                report["valid"] = True
            else:
                logger.warning(
                    f"Log file {path} has {report['line_count']} lines "
                    f"(min required: {min_lines})"
                )

    except Exception as e:
        logger.error(f"Error reading log {path}: {e}")
        return report

    return report

def main():
    """
    Main entry point for T019: Verify and archive output.
    Checks that T014-T018 generated the required artifacts.
    """
    data_root = get_data_path()
    processed_dir = data_root / "processed"
    raw_dir = data_root / "raw"

    # Define expected artifacts
    csv_path = processed_dir / "cleaned_studies.csv"
    log_path = raw_dir / "excluded_studies.log"

    # Expected columns for cleaned_studies.csv based on the data model
    # (Study, EffectSize, MetaAnalysisResult fields relevant to the CSV)
    required_csv_columns = [
        "study_id", "title", "year", "source", "n_total", "n_experimental",
        "n_control", "mean_exp", "sd_exp", "mean_ctrl", "sd_ctrl",
        "age_mean", "age_sd", "mindfulness_component", "delivery_format",
        "social_skill_domain", "follow_up_months", "effect_size_hedges_g",
        "se_hedges_g", "included"
    ]

    logger.info("Starting T019 verification of pipeline outputs...")
    logger.info(f"Checking CSV: {csv_path}")
    logger.info(f"Checking Log: {log_path}")

    csv_report = verify_csv_artifact(csv_path, required_csv_columns)
    log_report = verify_log_artifact(log_path, min_lines=0)

    all_valid = csv_report["valid"] and log_report["valid"]

    logger.info("-" * 60)
    logger.info("VERIFICATION RESULTS")
    logger.info("-" * 60)
    logger.info(f"CSV Artifact ({csv_path}):")
    logger.info(f"  Exists: {csv_report['exists']}")
    logger.info(f"  Rows: {csv_report['row_count']}")
    logger.info(f"  Columns Match: {csv_report['columns_match']}")
    if csv_report['missing_columns']:
        logger.info(f"  Missing: {csv_report['missing_columns']}")
    logger.info(f"  Valid: {csv_report['valid']}")

    logger.info(f"Log Artifact ({log_path}):")
    logger.info(f"  Exists: {log_report['exists']}")
    logger.info(f"  Lines: {log_report['line_count']}")
    logger.info(f"  Valid: {log_report['valid']}")

    logger.info("-" * 60)
    if all_valid:
        logger.info("T019 VERIFICATION PASSED: All required artifacts are present and valid.")
        print("SUCCESS: T019 verification passed.")
    else:
        logger.error("T019 VERIFICATION FAILED: Missing or invalid artifacts detected.")
        print("FAILURE: T019 verification failed. Check logs above.")
        sys.exit(1)

    return all_valid

if __name__ == "__main__":
    main()
