"""
Final Validation Module (T035)

Validates the completion of the entire pipeline by checking the existence
and content integrity of all required artifacts.
"""
import os
import sys
import csv
import time
import logging
from pathlib import Path

from code.config import DATA_PROCESSED_DIR, LOGS_DIR

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(os.path.join(LOGS_DIR, 'final_validation.log'))
    ]
)
logger = logging.getLogger(__name__)

# Define required artifacts based on T035 specification
REQUIRED_FILES = [
    "energy_results_aggregated.csv",
    "stats_report.csv",
    "energy_bar.png",
    "tradeoff_scatter.png"
]

REQUIRED_LOGS = [
    "pipeline_duration.log"
]

def check_file_exists(filepath: Path) -> bool:
    """Check if a file exists and is not empty."""
    if not filepath.exists():
        logger.error(f"MISSING: {filepath}")
        return False
    if filepath.stat().st_size == 0:
        logger.error(f"EMPTY: {filepath}")
        return False
    logger.info(f"FOUND: {filepath} ({filepath.stat().st_size} bytes)")
    return True

def check_csv_content(filepath: Path, required_columns: list = None) -> bool:
    """
    Check if a CSV file exists and contains the required columns.
    If required_columns is None, just checks existence and non-empty.
    """
    if not check_file_exists(filepath):
        return False

    try:
        with open(filepath, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            if required_columns:
                if not required_columns:
                    # If required_columns is empty list, just check headers exist
                    headers = reader.fieldnames
                    if not headers:
                        logger.error(f"CSV {filepath} has no headers.")
                        return False
                    return True

                if reader.fieldnames is None:
                    logger.error(f"CSV {filepath} has no headers.")
                    return False

                missing_cols = set(required_columns) - set(reader.fieldnames)
                if missing_cols:
                    logger.error(f"CSV {filepath} missing columns: {missing_cols}")
                    return False

                # Check for at least one data row
                has_data = False
                for _ in reader:
                    has_data = True
                    break

                if not has_data:
                    logger.error(f"CSV {filepath} has no data rows.")
                    return False

            logger.info(f"CONTENT OK: {filepath}")
            return True
    except Exception as e:
        logger.error(f"Error reading CSV {filepath}: {e}")
        return False

def check_log_content(filepath: Path, required_keywords: list = None) -> bool:
    """
    Check if a log file exists and contains required keywords (if any).
    """
    if not check_file_exists(filepath):
        return False

    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            if not content.strip():
                logger.error(f"Log {filepath} is empty.")
                return False

            if required_keywords:
                for keyword in required_keywords:
                    if keyword not in content:
                        logger.error(f"Log {filepath} missing keyword: {keyword}")
                        return False

            logger.info(f"CONTENT OK: {filepath}")
            return True
    except Exception as e:
        logger.error(f"Error reading log {filepath}: {e}")
        return False

def main():
    """
    Main entry point for final validation.
    Returns 0 if all checks pass, 1 otherwise.
    """
    logger.info("Starting Final Validation (T035)...")
    all_passed = True

    # 1. Check Data Files
    logger.info("--- Checking Data Artifacts ---")
    
    # energy_results_aggregated.csv
    csv_path = Path(DATA_PROCESSED_DIR) / "energy_results_aggregated.csv"
    if not check_csv_content(csv_path, required_columns=['model_id', 'problem_id', 'tokens_generated', 'energy_kwh', 'runtime_seconds', 'pass_fail_status']):
        all_passed = False

    # stats_report.csv
    stats_path = Path(DATA_PROCESSED_DIR) / "stats_report.csv"
    if not check_csv_content(stats_path):
        all_passed = False

    # 2. Check Image Files
    logger.info("--- Checking Visualization Artifacts ---")
    
    # energy_bar.png
    bar_path = Path(DATA_PROCESSED_DIR) / "energy_bar.png"
    if not check_file_exists(bar_path):
        all_passed = False

    # tradeoff_scatter.png
    scatter_path = Path(DATA_PROCESSED_DIR) / "tradeoff_scatter.png"
    if not check_file_exists(scatter_path):
        all_passed = False

    # 3. Check Log Files
    logger.info("--- Checking Log Artifacts ---")
    
    # pipeline_duration.log
    duration_log_path = Path(LOGS_DIR) / "pipeline_duration.log"
    if not check_log_content(duration_log_path):
        all_passed = False

    # Final Result
    logger.info("--- Validation Summary ---")
    if all_passed:
        logger.info("SUCCESS: All required artifacts exist and are valid.")
        return 0
    else:
        logger.error("FAILURE: One or more required artifacts are missing or invalid.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
