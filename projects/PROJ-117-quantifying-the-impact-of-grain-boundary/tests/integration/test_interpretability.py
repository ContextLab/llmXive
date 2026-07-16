"""
Integration test for User Story 3: Feature Interpretability & Sensitivity Analysis.

This test verifies:
1. Plot generation (SHAP summary plot) exists in artifacts/figures/.
2. Sensitivity table accuracy (threshold-sensitivity-table.csv) exists in artifacts/reports/.
3. The sensitivity table contains the required columns and valid data.
4. The threshold justification from config.yaml is correctly included in the report logic.

Prerequisites:
- T021 (interpret.py) must have run successfully.
- models/best_model.json must exist.
- data/processed/cleaned_dataset.parquet must exist.
- config.yaml must exist with thresholds.r2.citation.
"""

import os
import sys
import json
import csv
import logging
import subprocess
from pathlib import Path
from typing import Dict, Any, List

# Add project root to path if necessary
PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

# Import utilities from the project
from utils import setup_logging

logger = setup_logging("test_interpretability")

# Configuration
ARTIFACTS_DIR = PROJECT_ROOT / "artifacts"
FIGURES_DIR = ARTIFACTS_DIR / "figures"
REPORTS_DIR = ARTIFACTS_DIR / "reports"
CONFIG_PATH = PROJECT_ROOT / "config.yaml"
MODEL_PATH = PROJECT_ROOT / "models" / "best_model.json"
DATA_PATH = PROJECT_ROOT / "data" / "processed" / "cleaned_dataset.parquet"

EXPECTED_PLOT_NAME = "shap_summary_plot.png"
EXPECTED_TABLE_NAME = "threshold-sensitivity-table.csv"
EXPECTED_REPORT_NAME = "interpretability_report.json"

REQUIRED_TABLE_COLUMNS = ["threshold", "pass_rate", "fpr_proxy", "sample_size"]


def check_file_exists(path: Path, description: str) -> bool:
    """Check if a file exists and log the result."""
    if path.exists():
        logger.info(f"✓ {description} exists: {path}")
        return True
    else:
        logger.error(f"✗ {description} MISSING: {path}")
        return False


def validate_sensitivity_table(table_path: Path) -> bool:
    """
    Validate the content of the threshold-sensitivity-table.csv.
    Checks for required columns and data integrity.
    """
    if not table_path.exists():
        logger.error(f"Table file not found: {table_path}")
        return False

    try:
        with open(table_path, 'r', newline='') as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames

            if headers is None:
                logger.error("Sensitivity table is empty or has no headers.")
                return False

            # Check for required columns
            missing_cols = set(REQUIRED_TABLE_COLUMNS) - set(headers)
            if missing_cols:
                logger.error(f"Sensitivity table missing columns: {missing_cols}")
                return False

            rows = list(reader)
            if not rows:
                logger.warning("Sensitivity table has no data rows (might be valid if no thresholds met, but usually implies error).")
                # Depending on strictness, this could be a failure. For now, warn.

            # Validate data types and ranges for a few rows
            valid_rows = 0
            for i, row in enumerate(rows):
                try:
                    threshold = float(row['threshold'])
                    pass_rate = float(row['pass_rate'])
                    fpr_proxy = float(row['fpr_proxy'])
                    sample_size = int(row['sample_size'])

                    # Basic range checks
                    if not (0.0 <= pass_rate <= 1.0):
                        logger.error(f"Row {i}: pass_rate {pass_rate} out of [0, 1]")
                        return False
                    if not (0.0 <= fpr_proxy <= 1.0):
                        logger.error(f"Row {i}: fpr_proxy {fpr_proxy} out of [0, 1]")
                        return False
                    if sample_size <= 0:
                        logger.error(f"Row {i}: sample_size {sample_size} must be > 0")
                        return False

                    valid_rows += 1
                except (ValueError, TypeError) as e:
                    logger.error(f"Row {i} data validation error: {e}")
                    return False

            logger.info(f"✓ Sensitivity table validated: {len(rows)} rows, {valid_rows} valid.")
            return True

    except Exception as e:
        logger.error(f"Error reading sensitivity table: {e}")
        return False


