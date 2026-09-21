import json
import logging
import os
from pathlib import Path
from typing import Dict, Any, Optional

from utils import validate_json_schema

# Define the custom exception as required by the task and used in analyze.py
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

def validate_and_check_quality(
    processed_data_path: str,
    raw_data_path: str,
    schema_path: str,
    threshold: float = 0.95
) -> bool:
    """
    Validate data quality by comparing processed vs raw counts and checking schema.

    Args:
        processed_data_path: Path to the processed CSV/JSON file.
        raw_data_path: Path to the raw JSON file containing all fetched PRs.
        schema_path: Path to the JSON schema for validation.
        threshold: Minimum acceptable success rate (default 0.95).

    Raises:
        DataQualityError: If the success rate is below the threshold.
    """
    logger = logging.getLogger(__name__)

    # Load raw data to get total count
    if not os.path.exists(raw_data_path):
        logger.error(f"Raw data file not found: {raw_data_path}")
        raise FileNotFoundError(f"Raw data file not found: {raw_data_path}")

    with open(raw_data_path, 'r', encoding='utf-8') as f:
        raw_data = json.load(f)
    
    total_prs = len(raw_data)
    logger.info(f"Total PRs in raw data: {total_prs}")

    # Load processed data to get successful count
    if not os.path.exists(processed_data_path):
        # If processed file doesn't exist, success rate is 0
        success_rate = 0.0
        processed_prs = 0
    else:
        # For CSV, we count rows; for JSON, we count list items
        if processed_data_path.endswith('.csv'):
            import csv
            with open(processed_data_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                processed_prs = sum(1 for _ in reader)
        else:
            with open(processed_data_path, 'r', encoding='utf-8') as f:
                processed_data = json.load(f)
                if isinstance(processed_data, list):
                    processed_prs = len(processed_data)
                else:
                    processed_prs = 0
        
        success_rate = calculate_success_rate(processed_prs, total_prs)
        logger.info(f"Processed PRs: {processed_prs}, Success Rate: {success_rate:.2%}")

    # Validate schema for processed data if it exists
    if processed_prs > 0:
        if processed_data_path.endswith('.json'):
            with open(processed_data_path, 'r', encoding='utf-8') as f:
                processed_data = json.load(f)
            if isinstance(processed_data, list) and len(processed_data) > 0:
                if not validate_json_schema(processed_data[0], schema_path):
                    logger.warning("Schema validation failed for processed data sample.")
                    # We continue but log the warning

    # Check threshold
    if success_rate < threshold:
        error_msg = f"Data quality threshold not met: {success_rate:.1%}"
        logger.error(error_msg)
        raise DataQualityError(error_msg)
    
    logger.info(f"Data quality check passed. Success rate: {success_rate:.2%} >= {threshold:.2%}")
    return True

def main():
    """Main entry point for data quality validation."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)

    project_root = Path(__file__).parent.parent
    raw_data_path = project_root / 'data' / 'raw' / 'pr_data.json'
    processed_data_path = project_root / 'data' / 'processed' / 'pr_turnaround.csv'
    schema_path = project_root / 'contracts' / 'pull_request.schema.yaml'

    try:
        validate_and_check_quality(
            processed_data_path=str(processed_data_path),
            raw_data_path=str(raw_data_path),
            schema_path=str(schema_path),
            threshold=0.95
        )
        logger.info("Data quality validation completed successfully.")
    except DataQualityError as e:
        logger.critical(f"Pipeline halted: {e}")
        raise
    except FileNotFoundError as e:
        logger.critical(f"Pipeline halted due to missing file: {e}")
        raise
    except Exception as e:
        logger.critical(f"Unexpected error during data quality check: {e}")
        raise

if __name__ == '__main__':
    main()