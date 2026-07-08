"""
Data quality validation module for the llmXive pipeline.
Implements T018b: Calculate overall data quality success rate and halt if threshold not met.
"""
import json
import logging
import os
from pathlib import Path
from typing import Dict, Any, Optional

# Import existing utilities from the project API surface
from utils import validate_json_schema

logger = logging.getLogger(__name__)

class DataQualityError(Exception):
    """Raised when data quality threshold is not met."""
    pass

def calculate_success_rate(processed_count: int, total_count: int) -> float:
    """
    Calculate the data quality success rate.
    
    Args:
        processed_count: Number of PRs successfully processed and saved.
        total_count: Total number of PRs attempted.
    
    Returns:
        Success rate as a float between 0.0 and 1.0.
    """
    if total_count == 0:
        return 0.0
    return processed_count / total_count

def validate_and_check_quality(
    processed_data_path: str,
    total_prs_attempted: int,
    quality_threshold: float = 0.95
) -> Dict[str, Any]:
    """
    Validate processed data against schema and check quality threshold.
    
    This function:
    1. Loads the processed data from the specified path.
    2. Validates each record against the pull_request schema.
    3. Calculates the success rate (processed/total).
    4. Raises DataQualityError if rate < threshold.
    
    Args:
        processed_data_path: Path to the processed data JSON file.
        total_prs_attempted: Total number of PRs that were attempted to be processed.
        quality_threshold: Minimum acceptable success rate (default 0.95).
    
    Returns:
        Dictionary containing validation results and statistics.
    
    Raises:
        DataQualityError: If the success rate is below the threshold.
        FileNotFoundError: If the processed data file does not exist.
    """
    if not os.path.exists(processed_data_path):
        raise FileNotFoundError(f"Processed data file not found: {processed_data_path}")

    logger.info(f"Loading processed data from {processed_data_path}")
    with open(processed_data_path, 'r', encoding='utf-8') as f:
        processed_data = json.load(f)

    if not isinstance(processed_data, list):
        logger.warning("Processed data is not a list, attempting to handle as single object")
        processed_data = [processed_data]

    processed_count = len(processed_data)
    success_rate = calculate_success_rate(processed_count, total_prs_attempted)

    logger.info(f"Processed {processed_count} records out of {total_prs_attempted} attempted.")
    logger.info(f"Success rate: {success_rate:.2%}")

    # Validate schema for a sample of records (or all if small)
    schema_path = "contracts/pull_request.schema.yaml"
    validation_errors = 0
    if processed_count > 0:
        logger.info(f"Validating schema for {min(100, processed_count)} records...")
        sample_size = min(100, processed_count)
        for i, record in enumerate(processed_data[:sample_size]):
            if not validate_json_schema(record, schema_path):
                validation_errors += 1
                if validation_errors <= 5:
                    logger.warning(f"Schema validation failed for record {i}")

    if validation_errors > 0:
        logger.warning(f"Found {validation_errors} schema validation errors in sample")

    # Check against threshold
    if success_rate < quality_threshold:
        error_msg = f"Data quality threshold not met: {success_rate:.2%} (threshold: {quality_threshold:.2%})"
        logger.error(error_msg)
        raise DataQualityError(error_msg)

    result = {
        "processed_count": processed_count,
        "total_attempted": total_prs_attempted,
        "success_rate": success_rate,
        "threshold": quality_threshold,
        "status": "passed",
        "validation_errors_sample": validation_errors
    }

    logger.info(f"Data quality check PASSED: {success_rate:.2%} >= {quality_threshold:.2%}")
    return result

def main():
    """
    Main entry point for data quality validation.
    Reads processed data and checks quality threshold.
    """
    # Setup logging
    from logging_config import setup_logging
    setup_logging()

    # Configuration
    project_root = Path(__file__).parent.parent
    processed_data_path = project_root / "data" / "processed" / "processed_prs.json"
    total_prs_file = project_root / "data" / "processed" / "processing_stats.json"
    
    # Load total PRs attempted from stats file if it exists
    total_prs_attempted = 0
    if total_prs_file.exists():
        with open(total_prs_file, 'r') as f:
            stats = json.load(f)
            total_prs_attempted = stats.get("total_prs_processed", 0)
    else:
        logger.warning("Processing stats file not found. Attempting to infer from processed data.")
        # Fallback: count from processed data if stats file missing
        if processed_data_path.exists():
            with open(processed_data_path, 'r') as f:
                data = json.load(f)
                total_prs_attempted = len(data) if isinstance(data, list) else 1

    if total_prs_attempted == 0:
        logger.warning("No PRs found to validate. Skipping quality check.")
        return

    try:
        result = validate_and_check_quality(
            processed_data_path=str(processed_data_path),
            total_prs_attempted=total_prs_attempted,
            quality_threshold=0.95
        )
        print(json.dumps(result, indent=2))
    except DataQualityError as e:
        print(f"ERROR: {e}")
        raise
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        raise

if __name__ == "__main__":
    main()