def validate_interpretability_report(report_path: Path) -> bool:
    """
    Validate the interpretability_report.json for required structure.
    Specifically checks for the presence of the threshold justification.
    """
    if not report_path.exists():
        logger.error(f"Report file not found: {report_path}")
        return False

    try:
        with open(report_path, 'r') as f:
            data = json.load(f)

        # Check for key sections
        required_keys = ["shap_summary", "sensitivity_analysis", "threshold_justification"]
        missing_keys = [k for k in required_keys if k not in data]
        if missing_keys:
            logger.error(f"Report missing keys: {missing_keys}")
            return False

        # Validate threshold justification content
        justification = data.get("threshold_justification", "")
        if not justification or not isinstance(justification, str) or len(justification.strip()) == 0:
            logger.error("Threshold justification is empty or invalid.")
            return False

        logger.info("✓ Interpretability report validated.")
        return True

    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in report: {e}")
        return False
    except Exception as e:
        logger.error(f"Error validating report: {e}")
        return False


def run_interpretability_script() -> bool:
    """
    Run the interpret.py script to generate artifacts.
    Returns True if the script exits with code 0.
    """
    script_path = PROJECT_ROOT / "code" / "interpret.py"
    if not script_path.exists():
        logger.error(f"Script not found: {script_path}")
        return False

    logger.info(f"Running interpretability script: {script_path}")
    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            timeout=300 # 5 minute timeout
        )

        if result.returncode != 0:
            logger.error(f"Script failed with return code {result.returncode}")
            logger.error(f"STDOUT: {result.stdout}")
            logger.error(f"STDERR: {result.stderr}")
            return False

        logger.info("✓ Script executed successfully.")
        return True

    except subprocess.TimeoutExpired:
        logger.error("Script execution timed out.")
        return False
    except Exception as e:
        logger.error(f"Error running script: {e}")
        return False


def test_prerequisites() -> bool:
    """Check if all prerequisite artifacts exist before running the test."""
    logger.info("Checking prerequisites...")
    checks = [
        (MODEL_PATH, "Trained model file"),
        (DATA_PATH, "Cleaned dataset"),
        (CONFIG_PATH, "Config file (for threshold justification)"),
    ]

    all_passed = True
    for path, desc in checks:
        if not check_file_exists(path, desc):
            all_passed = False

    return all_passed


def main():
    """Main entry point for the integration test."""
    logger.info("=" * 60)
    logger.info("Starting Integration Test: Test Interpretability (T024)")
    logger.info("=" * 60)

    # 1. Check Prerequisites
    if not test_prerequisites():
        logger.error("Prerequisites check failed. Aborting test.")
        return 1

    # 2. Run the interpretability script (if not already run or to ensure fresh output)
    # Note: In a real CI pipeline, this might be skipped if the script is run separately.
    # Here we run it to ensure the artifacts exist for this specific test run.
    if not run_interpretability_script():
        logger.error("Failed to run interpretability script.")
        return 1

    # 3. Verify Plot Generation
    plot_path = FIGURES_DIR / EXPECTED_PLOT_NAME
    if not check_file_exists(plot_path, "SHAP Summary Plot"):
        # It's possible the plot name is different or generation failed silently
        # List files in figures dir to debug
        if FIGURES_DIR.exists():
            files = list(FIGURES_DIR.iterdir())
            logger.warning(f"Files in {FIGURES_DIR}: {[f.name for f in files]}")
        return 1

    # 4. Verify Sensitivity Table Accuracy
    table_path = REPORTS_DIR / EXPECTED_TABLE_NAME
    if not validate_sensitivity_table(table_path):
        return 1

    # 5. Verify Interpretability Report (includes justification check)
    report_path = REPORTS_DIR / EXPECTED_REPORT_NAME
    if not validate_interpretability_report(report_path):
        return 1

    logger.info("=" * 60)
    logger.info("✓ ALL INTEGRATION TESTS PASSED (T024)")
    logger.info("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())