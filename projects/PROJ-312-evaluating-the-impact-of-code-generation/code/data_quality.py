import json
import logging
import os
from pathlib import Path
from typing import Dict, Any, Optional

from utils import validate_json_schema

# Define the custom exception as required by the task
class DataQualityError(Exception):
    """Raised when data quality thresholds are not met."""
    pass

def calculate_success_rate(processed_count: int, total_count: int) -> float:
    """
    Calculate the overall data quality success rate.

    Args:
        processed_count: Number of PRs successfully processed.
        total_count: Total number of PRs attempted.

    Returns:
        Success rate as a float between 0.0 and 1.0.
    """
    if total_count == 0:
        return 0.0
    return processed_count / total_count

def validate_and_check_quality(processed_data_path: str, raw_data_path: str, threshold: float = 0.95) -> bool:
    """
    Load processed and raw data, calculate success rate, and enforce quality threshold.

    This function implements SC-003: If the success rate is below the threshold,
    it raises DataQualityError. Otherwise, it logs success.

    Args:
        processed_data_path: Path to the processed JSON/CSV file.
        raw_data_path: Path to the raw JSON/CSV file (source of truth for total count).
        threshold: Minimum acceptable success rate (default 0.95).

    Returns:
        True if quality threshold is met.

    Raises:
        DataQualityError: If the success rate is below the threshold.
    """
    logger = logging.getLogger(__name__)

    # Load raw data to determine total count
    try:
        with open(raw_data_path, 'r', encoding='utf-8') as f:
            raw_data = json.load(f)
        total_prs = len(raw_data)
    except FileNotFoundError:
        raise FileNotFoundError(f"Raw data file not found at {raw_data_path}")
    except json.JSONDecodeError:
        raise ValueError(f"Invalid JSON in raw data file: {raw_data_path}")

    if total_prs == 0:
        logger.warning("Raw data is empty. Cannot calculate success rate.")
        raise DataQualityError("Data quality threshold not met: 0% (No raw data found)")

    # Load processed data to determine successful count
    try:
        with open(processed_data_path, 'r', encoding='utf-8') as f:
            processed_data = json.load(f)
        processed_prs = len(processed_data)
    except FileNotFoundError:
        raise FileNotFoundError(f"Processed data file not found at {processed_data_path}")
    except json.JSONDecodeError:
        raise ValueError(f"Invalid JSON in processed data file: {processed_data_path}")

    success_rate = calculate_success_rate(processed_prs, total_prs)
    success_rate_percent = success_rate * 100

    logger.info(f"Data Quality Check: Processed {processed_prs} of {total_prs} PRs.")
    logger.info(f"Success Rate: {success_rate_percent:.2f}%")

    if success_rate < threshold:
        error_msg = f"Data quality threshold not met: {success_rate_percent:.2f}%"
        logger.error(error_msg)
        raise DataQualityError(error_msg)

    logger.info(f"Data quality threshold met: {success_rate_percent:.2f}% >= {threshold * 100:.2f}%")
    return True

def main():
    """
    Main entry point for T018b: Data Quality Check.
    Reads from data/raw/ and data/processed/, validates quality, and halts if necessary.
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)

    # Define paths relative to project root
    # Assuming this script runs from the project root or code/ directory
    project_root = Path(__file__).resolve().parent.parent
    raw_data_path = project_root / "data" / "raw" / "processed_prs.json"
    processed_data_path = project_root / "data" / "processed" / "final_dataset.json"

    # Fallback to relative paths if running from code/ directly
    if not raw_data_path.exists():
        raw_data_path = Path("data/raw/processed_prs.json")
    if not processed_data_path.exists():
        processed_data_path = Path("data/processed/final_dataset.json")

    logger.info(f"Checking data quality. Raw: {raw_data_path}, Processed: {processed_data_path}")

    try:
        validate_and_check_quality(
            processed_data_path=str(processed_data_path),
            raw_data_path=str(raw_data_path),
            threshold=0.95
        )
        logger.info("Pipeline data quality check passed. Proceeding.")
    except DataQualityError as e:
        logger.critical(str(e))
        # Halt the pipeline as required
        raise SystemExit(1)
    except Exception as e:
        logger.error(f"Unexpected error during quality check: {e}")
        raise SystemExit(1)

if __name__ == "__main__":
    main()