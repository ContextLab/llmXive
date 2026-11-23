"""
Integration test for the full data pipeline (fetch -> analyze -> save).

This test verifies that the pipeline correctly fetches data, performs static analysis,
and saves the results to the expected output location with the required schema keys.
"""
import json
import os
import sys
import tempfile
import shutil
from pathlib import Path
import pytest

# Add the project root to the path to allow imports
# Assuming this test runs from the project root or the test directory
project_root = Path(__file__).parent.parent.parent
if str(project_root / 'code') not in sys.path:
    sys.path.insert(0, str(project_root / 'code'))

from data.download import download_valid_functions
from data.static_analysis import run_static_analysis_on_dataset
from data.processor import save_processed_data, validate_sample_count
from utils.logging import setup_logging, get_logger
from config import Config

logger = get_logger(__name__)

def test_full_pipeline_produces_json():
    """
    Asserts that the full pipeline (download -> analyze -> save) produces
    data/processed/raw_metrics.json containing the required keys.
    
    Required keys per spec: code, hash, loc, nesting_depth, param_count, 
    pep8_violations, pep8_adherence_score, docstring_present.
    """
    # Setup: Create a temporary directory to simulate the project data structure
    # if running in isolation, but we will target the real project paths as per task spec.
    # The task requires writing to data/processed/raw_metrics.json.
    
    output_dir = project_root / 'data' / 'processed'
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file_path = output_dir / 'raw_metrics.json'
    
    # Clean up previous run if exists to ensure fresh test
    if output_file_path.exists():
        output_file_path.unlink()
    
    # Configuration for the test (small sample to ensure speed)
    # We use the Config class to get defaults, but override sample size for testing
    config = Config()
    test_sample_size = 5  # Small number for integration test speed
    max_attempts = 10
    
    logger.info(f"Starting integration test with {test_sample_size} samples.")
    
    # Step 1: Download valid functions
    # We call the download function directly. It should fetch from the real source.
    # If the real source is unreachable, this should fail loudly as per constraints.
    logger.info("Step 1: Fetching valid functions from BigCode dataset...")
    try:
        valid_functions = download_valid_functions(
            target_count=test_sample_size,
            max_attempts=max_attempts,
            random_seed=config.RANDOM_SEED
        )
    except Exception as e:
        logger.error(f"Failed to download functions: {e}")
        # If download fails (e.g., network issue), the test fails.
        # This satisfies the "fail loudly" requirement for real data.
        raise AssertionError("Pipeline failed at download stage: Could not fetch real data.") from e

    assert len(valid_functions) > 0, "No valid functions were downloaded."
    logger.info(f"Downloaded {len(valid_functions)} valid functions.")

    # Step 2: Perform Static Analysis
    logger.info("Step 2: Running static analysis on downloaded functions...")
    try:
        analyzed_data = run_static_analysis_on_dataset(valid_functions)
    except Exception as e:
        logger.error(f"Failed to analyze functions: {e}")
        raise AssertionError("Pipeline failed at analysis stage.") from e
    
    assert len(analyzed_data) == len(valid_functions), "Analysis output count mismatch."
    logger.info(f"Analysis complete for {len(analyzed_data)} functions.")

    # Step 3: Save Processed Data
    logger.info("Step 3: Saving processed data to disk...")
    try:
        save_processed_data(analyzed_data, output_file_path)
    except Exception as e:
        logger.error(f"Failed to save data: {e}")
        raise AssertionError("Pipeline failed at save stage.") from e

    # Verification: Check file existence
    assert output_file_path.exists(), f"Output file {output_file_path} was not created."
    logger.info(f"Output file created: {output_file_path}")

    # Verification: Load and validate content
    with open(output_file_path, 'r', encoding='utf-8') as f:
        results = json.load(f)

    assert isinstance(results, list), "Output must be a list of records."
    assert len(results) > 0, "Output list is empty."

    # Define required keys per spec (T013 and T014 requirements)
    required_keys = {
        'code',
        'hash',
        'loc',
        'nesting_depth',
        'param_count',
        'pep8_violations',
        'pep8_adherence_score',
        'docstring_present'
    }

    # Check first record for required keys
    first_record = results[0]
    missing_keys = required_keys - set(first_record.keys())
    assert not missing_keys, f"Missing required keys in output: {missing_keys}. Found keys: {first_record.keys()}"

    # Verify data types for a few critical fields
    assert isinstance(first_record['code'], str), "code must be a string"
    assert isinstance(first_record['hash'], str), "hash must be a string"
    assert isinstance(first_record['loc'], (int, float)), "loc must be numeric"
    assert isinstance(first_record['nesting_depth'], (int, float)), "nesting_depth must be numeric"
    assert isinstance(first_record['param_count'], (int, float)), "param_count must be numeric"
    assert isinstance(first_record['pep8_violations'], (int, float)), "pep8_violations must be numeric"
    assert isinstance(first_record['pep8_adherence_score'], (int, float)), "pep8_adherence_score must be numeric"
    assert isinstance(first_record['docstring_present'], bool), "docstring_present must be boolean"

    logger.info("Integration test PASSED: Pipeline produced valid JSON with required keys.")
    
    # Optional: Clean up test file if desired, but keeping it for verification is often better
    # output_file_path.unlink()

if __name__ == '__main__':
    setup_logging()
    test_full_pipeline_produces_json()
    print("All integration tests passed.")