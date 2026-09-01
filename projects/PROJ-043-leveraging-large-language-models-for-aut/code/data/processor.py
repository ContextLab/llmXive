"""
Processor module for User Story 1.
Orchestrates the download of Python functions and the computation of static metrics.
"""

import json
import logging
import sys
from pathlib import Path
from typing import List, Dict, Any

# Project imports based on provided API surface
from data.download import download_valid_functions
from data.static_analysis import run_static_analysis_on_dataset
from utils.logging import get_logger, DataFetchError
from models.entities import FunctionSample

logger = get_logger(__name__)

# Configuration constants
MIN_VALID_SAMPLES = 100
OUTPUT_FILE_PATH = "data/processed/raw_metrics.json"


def ensure_output_directory() -> Path:
    """Ensures the output directory exists."""
    output_path = Path(OUTPUT_FILE_PATH)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    return output_path


def validate_sample_count(samples: List[Dict[str, Any]], min_count: int) -> None:
    """
    Validates that the number of processed samples meets the minimum requirement.
    Raises a ValueError if the count is insufficient.
    """
    count = len(samples)
    if count < min_count:
        error_msg = (
            f"Validation Failed: Only {count} valid samples found. "
            f"Minimum required: {min_count}. "
            "Halting pipeline to prevent processing insufficient data."
        )
        logger.error(error_msg)
        raise ValueError(error_msg)
    logger.info(f"Validation passed: {count} valid samples meet the minimum requirement of {min_count}.")


def save_processed_data(samples: List[Dict[str, Any]], output_path: Path) -> None:
    """
    Saves the processed samples to the specified JSON file.
    """
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(samples, f, indent=2, ensure_ascii=False)
    logger.info(f"Successfully saved {len(samples)} samples to {output_path}")


def process_pipeline() -> List[Dict[str, Any]]:
    """
    Main orchestration function for User Story 1.
    1. Downloads valid Python functions.
    2. Runs static analysis (metrics calculation).
    3. Filters out unparseable functions (handled internally by download/analysis).
    4. Validates the count >= 100.
    5. Saves to data/processed/raw_metrics.json.
    """
    logger.info("Starting User Story 1 pipeline: Download and Static Analysis.")

    # Step 1: Download valid functions
    # download_valid_functions handles fetching, validation, and retry logic.
    # It returns a list of FunctionSample-like dicts or objects.
    try:
        logger.info("Fetching valid Python functions from BigCode dataset...")
        raw_samples = download_valid_functions()
        
        if not raw_samples:
            logger.warning("No valid samples downloaded. Pipeline cannot proceed.")
            return []
        
        logger.info(f"Downloaded {len(raw_samples)} raw valid samples.")

    except DataFetchError as e:
        logger.critical(f"Critical data fetch error: {e}")
        raise
    except Exception as e:
        logger.critical(f"Unexpected error during download: {e}")
        raise

    # Step 2: Run Static Analysis
    # This computes LOC, nesting, complexity, pylint scores, etc.
    # It also filters out any remaining unparseable functions if the download didn't catch them.
    logger.info("Running static analysis on downloaded samples...")
    try:
        analyzed_samples = run_static_analysis_on_dataset(raw_samples)
    except Exception as e:
        logger.critical(f"Static analysis failed: {e}")
        raise

    if not analyzed_samples:
        logger.warning("Static analysis resulted in zero valid samples.")
        return []

    logger.info(f"Analysis complete. {len(analyzed_samples)} samples with metrics.")

    # Step 3: Validate count
    logger.info(f"Validating sample count against threshold ({MIN_VALID_SAMPLES})...")
    validate_sample_count(analyzed_samples, MIN_VALID_SAMPLES)

    # Step 4: Save output
    output_path = ensure_output_directory()
    save_processed_data(analyzed_samples, output_path)

    logger.info("User Story 1 pipeline completed successfully.")
    return analyzed_samples


def main():
    """Entry point for the processor script."""
    try:
        process_pipeline()
    except ValueError as e:
        # Specific validation failure
        print(f"Pipeline failed validation: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        # General failure
        print(f"Pipeline failed with error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()